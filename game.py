from deck import Card, Deck
import requests
import logging
import time

"""
By Todd Dole, Revision 1.0
Written for Hardin-Simmons CSCI-4332 Artificial Intelligence
"""

class Game:
    _counter = 0

    def __init__(self, players, test=False):
        self.players = players
        self.deck = Deck()
        self.deck.shuffle()
        Game._counter += 1
        self.game_id = Game._counter
        self.events = []
        for _ in range(len(players)):
            self.events.append("")
        self.players_left = len(self.players)
        self.discard_pile = []
        self.game_status = ""
        self.hand_status = ""
        self.test_game = test

    def call_shutdown(self, player_num):
        url = "http://127.0.0.1:" + self.players[player_num].port + "/shutdown"
        try:
            response = requests.get(url)
            if response.status_code != 200:
                logging.error("Game " + str(self.game_id) + " shutdown Failed, status code "+str(response.status_code) + ", URL: "+url)
        except Exception as e:
            logging.warning("Error shutting down "+url)




    def call_api(self, endpoint, player_num, payload):
        url = "http://127.0.0.1:" + self.players[player_num].port + "/" + endpoint
        try:
            response = requests.post(url, json=payload, timeout=200)
        except requests.exceptions.Timeout:
            logging.error("Game " + str(self.game_id) + " API Call timed out: "+url)
            return {"status":"timeout"}
        except Exception as e:
            logging.error("Game " + str(self.game_id) + " API Call Failed to Connect: "+url)
            return {"status":"error"}

        if response.status_code == 200:
            logging.info("Game " + str(self.game_id) + " API Call Successful: "+url)
            return response.json()
        else:
            logging.error("Game " + str(self.game_id) + " API Call Failed, status code "+str(response.status_code) + ", URL: "+url)
            return {"status":"error"}

    def update_players(self):

        for i in range(len(self.players)):
            if self.events[i]=="": continue
            payload = {
                "game_id": str(self.game_id),
                "event": self.events[i]
            }
            result = self.call_api(
                "update-"+str(len(self.players)) +"p-game/",
                i,
                payload)
            self.events[i]=""

            # TODO - Add forfeit code here on invalid result


    def forfeit(self, player_number, reason):
        self.scores[player_number]+=(1000 * self.players_left)
        self.players_left -= 1
        logging.warning("Game " + str(self.game_id) + " Forfeit by " + self.players[player_number].name + " (" + reason + ")")

        forfeit_str = self.players[player_number].name + " Forfeits (" + reason + ")\n"
        for i in range(len(self.players)):
            self.events[i]+= forfeit_str

        if self.players_left <= 1:
            # Hand and Game Ends, build the event report strings

            hand_str = "Hand Ends:"
            game_str = "Game Ends:"
            self.hand_status = "done"
            self.game_status = "done"
            for i in range(len(self.players)):
                hand_str += " " + self.players[i].name + " " + str(self.scores[i])
                game_str += " " + self.players[i].name + " " + str(self.scores[i])
                if (self.scores[i]<1000): game_str+=" *"
            for i in range(len(self.players)):
                self.events[i]+=hand_str + "\n"
                self.events[i]+=game_str + "\n"

            self.update_players() # Notify players of the game ending.

        else:
            for card in self.hands[player_number]:
                self.discard_pile.append(card)

            self.hands[player_number] = []

    def shuffle_discard(self):
        if (len(self.discard_pile)>5):
            save_cards = 3
        elif (len(self.discard_pile)>3):
            save_cards = 2
        else:
            save_cards = 1

        for i in range(len(self.discard_pile), save_cards-1, -1):
            self.deck.return_card(self.discard_pile.pop())

        self.deck.shuffle()
        for i in range(len(self.players)):
            self.events[i]+= "Shuffled discard, kept top "+str(save_cards)+"\n"

    def run(self):
        results = ""
        self.game_status = "running"
        self.scores = [0] * len(self.players)
        start_player = 0

        while (self.game_status == "running"):
            self.hand_status = "running"
            while (self.hand_status == "running"):
                start_player += 1
                start_player %= len(self.players)
                player_turn = 0
                player_phase = 0
                self.hands = []
                for _ in range(len(self.players)):
                    self.hands.append([])
                self.deck = Deck()
                self.deck.shuffle()

                # deal a hand to each player
                for i in range(10):
                    for j in range(len(self.players)):
                        if self.scores[j]>=500: continue        # Skip forfeited players
                        self.hands[j].append(self.deck.deal())
                        if (i == 9):

                            # Call either start-*p-game or start-*p-hand
                            hand_str = ""
                            for card in self.hands[j]: hand_str += str(card) + " "
                            hand_str = hand_str[:-1]

                            if sum(self.scores)==0:
                                opponent_list = ",".join(self.players[k].name for k in range(len(self.players)) if k != j)

                                payload = {
                                    "game_id": str(self.game_id),
                                    "opponent": opponent_list,
                                    "hand": hand_str
                                }
                            else:
                                payload = {"hand": hand_str}

                            result = self.call_api("start-" + str(len(self.players)) + "p-" + ("game" if sum(self.scores)==0 else "hand"), j, payload)
                            # If the result is invalid, forfeit
                            if "status" in result:
                                if result["status"] == "error":
                                    self.forfeit(j, "API error")
                                elif result["status"] == "timeout":
                                    self.forfeit(j, "API timeout")

                # put a card on discard
                card = self.deck.deal()
                self.discard_pile.insert(0, card)
                for i in range(len(self.players)):
                    self.events[i] += "Dealer discards " + str(card) + "\n"

                while (player_turn  < len(self.players) and self.hand_status=="running"):  # Cycle through each player's turn once
                    current_player = (player_turn + start_player) % len(self.players)
                    if self.scores[current_player]>=1000: continue # player disqualified, skip

                    # call the draw api
                    payload = {
                        "game_id": str(self.game_id),
                        "event": self.events[current_player]
                    }
                    self.events[current_player] = ""

                    result = self.call_api("draw/", current_player, payload)
                    if "play" in result:
                        # process the play
                        play_string = result["play"]
                        if ("draw discard") in play_string:
                            if (len(self.discard_pile)==0):
                                self.forfeit(current_player, "Drew from empty discard pile")
                            else:
                                card = self.discard_pile.pop(0)
                                draw_string = self.players[current_player].name + " takes "+str(card) + "\n"
                                for i in range(len(self.players)):
                                    self.events[i]+= draw_string
                                self.hands[current_player].append(card)
                        elif ("draw stock") in play_string:
                            card = self.deck.deal()
                            draw_string = self.players[current_player].name + " draws " + str(card) + "\n"
                            for i in range(len(self.players)):
                                if i==current_player:
                                    self.events[i] += draw_string
                                    logging.info("Game " + str(self.game_id) + ": " + draw_string)
                                else:
                                    self.events[i] += self.players[current_player].name + " draws\n"

                            self.hands[current_player].append(card)
                            if (len(self.deck.cards)<=1):
                                self.shuffle_discard()
                        else:
                            self.forfeit(current_player, "Invalid Play Response")
                            continue

                    elif "status" in result:
                        if result["status"] == "error":
                            self.forfeit(current_player, "API error")
                            continue
                        elif result["status"] == "timeout":
                            self.forfeit(current_player, "API timeout")
                            continue

                    # call the lay-down api
                    payload = {
                        "game_id": str(self.game_id),
                        "event": self.events[current_player]
                    }
                    self.events[current_player] = ""
                    result = self.call_api("lay-down/", current_player, payload)
                    if "play" in result:
                        play_string = result["play"]
                        ps_words = play_string.split(" ")
                        while (len(ps_words)>0):
                            if ps_words[0]=="meld":
                                logging.info("Player is melding, "+play_string)
                            elif ps_words[0]=="layoff":
                                logging.info("Player is laying off, " + play_string)
                            elif ps_words[0]=="discard":
                                if ps_words[1] in self.hands[current_player]:
                                    self.hands[current_player].remove(ps_words[1])
                                    self.discard_pile.insert(0,Card(ps_words[1]))
                                    for i in range(len(self.players)):
                                        self.events[i] += self.players[current_player].name + " discards " + ps_words[1] + "\n"
                                    # Take the first two elements off ps_words
                                    ps_words.pop(0)
                                    ps_words.pop(0)
                                else:
                                    self.forfeit(current_player, "Player discarded invalid card")
                                    continue
                    elif "status" in result:
                        if result["status"] == "error":
                            self.forfeit(current_player, "API error")
                            continue
                        elif result["status"] == "timeout":
                            self.forfeit(current_player, "API timeout")
                            continue

                # start over with first player
                self.player_turn = 0
                self.player_phase = 0
        logging.info("Finished with game run for "+str(self.game_id))
        if self.test_game:
            for i in range(len(self.players)):
                if self.players[i].name != "TestDummy1": self.call_shutdown(i)
            time.sleep(5)

        for player in self.players:
            player.set_playing(False)

        return results



