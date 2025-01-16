from deck import Card, Deck

"""
By Todd Dole, Revision 1.0
Written for Hardin-Simmons CSCI-4332 Artificial Intelligence
"""

class Game:
    _counter = 0

    def __init__(self, players):
        self.players = players
        self.deck = Deck()
        self.deck.shuffle()
        Game._counter += 1
        self.game_id = Game._counter




