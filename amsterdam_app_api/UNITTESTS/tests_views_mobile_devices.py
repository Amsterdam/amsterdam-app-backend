import os
from django.test import Client
from django.test import TestCase
from amsterdam_app_api.UNITTESTS.mock_data import TestData
from amsterdam_app_api.GenericFunctions.AESCipher import AESCipher
from amsterdam_app_api.models import MobileDevices
from amsterdam_app_api.serializers import MobileDevicesSerializer
from amsterdam_app_api.api_messages import Messages
from amsterdam_app_api.models import Projects

messages = Messages()


class SetUp:
    def __init__(self):
        self.data = TestData()
        for project in self.data.projects:
            Projects.objects.create(**project)


class TestApiDeviceRegistration(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestApiDeviceRegistration, self).__init__(*args, **kwargs)
        self.url = '/api/v1/device_registration'
        self.token = AESCipher(os.getenv('APP_TOKEN'), os.getenv('AES_SECRET')).encrypt()

    def setUp(self):
        SetUp()
        MobileDevices.objects.all().delete()

    def test_register_device_valid(self):
        json_data = '{"device_token": "0000000000", "os_type": "ios", "projects": ["0000000000"]}'

        c = Client()
        result = c.post(self.url, json_data, headers={"DeviceAuthorization": self.token}, content_type="application/json")

        self.assertEqual(result.status_code, 200)
        self.assertDictEqual(result.data, {'status': True, 'result': {'active': ['0000000000'], 'inactive': [], 'deleted': []}})

    def test_register_device_update(self):
        c = Client()

        json_data0 = '{"device_token": "0000000000", "os_type": "ios", "projects": ["0000000000"]}'
        result = c.post(self.url, json_data0, headers={"DeviceAuthorization": self.token}, content_type="application/json")

        self.assertEqual(result.status_code, 200)
        self.assertDictEqual(result.data, {'status': True, 'result': {'active': ['0000000000'], 'inactive': [], 'deleted': []}})

        json_data1 = '{"device_token": "0000000000", "os_type": "ios", "projects": ["0000000000", "1111111111"]}'
        result = c.post(self.url, json_data1, headers={"DeviceAuthorization": self.token}, content_type="application/json")

        self.assertEqual(result.status_code, 200)
        self.assertDictEqual(result.data, {'status': True, 'result': {'active': ['0000000000'], 'inactive': [], 'deleted': ['1111111111']}})

        mobile_devices = MobileDevices.objects.all()
        serializer = MobileDevicesSerializer(mobile_devices, many=True)
        self.assertEqual(len(serializer.data), 1)

    def test_register_device_update_refresh_token(self):
        c = Client()

        json_data0 = '{"device_token": "0000000000", "os_type": "ios", "projects": ["0000000000"]}'
        result = c.post(self.url, json_data0, headers={"DeviceAuthorization": self.token}, content_type="application/json")

        self.assertEqual(result.status_code, 200)
        self.assertDictEqual(result.data, {"status": True, "result": {"active": ["0000000000"], "inactive": [], "deleted": []}})

        json_data1 = '{"device_token": "0000000000", "device_refresh_token": "0000000001"}'
        result = c.post(self.url, json_data1, headers={"DeviceAuthorization": self.token}, content_type="application/json")

        self.assertEqual(result.status_code, 200)
        self.assertDictEqual(result.data, {'status': True, 'result': {'active': ['0000000000'], 'inactive': [], 'deleted': []}})

        mobile_devices = MobileDevices.objects.filter(pk="0000000001").first()
        self.assertEqual(mobile_devices.device_token, "0000000001")
        self.assertEqual(mobile_devices.os_type, "ios")
        self.assertEqual(mobile_devices.projects, ["0000000000"])

    def test_unknown_device(self):
        c = Client()

        json_data = '{"device_token": "0000000000", "device_refresh_token": "0000000001"}'
        result = c.post(self.url, json_data, headers={"DeviceAuthorization": self.token}, content_type="application/json")

        self.assertEqual(result.status_code, 404)
        self.assertDictEqual(result.data, {'status': False, 'result': messages.no_record_found})

    def test_register_device_auto_removal(self):
        c = Client()

        json_data0 = '{"device_token": "0000000000", "os_type": "ios", "projects": ["0000000000"]}'
        result = c.post(self.url, json_data0, headers={"DeviceAuthorization": self.token}, content_type="application/json")

        self.assertEqual(result.status_code, 200)
        self.assertDictEqual(result.data, {'status': True, 'result': {'active': ['0000000000'], 'inactive': [], 'deleted': []}})

        json_data1 = '{"device_token": "0000000000", "os_type": "ios", "projects": []}'
        result = c.post(self.url, json_data1, headers={"DeviceAuthorization": self.token}, content_type="application/json")

        self.assertEqual(result.status_code, 204)
        self.assertDictEqual(result.data, {'status': True, 'result': 'Device removed from database'})

        mobile_devices = MobileDevices.objects.all()
        serializer = MobileDevicesSerializer(mobile_devices, many=True)
        self.assertEqual(len(serializer.data), 0)

    def test_register_device_invalid_request(self):
        c = Client()

        json_data0 = '{"device_token": "0000000000", "projects": ["0000000000"]}'
        result = c.post(self.url, json_data0, headers={"DeviceAuthorization": self.token}, content_type="application/json")

        self.assertEqual(result.status_code, 422)
        self.assertDictEqual(result.data, {'status': False, 'result': messages.invalid_query})

        json_data1 = '{"os_type": "ios", "projects": ["0000000000"]}'
        result = c.post(self.url, json_data1, headers={"DeviceAuthorization": self.token}, content_type="application/json")

        self.assertEqual(result.status_code, 422)
        self.assertDictEqual(result.data, {'status': False, 'result': messages.invalid_query})

    def test_register_device_delete(self):
        c = Client()

        json_data0 = '{"device_token": "0000000000", "os_type": "ios", "projects": ["0000000000"]}'
        result = c.post(self.url, json_data0, headers={"DeviceAuthorization": self.token}, content_type="application/json")

        self.assertEqual(result.status_code, 200)
        self.assertDictEqual(result.data, {'status': True, 'result': {'active': ['0000000000'], 'inactive': [], 'deleted': []}})

        result = c.delete('{url}?id=0000000000'.format(url=self.url), headers={"DeviceAuthorization": self.token})

        self.assertEqual(result.status_code, 204)
        self.assertDictEqual(result.data, {'status': True, 'result': 'Device removed from database'})

        mobile_devices = MobileDevices.objects.all()
        serializer = MobileDevicesSerializer(mobile_devices, many=True)
        self.assertEqual(len(serializer.data), 0)

    def test_register_device_delete_no_identifier(self):
        c = Client()

        result = c.delete(self.url, headers={"DeviceAuthorization": self.token})

        self.assertEqual(result.status_code, 422)
        self.assertDictEqual(result.data, {'status': False, 'result': messages.invalid_query})

    def test_invalid_token(self):
        c = Client()

        result = c.post(self.url, headers={"DeviceAuthorization": 'invalid'})

        self.assertEqual(result.status_code, 403)
        self.assertEqual(result.reason_phrase, 'Forbidden')
