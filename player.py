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
        self.wins = 0
        self.losses = 0

    def set_playing(self, playing):
        self.playing = playing

    def is_playing(self):
        return self.playing

    def add_record(self, win=False):
        if (win): self.wins += 1
        else: self.losses += 1