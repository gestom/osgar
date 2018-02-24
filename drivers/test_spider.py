import unittest
from unittest.mock import MagicMock

from drivers.spider import Spider, CAN_packet
from lib.logger import LogWriter

class SpiderTest(unittest.TestCase):

    def test_split_buffer(self):
        self.assertEqual(Spider.split_buffer(b''), (b'', b''))
        self.assertEqual(Spider.split_buffer(b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xfe\x10'), (b'', b'\xfe\x10'))
        data = b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xfeW\xfe0@h\x9e\x01i\x01\xf7\x01\x18\x00'
        self.assertEqual(Spider.split_buffer(data), (b'\xfe0@h\x9e\x01i\x01\xf7\x01\x18\x00', b'\xfeW'))

        data = b'0@h\x9e\x01i\x01\xf7\x01\x18\x00'
        self.assertEqual(Spider.split_buffer(data), (b'h\x9e\x01i\x01\xf7\x01\x18\x00', b'0@'))

    def test_can_packet(self):
        self.assertEqual(CAN_packet(0x400, [0, 0]), b'\x80\x02\x00\x00')

    def test_uninitialized_can_bridge(self):
        bus = MagicMock()
        spider = Spider(config={'stream_id_in':1, 'stream_id_out':2}, bus=bus)
        spider.send((0, 0))
#        bus.write.assert_called_once_with(0, 'ERROR: CAN bridge not initialized yet! [(0, 0)]')

# vim: expandtab sw=4 ts=4