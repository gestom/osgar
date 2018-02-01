"""
  RoboOrienteering 2018 - experiments with lib.logger and robot container
"""

import argparse
import sys
from queue import Queue

from lib.logger import LogWriter, LogReader
from lib.config import Config
from drivers import all_drivers


class RoboOrienteering2018:
    def __init__(self, config, logger):
        self.logger = logger
        self.stream_id = config['stream_id']
        self.drivers = []
        for driver_name in config['drivers']:
            driver = all_drivers[driver_name](config[driver_name], logger,
                                              output=self.input_gate, name=driver_name)
            self.drivers.append(driver)
        self.queue = Queue()

    def start(self):
        for driver in self.drivers:
            driver.start()

    def update(self, timeout=5):
        if len(self.drivers) > 0:
            data = self.queue.get(timeout=timeout)
            if 'gps' in data:
                print(data)

    def finish(self):
        for driver in self.drivers:
            driver.request_stop()
        for driver in self.drivers:
            driver.join()

    def input_gate(self, name, data):
        if name == 'gps':
            print(name, data)
        dt = self.logger.write(self.stream_id, bytes(str((name, data)),'ascii'))  # TODO single or mutiple streams?
        self.queue.put((dt, name, data))

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
