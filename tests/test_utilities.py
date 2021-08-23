import unittest
from depfarm import utilities
import os

file_names = ['AK_BrooksCamp_2012/\n', 'AK_Coastal_2009/\n']

get_info_1 = ([-17347360, 8065364, -12414, -
              17321558, 8091166, 13388], 529285317)
get_info_2 = ([-15730544, 10937407, -19027, -
              15691854, 10976097, 19663], 55711772)


class TestCases(unittest.TestCase):
    def test_get_info_1(self):
        value = utilities.get_info('https://s3-us-west-2.amazonaws.com/usgs-lidar-public/' +
                                   (file_names[0][:-1])+'ept.json')

        self.assertEqual(get_info_1, value)

    def test_get_info_2(self):
        value = utilities.get_info('https://s3-us-west-2.amazonaws.com/usgs-lidar-public/' +
                                   (file_names[1][:-1])+'ept.json')

        self.assertEqual(get_info_2, value)


if __name__ == '__main__':
    unittest.main()
