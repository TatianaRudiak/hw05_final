from django.test import TestCase


class MyTestCase(TestCase):
    def assert_equal_attr(self, actual, expected, *args):
        if args:
            for attr_name in args:
                with self.subTest(attr_name=attr_name):
                    self.assertEqual(getattr(actual, attr_name), getattr(expected, attr_name))
        else:
            self.assertEqual(type(expected), type(actual))
            self.assertEqual(actual, expected)
