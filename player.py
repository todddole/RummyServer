import datetime

"""
By Todd Dole, Revision 1.0
Written for Hardin-Simmons CSCI-4332 Artificial Intelligence
"""

class Player:
    def __init__(self, address, port, name):
        self.address = address
        self.port = port
        self.name = name
        self.last = datetime.datetime.now()
        self.playing = False

    def set_playing(self, playing):
        self.playing = playing

    def is_playing(self):
        return self.playing