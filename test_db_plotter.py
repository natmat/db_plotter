from unittest import TestCase

from db_plotter import Route

waypoints = {(1,2),(3,4)}

class TestRoute(TestCase):
    def setUp(self):
        self.route = Route()

class TestWpValid(TestRoute):
    def test_wp_valid(self):
        wp = (1,2)
        to = (3,4)
        self.assertTrue(self.route.is_valid(wp, to, "UP"))
