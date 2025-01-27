import random

"""
By Todd Dole, Revision 1.0
Written for Hardin-Simmons CSCI-4332 Artificial Intelligence
"""


class Card:
    def __init__(self, suit, value=""):
        if (value==""):
            self.value = suit[0:1]
            self.suit = suit[1:]
        else:
            self.suit = suit
            self.value = value
        self.cv = 0
        if self.suit=="D": self.cv+=13
        elif self.suit=="H": self.cv+=26
        elif self.suit=="S": self.cv+=39
        if self.value== "A": self.cv+=1
        elif self.value=="T": self.cv+=10
        elif self.value=="J": self.cv+=11
        elif self.value=="Q": self.cv+=12
        elif self.value=="K": self.cv+=13
        else: self.cv+=int(self.value)

    def __lt__(self, other):
        return self.cv < other.cv

    def __gt__(self, other):
        return self.cv > other.cv

    def __repr__(self):
        return f"{self.value}{self.suit}"

    def get_score(self):
        if self.value.isdigit():
            return int(self.value)
        if self.value == 'A': return 1
        return 10

    def get_cv(self):
        return self.cv

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

    def return_card(self, card):
        if card not in self.cards:
            self.cards.append(card)