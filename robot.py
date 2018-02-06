"""
  Robot - container for drivers
"""

import argparse
import sys
from queue import Queue

from lib.logger import LogWriter, LogReader
from lib.config import Config
from drivers import all_drivers


class Robot:
    def __init__(self, config, logger):
        self.logger = logger
        self.stream_id = config['stream_id']
        self.stream_id_out = config.get('stream_id_out', None)
        self.stream_id_ref = config.get('stream_id_ref', None)
        self.drivers = []
        self.executors = []
        for driver_name in config['drivers']:
            driver = all_drivers[driver_name](config[driver_name], logger,
                                              output=self.input_gate, name=driver_name)
            self.drivers.append(driver)
            if 'executors' in config and driver_name in config['executors']:
                self.executors.append(driver)
        self.queue = Queue()

    def start(self):
        for driver in self.drivers:
            driver.start()

    def update(self, timeout=5):
        if len(self.drivers) > 0:
            data = self.queue.get(timeout=timeout)
            if self.stream_id_ref is not None:
                ignore_dt = self.logger.write(self.stream_id_ref, bytes(str(data),'ascii'))
            return data
        return None

    def finish(self):
        for driver in self.drivers:
            driver.request_stop()
        for driver in self.drivers:
            driver.join()

    def input_gate(self, name, data):
        with self.logger.lock:  # make sure that order by timestamp is preserved            
            dt = self.logger.write(self.stream_id, bytes(str((name, data)),'ascii'))  # TODO single or mutiple streams?
            self.queue.put((dt, name, data))

    def execute(self, msg_id, data):
        assert self.stream_id_out is not None
        dt = self.logger.write(self.stream_id_out, bytes(str((msg_id, data)),'ascii'))
        for driver in self.executors:
            driver.send(data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test robot configuration')
    subparsers = parser.add_subparsers(help='sub-command help', dest='command')
    subparsers.required = True
    parser_run = subparsers.add_parser('run', help='run on real HW')
    parser_run.add_argument('config', help='configuration file')
    parser_run.add_argument('--note', help='add description')

    parser_replay = subparsers.add_parser('replay', help='replay from logfile')
    parser_replay.add_argument('logfile', help='recorded log file')
    args = parser.parse_args()

    if args.command == 'replay':
        pass  # TODO
    elif args.command == 'run':
        log = LogWriter(prefix='robot-test-', note=str(sys.argv))
        config = Config.load(args.config)
        log.write(0, bytes(str(config.data), 'ascii'))  # write configuration
        robot = Robot(config=config.data['robot'], logger=log)
        robot.start()
        for i in range(1000):
            robot.update()
        robot.finish()
    else:
        assert False, args.command  # unsupported command

# vim: expandtab sw=4 ts=4
