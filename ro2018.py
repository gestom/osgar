"""
  RoboOrienteering 2018 - experiments with lib.logger and robot container
"""

import argparse
import sys
import math
from datetime import timedelta

from lib.logger import LogWriter, LogReader
from lib.config import Config
from drivers import all_drivers
from robot import Robot


class LogRobot:
    def __init__(self, logger, stream_id_in, stream_id_out):
        self.log_read = logger.read_gen(multiple_streams=[stream_id_in, stream_id_out])
        self.stream_id_in = stream_id_in
        self.stream_id_out = stream_id_out

    def update(self):
        dt, stream, packet = next(self.log_read)
        assert stream == self.stream_id_in, (stream, self.stream_id_in)
        msg_id, data = eval(packet)  # TODO replace by safe version!
        return dt, msg_id, data

    def execute(self, msg_id, data):
        if self.stream_id_out is None:  # i.e. ignore outputs
            return
        dt, stream, packet = next(self.log_read)
        assert stream == self.stream_id_out, (stream, self.stream_id_out)
        log_msg_id, log_data = eval(packet)  # TODO replace by safe version!
        assert (msg_id, data) == (log_msg_id, log_data), ((msg_id, data), (log_msg_id, log_data))


def geo_length(pos1, pos2):
    "return distance on sphere for two integer positions in milliseconds"
    x_scale = math.cos(math.radians(pos1[0]/3600000))
    scale = 40000000/(360*3600000)
    return math.hypot((pos2[0] - pos1[0])*x_scale, pos2[1] - pos1[1]) * scale


def geo_angle(pos1, pos2):
    if geo_length(pos1, pos2) < 1.0:
        return None
    x_scale = math.cos(math.radians(pos1[0]/3600000))
    return math.atan2(pos2[1] - pos1[1], (pos2[0] - pos1[0])*x_scale)


class RoboOrienteering2018:
    def __init__(self, robot):
        self.robot = robot
        self.goal = (51749517 + 100, 180462688)  # TODO extra configuration
        self.time = None
        self.last_position = None  # (lon, lat) in milliseconds
        self.last_imu_yaw = None  # magnetic north in degrees
        self.cmd = (0, 0)

    def update(self):
        packet = self.robot.update()
        if packet is not None:
#            print('RO', packet)
            timestamp, msg_id, data = packet
            self.time = timestamp
            if msg_id == 'gps':
                self.last_position = data
            elif msg_id == 'imu':
                (yaw, pitch, roll), (magx, y, z), (accx, y, z), (gyrox, y, z) = data
                self.last_imu_yaw = yaw
            elif msg_id == 'spider':  # i.e. I can drive only spider??
                self.robot.execute('spider', self.cmd)

    def set_speed(self, speed, angular_speed):
        self.cmd = (speed, angular_speed)

    def play0(self):
        for i in range(10):
            self.update()
        self.set_speed(10, 0)
        for i in range(100):
            self.update()
        self.set_speed(0, 0)
        for i in range(10):
            self.update()

    def play(self):
        print("Waiting for valid GPS position...")
        while self.last_position is None or self.last_position == (None, None):
            self.update()
        print("Ready")
        print("Goal at %.2fm" % geo_length(self.last_position, self.goal))

        print("Heading %.1fdeg" % math.degrees(geo_angle(self.last_position, self.goal)))
        
        start_time = self.time
        while geo_length(self.last_position, self.goal) > 1.0 and self.time - start_time < timedelta(seconds=10):
            self.set_speed(10, 0)
            prev_time = self.time
            self.update()
            if int(prev_time.total_seconds()) != int(self.time.total_seconds()):
                print(self.time, geo_length(self.last_position, self.goal))

        print("STOP (3s)")
        self.set_speed(0, 0)
        start_time = self.time
        while self.time - start_time < timedelta(seconds=3):
            self.set_speed(0, 0)
            self.update()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='RoboOrienteering 2018')
    subparsers = parser.add_subparsers(help='sub-command help', dest='command')
    subparsers.required = True
    parser_run = subparsers.add_parser('run', help='run on real HW')
    parser_run.add_argument('config', help='configuration file')
    parser_run.add_argument('--note', help='add description')

    parser_replay = subparsers.add_parser('replay', help='replay from logfile')
    parser_replay.add_argument('logfile', help='recorded log file')
    parser_replay.add_argument('--force', '-F', dest='force', action='store_true', help='force replay even for failing output asserts')
    args = parser.parse_args()

    if args.command == 'replay':
        log = LogReader(args.logfile)
        print(next(log.read_gen(0))[-1])  # old arguments
        config_str = next(log.read_gen(0))[-1]
        config = eval(config_str)  # TODO what was the safe version of eval?!
        if args.force:
            robot = LogRobot(log, config['robot']['stream_id'], stream_id_out=None)
        else:
            robot = LogRobot(log, config['robot']['stream_id'], config['robot']['stream_id_out'])
        game = RoboOrienteering2018(robot)
        game.play()

    elif args.command == 'run':
        log = LogWriter(prefix='ro2018-', note=str(sys.argv))
        config = Config.load(args.config)
        log.write(0, bytes(str(config.data), 'ascii'))  # write configuration
        robot = Robot(config=config.data['robot'], logger=log)
        robot.start()
        game = RoboOrienteering2018(robot)
        game.play()
        robot.finish()
    else:
        assert False, args.command  # unsupported command

# vim: expandtab sw=4 ts=4
