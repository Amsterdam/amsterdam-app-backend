from django.db import connections, DEFAULT_DB_ALIAS
from django.test import TestCase
from amsterdam_app_api.UNITTESTS.mock_data import TestData
from amsterdam_app_api.models import Projects
from amsterdam_app_api.models import ProjectDetails
from amsterdam_app_api.GenericFunctions.TextSearch import TextSearch


class SetUp:
    def __init__(self):
        # Create needed database extensions
        connection = connections[DEFAULT_DB_ALIAS]
        cursor = connection.cursor()
        cursor.execute('CREATE EXTENSION pg_trgm')
        cursor.execute('CREATE EXTENSION unaccent')

        self.data = TestData()
        for project in self.data.projects:
            Projects.objects.create(**project)

        for project in self.data.project_details:
            ProjectDetails.objects.create(**project)


class TestTextSearch(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestTextSearch, self).__init__(*args, **kwargs)
        self.data = TestData()

    def setUp(self):
        SetUp()

    def test_search(self):
        text_search = TextSearch(ProjectDetails, 'test0', 'title,subtitle', return_fields='title,subtitle', page_size=2, page=0)
        result = text_search.search()
        expected_result = {
            'page':
                [
                    {'title': 'test0', 'subtitle': 'subtitle', 'score': 1.0},
                    {'title': 'test0', 'subtitle': 'subtitle', 'score': 1.0}
                ],
            'pages': 1
        }

        self.assertDictEqual(result, expected_result)

    def test_search_paginated(self):
        text_search = TextSearch(ProjectDetails, 'test0', 'title,subtitle', return_fields='title,subtitle', page_size=1, page=1)
        result = text_search.search()
        expected_result = {
            'page': [{'title': 'test0', 'subtitle': 'subtitle', 'score': 1.0}],
            'pages': 2
        }

        self.assertDictEqual(result, expected_result)

    def test_search_2_letters(self):
        text_search = TextSearch(ProjectDetails, 'te', 'title,subtitle', return_fields='title,subtitle', page_size=2, page=0)
        result = text_search.search()
        expected_result = {'page': [], 'pages': 0}

        self.assertDictEqual(result, expected_result)
