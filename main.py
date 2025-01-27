from time import sleep

import uvicorn
from fastapi import FastAPI, Path, BackgroundTasks
from pydantic import BaseModel
from threading import Lock
from game import Game
import random
import logging
import threading
import time
import requests


from player import Player

"""
By Todd Dole, Revision 0.9
Written for Hardin-Simmons CSCI-4332 Artificial Intelligence
Revision History:
0.7 Basic Implementation of API structure
0.8 added start of gameplay, discard handling
0.9 added automatic game start thread, meld handling, game results
0.95 finished meld handling, corrected error handling on failed api calls at start of game that resulted in hung game
"""

VERSION = "0.95"

app = FastAPI()

class ThreadSafeDataStore:
    def __init__(self):
        self._lock = Lock()
        self.players = []
        self.games = []
        self.test_queue = []
        self.test_player = None
        self.start_new_games = True
        self.start_test_games = True

    def add_player(self, player):
        with self._lock:
            self.players.append(player)

    def get_players(self):
        with self._lock:
            return self.players

    def get_free_players(self):
        with self._lock:
            free_players = []
            for player in self.players:
                if player.is_playing() == False:
                    free_players.append(player)
            return free_players

    def add_to_test_queue(self, player):
        with self._lock:
            self.test_queue.append(player)

    def pop_from_test_queue(self):
        with self._lock:
            return self.test_queue.pop(0)

    def get_test_queue_len(self):
        with self._lock:
            return len(self.test_queue)

    def set_test_player(self, player):
        with self._lock:
            self.test_player = player

    def is_test_player_free(self):
        with self._lock:
            if self.test_player is None:
                return False
            if self.test_player.is_playing() == False:
                return True
            return False

    def get_test_player(self):
        with self._lock:
            return self.test_player



store = ThreadSafeDataStore()

@app.get("/")
async def root():
    logging.info("Get /")
    return {"Hello": "World"}

class RegisterInfo(BaseModel):
    name: str
    address: str
    port: str
@app.post("/register")
async def register(register_info: RegisterInfo):
    new_player = Player(name=register_info.name, address=register_info.address, port=register_info.port)
    store.add_player(new_player)
    logging.info("Registered "+register_info.name)
    return {"Registered" : register_info.name }

@app.get("/play-2p/")
async def play(background_tasks: BackgroundTasks):
    players = store.get_free_players()
    if len(players) == 0:
        return {"Game Status":"No Free Players Found"}
    elif len(players) == 1:
        return {"Game Status":"Only One Free Player Found"}
    else:
        game_players = random.sample(players,2)
        game = Game(game_players)
        for player in game_players:
            player.set_playing(True)
        background_tasks.add_task(play_game, game)
        logging.info("Game Status: Started "+ str(game.game_id)+": "+game_players[0].name + " vs " + game_players[1].name)
        return{"Game Status":"Started "+ str(game.game_id)+": "+game_players[0].name + " vs " + game_players[1].name}

@app.get("/play-test/")
async def play_test(background_tasks: BackgroundTasks):
    if store.is_test_player_free() == False:
        logging.error("play-test called but test player is not free")
        return {"Game Status":"Test Player is not free"}
    player = store.pop_from_test_queue()
    if player is None:
        logging.error("play-test called but no player found in queue")
        return {"Game Status":"No Player In Test Queue Found"}
    else:
        game_players = [store.get_test_player(), player]
        random.shuffle(game_players)

        game = Game(game_players, test=True)
        for player in game_players:
            player.set_playing(True)
        background_tasks.add_task(play_game, game)
        logging.info("Game Status: Started Test Game "+ str(game.game_id)+": "+game_players[0].name + " vs " + game_players[1].name)
        return{"Game Status":"Started Test Game "+ str(game.game_id)+": "+game_players[0].name + " vs " + game_players[1].name}


def play_game(game):
    print("Playing game "+str(game.game_id))
    results = game.run()
    print("Done playing game "+str(game.game_id))
    for player in game.players:
        player.set_playing(False)

@app.post("/test")
async def register(register_info: RegisterInfo):
    new_player = Player(name=register_info.name, address=register_info.address, port=register_info.port)
    if new_player.name == "TestDummy1":
        store.test_player = new_player
        logging.info("Added Test Player: "+register_info.name)
        return {"TestPlayer" : register_info.name }
    else:
        store.add_to_test_queue(new_player)
        logging.info("Added to Test Queue: "+register_info.name)
        return {"Registered" : register_info.name }


def game_launcher():
    time.sleep(20)
    while store.start_new_games == True or store.start_test_games == True:
        if store.start_new_games == True and len(store.get_free_players())>1:
            logging.info("Starting a real game...")
            url = "http://127.0.0.1:16200/play-2p/"
            try:
                # Call the URL to register client with the game server
                response = requests.get(url)
            except Exception as e:
                logging.error("Failed to connect to "+url)
                sleep(10)
            finally:
                sleep(2)
        if store.start_test_games == True and store.get_test_queue_len()>=1 and store.is_test_player_free() == True:
            logging.info("Starting a test game...")
            url = "http://127.0.0.1:16200/play-test/"
            try:
                # Call the URL to register client with the game server
                response = requests.get(url)
            except Exception as e:
                logging.error("Failed to connect to "+url)
                sleep(10)
            finally:
                sleep(2)
        sleep(2)


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', filename='RummyServer.log', level=logging.INFO)
    logging.info("Starting server, version "+VERSION)
    x = threading.Thread(target=game_launcher)
    x.start()
    port = 16200  # Set your desired port number here
    uvicorn.run(app, host="127.0.0.1", port=port)

