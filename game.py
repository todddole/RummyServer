from deck import Card, Deck
import requests
import logging
import time
import datetime

"""
By Todd Dole, Revision 1.1
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
        self.meld_list = []
        self.api_calls = 0

    def call_shutdown(self, player_num):
        url = "http://127.0.0.1:" + self.players[player_num].port + "/shutdown"
        try:
            response = requests.get(url)
            if response.status_code != 200:
                logging.error("Game " + str(self.game_id) + " shutdown Failed, status code "+str(response.status_code) + ", URL: "+url)
        except Exception as e:
            logging.warning("Error shutting down "+url)




    def call_api(self, endpoint, player_num, payload):
        self.api_calls += 1
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
            logging.info("Game " + str(self.game_id) + " API Call Successful: "+url+", response = "+response.text)
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
        logging.info("Shuffling discard pile")
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

    def is_set(self, cards):
        """Returns True if a list of cards is a valid set, otherwise False"""
        try:
            value = cards[0].value
            for card in cards:
                if card.value != value:
                    return False
            return True
        except Exception as e:
            return False

    def run(self):
        start_time = time.time()
        results = ""
        self.game_status = "running"
        self.scores = [0] * len(self.players)
        start_player = 0
        self.hand_number = 0

        while (self.game_status == "running"):
            self.hand_status = "running"
            self.hand_number += 1
            logging.info("*** Starting Hand Number "+str(self.hand_number))

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
                self.discard_pile = []
                self.meld_list = []

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

                            result = self.call_api("start-" + str(len(self.players)) + "p-" + ("game/" if sum(self.scores)==0 else "hand/"), j, payload)
                            # If the result is invalid, forfeit
                            if "status" in result:
                                if result["status"] == "error":
                                    self.forfeit(j, "API error")
                                    if self.players_left <= 1:
                                        self.hand_status = "done"
                                        current_player = 0
                                elif result["status"] == "timeout":
                                    self.forfeit(j, "API timeout")
                                    if self.players_left <= 1:
                                        self.hand_status = "done"
                                        current_player = 0

                # put a card on discard
                card = self.deck.deal()
                self.discard_pile.insert(0, card)
                for i in range(len(self.players)):
                    self.events[i] += "Dealer discards " + str(card) + "\n"


                while (self.hand_status=="running"):
                    # Cycle through each player's turn
                    current_player = (player_turn + start_player) % len(self.players)
                    player_turn+=1
                    logging.info("*** Starting turn for " + self.players[current_player].name + ", turn "+str(player_turn))

                    if self.scores[current_player]>=1000:
                        logging.info("Skipping, player disqualified.\n")
                        continue # player disqualified, skip

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
                                logging.info(self.players[current_player].name + " drew from discard: "+str(card))
                                discard_draw = str(card)
                        elif ("draw stock") in play_string:
                            card = self.deck.deal()
                            draw_string = self.players[current_player].name + " draws " + str(card) + "\n"
                            for i in range(len(self.players)):
                                if i==current_player:
                                    self.events[i] += draw_string
                                else:
                                    self.events[i] += self.players[current_player].name + " draws\n"

                            self.hands[current_player].append(card)
                            logging.info(self.players[current_player].name + " drew from stock: "+str(card))
                            discard_draw = ""
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
                                new_meld = []
                                ps_words.pop(0)
                                done = False
                                while not done:
                                    if len(ps_words)==0:
                                        self.forfeit(current_player, "Invalid Meld String")
                                        ps_words=[""]
                                        break
                                    card_txt = ps_words.pop(0)
                                    for card in self.hands[current_player]:
                                        if card_txt == str(card):
                                            self.hands[current_player].remove(card)
                                            new_meld.append(card)
                                            card_txt = ""
                                            break

                                    if card_txt!="":
                                        self.forfeit(current_player, "Tried to meld "+card_txt+ " but it's not in their hand.")
                                        ps_words = [""]
                                        break

                                    if (len(ps_words)>0 and len(ps_words[0])>2) or (len(ps_words)==0):
                                        # meld is done
                                        done = True
                                        if len(new_meld)<3:
                                            self.forfeit(current_player, "Tried to meld " + str(new_meld))
                                            ps_words = [""]
                                            break

                                if len(ps_words)>0 and ps_words[0]=="": break

                                # Meld is complete, let's make sure the meld is valid
                                new_meld.sort()
                                if new_meld[0].value=="A" and new_meld[-1].value=="K":
                                    # We have a run that includes a king and an ace.  Move the ace to after king.
                                    new_meld.append(new_meld.pop(0))

                                is_set = True
                                is_run = True

                                set_val = str(new_meld[0])[0]
                                run_suit = str(new_meld[0])[1]
                                last_cv = 0
                                for card in new_meld:
                                    if (last_cv!=0):
                                        if (card.get_cv() - last_cv) - 1 not in [0, -13]:  # Check if it is one higher than previous card.  King to Ace will give -13
                                            is_run = False #
                                    card_text = str(card)
                                    if card_text[0]!=set_val: is_set = False
                                    if card_text[1]!=run_suit: is_run = False

                                if (not is_set and not is_run) or (is_set and is_run):
                                    self.forfeit(current_player, "Invalid meld: " + str(new_meld))
                                    ps_words = [""]
                                    break

                                # meld is valid, let's finish processing it
                                self.meld_list.append(new_meld)
                                event_txt = self.players[current_player].name + " plays meld("+str(len(self.meld_list)-1) + "): "
                                for card in new_meld:
                                    event_txt += str(card) + " "
                                event_txt = event_txt[:-1] + "\n"
                                for i in range(len(self.players)):
                                    self.events[i]+= event_txt

                            elif ps_words[0]=="layoff":
                                logging.info("Player is laying off, " + play_string)
                                # Let's make sure they have the card
                                ps_words.pop(0)

                                try:
                                    meld_stack = ps_words.pop(0)[5:-1]
                                    card_text = ps_words.pop(0)
                                except IndexError:
                                    meld_stack = ""
                                    card_text = ""
                                has_card = False
                                for card in self.hands[current_player]:
                                    if card_text == str(card):
                                        has_card = True
                                        break

                                if has_card == False:
                                    self.forfeit(current_player, "Tried to lay off " + "invalid card" if card_text=="" else card_text+", not in hand")
                                    ps_words = [""]
                                    continue

                                # Check that meld_stack is valid
                                try:
                                    meld_stack = int(meld_stack)
                                except ValueError:
                                    self.forfeit(current_player,"Badly formed meld stack:  " + meld_stack)
                                    ps_words = [""]
                                    continue

                                if meld_stack <0 or meld_stack > len(self.meld_list)-1:
                                    self.forfeit(current_player, "Player tried to add to a non-existent meld pile:  " + meld_stack)
                                    ps_words = [""]
                                    continue

                                # check that the card is a valid addition to the meld stack
                                valid_meld = False
                                if is_set(self.meld_list[meld_stack]):
                                    # We are adding to a set, make sure it is valid and process it
                                    if card.value == self.meld_list[meld_stack][0].value:
                                        valid_meld = True
                                        self.hands[current_player].remove(card)
                                        self.meld_list[meld_stack].append(card)
                                    else:
                                        self.forfeit(current_player,"Player tried to layoff" + str(card) + "on meld(" +
                                                     str(meld_stack)+ ") " + str(self.meld_list[meld_stack]))
                                        ps_words = [""]
                                        continue
                                else:
                                    # We are adding to a run, make sure it is valid and process it
                                    # First, make sure it is the correct suit
                                    if self.meld_list[meld_stack][0].suit != card.suit:
                                        self.forfeit(current_player, "Player tried to layoff" + str(card) + "on meld(" +
                                                     str(meld_stack) + ") " + str(self.meld_list[meld_stack]))
                                        ps_words = [""]
                                        continue

                                    # Now make sure it is a valid value and add it if so
                                    if self.meld_list[meld_stack][0].get_cv() - card.get_cv() == 1:
                                        # We are inserting at the start of the run
                                        self.hands[current_player].remove(card)
                                        self.meld_list[meld_stack].insert(0,card)
                                    elif card.get_cv() - self.meld_list[meld_stack][-1].get_cv() in [1,-12]:
                                        # We are adding it at the end of the run
                                        self.hands[current_player].remove(card)
                                        self.meld_list[meld_stack].append(card)
                                    else:
                                        self.forfeit(current_player, "Player tried to layoff" + str(card) + "on meld(" +
                                                     str(meld_stack) + ") " + str(self.meld_list[meld_stack]))
                                        ps_words = [""]
                                        continue

                                # IF we made it this far, it was a valid layoff.  Report to the players
                                for i in range(len(self.players)):
                                    self.events[i]+=self.players[current_player].name + " laysoff meld("+str(meld_stack)+ "): "+str(card)+"\n"


                            elif ps_words[0]=="discard":
                                has_card = None
                                for card in self.hands[current_player]:
                                    if str(card)==ps_words[1]:
                                        has_card = card
                                        break

                                if has_card is not None:
                                    # Make sure they didn't discard what was just picked up from discard
                                    if discard_draw is not None and discard_draw==ps_words[1]:
                                        self.forfeit(current_player, "Player discarded "+ps_words[1]+", which they just picked up from discard pile.")
                                        logging.error("Player discarded the card they just picked up from discard: " + ps_words[1] + ", hand is " + str(
                                            self.hands[current_player]))
                                        break
                                    self.hands[current_player].remove(card)
                                    self.discard_pile.insert(0,card)
                                    for i in range(len(self.players)):
                                        self.events[i] += self.players[current_player].name + " discards " + ps_words[1] + "\n"
                                        if i==current_player:
                                            logging.info(self.players[current_player].name + " discards " + ps_words[1])
                                    # Take the first two elements off ps_words
                                    ps_words.pop(0)
                                    ps_words.pop(0)
                                else:
                                    self.forfeit(current_player, "Player discarded invalid card")
                                    logging.error("Player discarded "+ps_words[1]+", hand is "+str(self.hands[current_player]))
                                    # bug fix 2/7 to break out of endless loop
                                    ps_words = [""]
                                    continue
                            else:
                                self.forfeit(current_player, "Player responded with malformed play text")
                                logging.error("Player responded with: " + str(ps_words))
                                # bug fix 2/7 to break out of endless loop
                                ps_words = [""]
                                continue
                            if len(ps_words)>=1 and ps_words[0]=="":   #Player already forfeited, break out of loop
                                ps_words.pop(0)

                    elif "status" in result:
                        if result["status"] == "error":
                            self.forfeit(current_player, "API error")
                            continue
                        elif result["status"] == "timeout":
                            self.forfeit(current_player, "API timeout")
                            continue

                    if len(self.hands[current_player]) == 0 or (self.scores[current_player]<1000 and self.scores[current_player]>=500) or player_turn>999:
                        self.hand_status = "done"
                        for i in range(len(self.players)):
                            for card in self.hands[i]:
                                self.scores[i] += card.get_score()

                    logging.info("Finished turn for "+self.players[current_player].name+", hand is: "+str(sorted(self.hands[current_player])))

                # Hand is finished
                logging.info("Finished player hand, winner = "+self.players[current_player].name)
                logging.info("Scores = "+str(self.scores))
                for i in range(len(self.players)):
                    self.events[i] += "Hand Ends: " + self.players[0].name + " " + str(self.scores[0]) + \
                             " " + self.players[1].name + " " + str(self.scores[1]) + "\n"

                # Check if game is done
                still_in = 0
                for score in self.scores:
                    if score>=500 and score < 1000: self.game_status = "finished" # game is over if a non-forfeit player is over 500
                    elif score<500: still_in += 1

                if still_in <=1: self.game_status = "finished"  # game is also over if only one (or less) player is still in (<500 points)

                if self.game_status == "running":
                    self.update_players()
                    continue # game still going, skip the game wrap up code

                # game is finished, record results
                if self.scores[current_player] == min(self.scores):
                    winner = current_player
                else:
                    win_score = min(self.scores)
                    for i in range(len(self.players)):
                        if self.scores[i]==win_score:
                            winner=i

                    for i in range(len(self.players)):
                        if i==winner:
                            self.players[i].add_record(win=True)
                        else:
                            self.players[i].add_record(win=False)

                for i in range(len(self.players)):
                    self.events[i] += "Game Ends: " + self.players[0].name + " " + str(self.scores[0])
                    self.events[i] += " * " if winner==0 else " "
                    self.events[i] += self.players[1].name + " " + str(self.scores[1])
                    self.events[i] += " *\n" if winner == 1 else "\n"

                self.update_players()

                with open("RummyResults.csv", "a") as file:
                    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    try:
                        file.write(current_time + "," + str(self.test_game) + ",2," +
                            self.players[0].name+","+self.players[1].name + ",," +
                            "," + str(self.scores[0]) + "," + str(self.scores[1]) + ",,," + str(winner) +
                            "," + str(self.hand_number) + "," + str(self.api_calls) + "," +
                                   str(int(time.time() - start_time)) + "\n")
                    except IOError:
                        logging.error("Error writing to file with game results.")



        logging.info("Finished with game run for "+str(self.game_id))
        if self.test_game:
            for i in range(len(self.players)):
                if self.players[i].name != "TestDummy1": self.call_shutdown(i)
            time.sleep(5)

        for player in self.players:
            player.set_playing(False)

        return results



