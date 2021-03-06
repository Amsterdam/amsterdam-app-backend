import firebase_admin
from threading import Thread
from amsterdam_app_api.UNITTESTS.mock_data import TestData
from queue import Queue
import requests
import json


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, status_code, json_data=None):
            self.status_code = status_code
            self.binary_data = [b'0', b'1']
            self.json_data = json_data

        def iter_content(self, size):
            for data in self.binary_data:
                yield data

        def json(self):
            return self.json_data

    if args[0] == 'valid_url':
        return MockResponse(200)
    elif args[0] == 'invalid_url':
        return MockResponse(404)
    elif args[0] == 'invalid_json_response?AppIdt=app-pagetype&reload=true':
        return MockResponse(200, json_data={})
    elif args[0] == 'valid_json_response?AppIdt=app-pagetype&reload=true':
        return MockResponse(200, json_data={'item': {'page': {'pagetype': 'mock'}}})
    elif args[0] == 'raise_exception?AppIdt=app-pagetype&reload=true':
        raise Exception('Mock exception')
    elif args[0] == 'https://www.amsterdam.nl/raise_exception?new_json=true&pager_rows=1000':
        raise Exception('Mock exception')
    elif args[0] == 'https://www.amsterdam.nl/get?new_json=true&pager_rows=1000':
        test_data = TestData()
        return MockResponse(200, json_data=test_data.iprox_projects)


class MockedThreading(Thread):
    def __init__(self, target=None, args=None, kwargs=None):
        super(Thread).__init__()
        self.target = target
        self.args = args
        self.kwargs = kwargs

    def start(self):
        if self.args is not None:
            self.target(*self.args)
        else:
            self.target(**self.kwargs)

    @staticmethod
    def join(**kwargs):
        return


def firebase_admin_messaging_send_multicast(args):
    class response:
        def __init__(self, success):
            self.success = success

    class Response:
        def __init__(self, args):
            self.args = args
            self.failure_count = 1
            self.responses = []
            for i in range(0, len(args.tokens)):
                if i == 0:
                    self.responses.append(response(False))
                else:
                    self.responses.append(response(True))

    return Response(args)


class address_to_coordinates:
    def __init__(self, *args, **kwargs):
        self.content = '{"results": [{"centroid": [0, -90]}]}'


class IproxStadslokettenValid:
    def __init__(self, *args, **kwargs):
        self.test_data = TestData()

    def json(self):
        return self.test_data.iprox_stadsloketten


class IproxStadslokettenInvalid:
    def __init__(self, *args, **kwargs):
        self.test_data = TestData()

    def json(self):
        return {}


class IproxStadslokettenException:
    def __init__(self, *args, **kwargs):
        self.test_data = TestData()

    def json(self):
        return 'Exception Data'


class IproxStadsloketValid:
    def __init__(self, *args, **kwargs):
        self.test_data = TestData()

    def json(self):
        return self.test_data.iprox_stadsloket


class IproxStadsloketInvalid:
    def __init__(self, *args, **kwargs):
        self.test_data = TestData()

    def json(self):
        return {}


class IproxStadsloketException:
    def __init__(self, *args, **kwargs):
        self.test_data = TestData()

    def json(self):
        return 'Exception Data'


class IproxStadsloketScraper:
    def __init__(self, url, **kwargs):
        self.url = url
        self.test_data = TestData()

    def json(self):
        if self.url == 'https://www.amsterdam.nl/contact/?AppIdt=app-pagetype&reload=true':
            return self.test_data.iprox_stadsloketten
        else:
            return self.test_data.iprox_stadsloket


class IproxStadsloketScraperImages:
    def __init__(self, *args, **kwargs):
        self.queue = Queue()
