import unittest
import os
import time

import numpy as np

from osgar.lib.logger import LogWriter, LogReader, LogAsserter, INFO_STREAM_ID


class LoggerTest(unittest.TestCase):
    
    def test_writer_prefix(self):
        log = LogWriter(prefix='tmp')
        self.assertTrue(log.filename.startswith('tmp'))
        log.close()
        os.remove(log.filename)

    def test_context_manager(self):
        with LogWriter(prefix='tmpp', note='1st test') as log:
            self.assertTrue(log.filename.startswith('tmpp'))
            filename = log.filename
            start_time = log.start_time
            t1 = log.write(10, b'\x01\x02\x02\x04')
            time.sleep(0.01)
            t2 = log.write(10, b'\x05\x06\x07\x08')
            self.assertLess(t1, t2)
        
        with LogReader(filename) as log:
            self.assertEqual(start_time, log.start_time)

            __, stream_id, data = next(log.read_gen())
            self.assertEqual(INFO_STREAM_ID, stream_id)

            t, stream_id, data = next(log.read_gen())
            self.assertEqual(stream_id, 10)
            self.assertEqual(data, b'\x01\x02\x02\x04')

            t, stream_id, data = next(log.read_gen())
            self.assertTrue(t.microseconds > 100)
            
            with self.assertRaises(StopIteration):
                __ = next(log.read_gen())

        with LogReader(filename) as log:
            for t, stream_id, data in log.read_gen(only_stream_id=10):
                self.assertEqual(stream_id, 10)
                self.assertEqual(data, b'\x01\x02\x02\x04')
                break

        os.remove(log.filename)

    def test_read_two_streams(self):
        with LogWriter(prefix='tmp2', note='test_read_two_streams') as log:
            filename = log.filename
            t1 = log.write(1, b'\x01\x02\x02\x04')
            time.sleep(0.001)
            t2 = log.write(3, b'\x05\x06')
            time.sleep(0.001)
            t3 = log.write(2, b'\x07\x08')

        with LogReader(filename) as log:
            arr = []
            for t, stream_id, data in log.read_gen([1, 2]):
                self.assertIn(stream_id, [1, 2])
                arr.append((t, stream_id))
            self.assertEqual(arr, [(t1, 1), (t3, 2)])

        os.remove(log.filename)

    def test_register(self):
        with LogWriter(prefix='tmp2', note='test_register') as log:
            filename = log.filename
            self.assertEqual(log.register('raw'), 1)

            with self.assertRaises(AssertionError):
                log.register('raw')  # duplicity name

            self.assertEqual(log.register('gps.position'), 2)

        with LogReader(filename) as log:
            arr = []
            for __, __, data in log.read_gen(INFO_STREAM_ID):
                if b'names' in data:
                    arr.append(data)
            self.assertEqual(len(arr), 2, arr)
            self.assertEqual(arr[0], b"{'names': ['raw']}")
            self.assertEqual(arr[1], b"{'names': ['raw', 'gps.position']}")

        os.remove(filename)

    def test_log_asserter(self):
        with LogWriter(prefix='tmp3', note='test_log_asserter') as log:
            filename = log.filename
            t1 = log.write(1, b'\x01\x02')
            time.sleep(0.001)
            t2 = log.write(2, b'\x05')
            time.sleep(0.001)
            t3 = log.write(1, b'\x07\x08')

        with LogAsserter(filename) as log:
            log.assert_stream_id = 2
            arr = []
            for t, stream_id, data in log.read_gen([1, 2]):
                self.assertIn(stream_id, [1,2])
                if stream_id == 2:
                    log.write(2, b'\x05')
                arr.append((t, stream_id))
            self.assertEqual(arr, [(t1, 1), (t2, 2), (t3, 1)])

        os.remove(log.filename)

# vim: expandtab sw=4 ts=4
