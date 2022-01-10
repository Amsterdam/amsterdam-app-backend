import json
import uuid
from django.test import Client
from django.test import TestCase
from unittest.mock import patch
from amsterdam_app_api.UNITTESTS.mock_data import TestData
from amsterdam_app_api.UNITTESTS.mock_functions import firebase_admin_messaging_send_multicast
from amsterdam_app_api.GenericFunctions.AESCipher import AESCipher
from amsterdam_app_api.models import Projects, ProjectManager, WarningMessages, MobileDevices
from amsterdam_app_api.api_messages import Messages

messages = Messages()


class TestApiNotification(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestApiNotification, self).__init__(*args, **kwargs)
        self.data = TestData()
        self.url = '/api/v1/notification'
        self.token = AESCipher('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '6886b31dfe27e9306c3d2b553345d9e5').encrypt()
        self.headers = {"UserAuthorization": self.token}
        self.content_type = "application/json"
        self.client = Client()
        self.warning_identifier = None

    def setUp(self):
        for project in self.data.projects:
            Projects.objects.create(**project)

        ProjectManager.objects.all().delete()
        for project_manager in self.data.project_manager:
            ProjectManager.objects.create(**project_manager)

        data = {
            'title': 'title',
            'project_identifier': '0000000000',
            'project_manager_id': 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
            'body': {'preface': 'short text', 'content': 'long text'},
            'images': []
        }
        WarningMessages.objects.all().delete()
        warning_message = WarningMessages.objects.create(**data)
        self.warning_identifier = str(warning_message.identifier)

    @patch('firebase_admin.messaging.send_multicast', side_effect=firebase_admin_messaging_send_multicast)
    def test_post_notification(self, firebase_admin_messaging_send_multicast):
        MobileDevices.objects.all().delete()
        for mobile_device in self.data.mobile_devices:
            MobileDevices.objects.create(**mobile_device)

        data = {'title': 'title', 'body': 'text', 'warning_identifier': self.warning_identifier}
        result = self.client.post(self.url, json.dumps(data), headers=self.headers, content_type=self.content_type)

        self.assertEqual(result.status_code, 200)
        self.assertDictEqual(result.data, {'status': True, 'result': 'push-notification accepted'})

    @patch('firebase_admin.messaging.send_multicast', side_effect=firebase_admin_messaging_send_multicast)
    def test_post_notification_no_subscriptions(self, firebase_admin_messaging_send_multicast):
        data = {'title': 'title', 'body': 'text', 'warning_identifier': self.warning_identifier}
        result = self.client.post(self.url, json.dumps(data), headers=self.headers, content_type=self.content_type)

        self.assertEqual(result.status_code, 422)
        self.assertDictEqual(result.data, {'status': False, 'result': 'No subscribed devices found'})

    def test_post_notification_no_warning_message(self):
        data = {'title': 'title', 'body': 'text', 'warning_identifier': str(uuid.uuid4())}
        result = self.client.post(self.url, json.dumps(data), headers=self.headers, content_type=self.content_type)

        self.assertEqual(result.status_code, 404)
        self.assertDictEqual(result.data, {'status': False, 'result': messages.no_record_found})

    def test_post_notification_no_news_message(self):
        data = {'title': 'title', 'body': 'text', 'warning_identifier': self.warning_identifier, 'news_identifier': ''}
        result = self.client.post(self.url, json.dumps(data), headers=self.headers, content_type=self.content_type)

        self.assertEqual(result.status_code, 404)
        self.assertDictEqual(result.data, {'status': False, 'result': messages.no_record_found})

    def test_post_notification_no_identifiers(self):
        data = {'title': 'title', 'body': 'text'}
        result = self.client.post(self.url, json.dumps(data), headers=self.headers, content_type=self.content_type)

        self.assertEqual(result.status_code, 422)
        self.assertDictEqual(result.data, {'status': False, 'result': messages.invalid_query})

    def test_post_notification_title_body(self):
        data = {}
        result = self.client.post(self.url, json.dumps(data), headers=self.headers, content_type=self.content_type)

        self.assertEqual(result.status_code, 422)
        self.assertDictEqual(result.data, {'status': False, 'result': messages.invalid_query})

    @patch('firebase_admin.messaging.send_multicast', side_effect=firebase_admin_messaging_send_multicast)
    def test_get_notification(self, firebase_admin_messaging_send_multicast):
        MobileDevices.objects.all().delete()
        for mobile_device in self.data.mobile_devices:
            MobileDevices.objects.create(**mobile_device)
        data = {'title': 'title', 'body': 'text', 'warning_identifier': self.warning_identifier}
        result = self.client.post(self.url, json.dumps(data), headers=self.headers, content_type=self.content_type)

        self.assertEqual(result.status_code, 200)
        self.assertDictEqual(result.data, {'status': True, 'result': 'push-notification accepted'})

        result = self.client.get('{url}s?project-ids=0000000000'.format(url=self.url))
        result_data = json.loads(result.content.decode())
        identifier = result_data['result'][0]['identifier']
        expected_result = {
            'status': True,
            'result': [{
                'identifier': identifier,
                'title': 'title',
                'body': 'text',
                'project_identifier': '0000000000',
                'news_identifier': None,
                'warning_identifier': self.warning_identifier,
                'publication_date': result_data['result'][0]['publication_date']
            }]
        }

        self.assertEqual(result.status_code, 200)
        self.assertDictEqual(result_data, expected_result)

    @patch('firebase_admin.messaging.send_multicast', side_effect=firebase_admin_messaging_send_multicast)
    def test_get_notification_inactive_project(self, firebase_admin_messaging_send_multicast):
        MobileDevices.objects.all().delete()
        for mobile_device in self.data.mobile_devices:
            MobileDevices.objects.create(**mobile_device)
        data = {'title': 'title', 'body': 'text', 'warning_identifier': self.warning_identifier}
        result = self.client.post(self.url, json.dumps(data), headers=self.headers, content_type=self.content_type)

        self.assertEqual(result.status_code, 200)
        self.assertDictEqual(result.data, {'status': True, 'result': 'push-notification accepted'})

        project = Projects.objects.filter(pk='0000000000').first()
        project.active = False
        project.save()

        result = self.client.get('{url}s?project-ids=0000000000'.format(url=self.url))

        self.assertEqual(result.status_code, 404)
        self.assertDictEqual(result.data, {'status': False, 'result': 'No record found'})


    def test_get_notification_invalid_query(self):
        result = self.client.get('{url}s'.format(url=self.url))

        self.assertEqual(result.status_code, 422)
        self.assertDictEqual(result.data, {'status': False, 'result': messages.invalid_query})
