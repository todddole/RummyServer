import random

"""
By Todd Dole, Revision 1.0
Written for Hardin-Simmons CSCI-4332 Artificial Intelligence
"""


class Card:
    def __init__(self, suit, value):
        self.suit = suit
        self.value = value

    def __repr__(self):
        return f"{self.value} of {self.suit}"

class Deck:
    def __init__(self):
        suits = ["H", "D", "C", "S"]
        values = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K"]
        self.cards = [Card(suit, value) for suit in suits for value in values]

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self):
        if len(self.cards) > 0:
            return self.cards.pop()
        else:
            return None

