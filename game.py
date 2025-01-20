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

    def call_api(self, endpoint, player_num, payload):
        url = "http://127.0.0.1:" + self.players[player_num].port + "/" + endpoint

    def run(self):
        results = ""
        game_status = "running"
        scores = [0] * len(self.players)
        start_player = 0

        while (game_status == "running"):
            hand_status = "running"
            while (hand_status == "running"):
                start_player += 1
                start_player %= len(self.players)
                player_turn = 0
                player_phase = 0
                updates = [""] * len(self.players)
                hands = [ [] ] * len(self.players)
                self.deck = Deck()
                self.deck.shuffle()

                # deal a hand to each player
                for i in range(10):
                    for j in range(len(self.players)):
                        hands[j].append(self.deck.deal())
                        if (i == 9):
                            # Call either start-*p-game or start-*p-hand
                            opponent_list = ",".join(self.players[k].name for k in range(len(self.players)) if k!=j)
                            if sum(self.scores)==0:
                                payload = {
                                    "game_id": str(self.game_id),
                                    "opponent": opponent_list,
                                    "hand": " ".join(hands[j])
                                }
                            else:
                                payload = {"hand": " ".join(hands[j])}

                            result = self.call_api("start-" + str(len(self.players)) + "p-" + ("game" if sum(self.scores)==0 else "hand"), j, payload)
                            # TODO - if result is invalid forfeit


                while (player_turn  < len(self.players)):  # Cycle through each player's turn once
                    current_player = (player_turn + start_player) % len(self.players)


                # start over with first player
                self.player_turn = 0
                self.player_phase = 0
        return results



