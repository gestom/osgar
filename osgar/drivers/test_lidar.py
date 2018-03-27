import unittest
from unittest.mock import MagicMock

from osgar.drivers.lidar import Lidar
from osgar.drivers.bus import BusHandler


class LidarTest(unittest.TestCase):

    def test_start_stop(self):
        config = {}
        logger = MagicMock()
        bus = BusHandler(logger, out={'orientation':[]}, name='imu')
        lidar = Lidar(config, bus=bus)
        lidar.start()
        lidar.request_stop()
        lidar.join()

# vim: expandtab sw=4 ts=4
