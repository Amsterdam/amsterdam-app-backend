from django.test import TestCase
from amsterdam_app_api.GenericFunctions.Distance import Distance


class TestDistance(TestCase):
    def test_distance_valid(self):
        distance = Distance((0.0, 0.0), (1.0, 1.0))
        self.assertEqual(distance.meter, 156899.56829134029)
        self.assertEqual(distance.strides, 212026.44363694632)

    def test_distance_in_valid(self):
        distance = Distance(('a', 'b'), ('c', 'd'))
        self.assertEqual(distance.meter, 0.0)
        self.assertEqual(distance.strides, 0.0)
