"""
  SICK Tim571 LIDAR Driver
"""

from threading import Thread

from osgar.drivers.bus import BusShutdownException


STX = b'\x02'
ETX = b'\x03'


class Lidar(Thread):
    def __init__(self, config, bus):
        Thread.__init__(self)
        self.setDaemon(True)

        self.bus = bus
        self.buf = b''

    def process_packet(self, packet):
        if packet.startswith(STX) and packet.endswith(ETX):
            return packet  # TODO parse
        return None

    def split_buffer(self, data):
        i = data.find(ETX)
        if i >= 0:
            return data[i + 1:], data[:i + 1]
        return data, b''

    def process_gen(self, data):
        self.buf, packet = self.split_buffer(self.buf + data)
        while len(packet) > 0:
            ret = self.process_packet(packet)
            if ret is not None:
                yield ret
            # now process only existing (remaining) buffer
            self.buf, packet = self.split_buffer(self.buf)  

    def run(self):
        try:
            self.bus.publish('raw', STX + b'sRN LMDscandata' + ETX)
            while True:
                packet = self.bus.listen()
                dt, __, data = packet
                for out in self.process_gen(data):
                    assert out is not None
                    self.bus.publish('scan', out)
                    self.bus.publish('raw', STX + b'sRN LMDscandata' + ETX)
        except BusShutdownException:
            pass

    def request_stop(self):
        self.bus.shutdown()

