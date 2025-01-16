from time import sleep

import uvicorn
from fastapi import FastAPI, Path, BackgroundTasks
from pydantic import BaseModel
from threading import Lock
from game import Game
import random

from player import Player

"""
By Todd Dole, Revision 1.0
Written for Hardin-Simmons CSCI-4332 Artificial Intelligence
"""

app = FastAPI()

class ThreadSafeDataStore:
    def __init__(self):
        self._lock = Lock()
        self.players = []
        self.games = []

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


store = ThreadSafeDataStore()




@app.get("/")
async def root():
    return {"Hello": "World"}

class RegisterInfo(BaseModel):
    name: str
    address: str
    port: str
@app.post("/register")
async def register(register_info: RegisterInfo):
    new_player = Player(name=register_info.name, address=register_info.address, port=register_info.port)
    store.add_player(new_player)
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
        return{"Game Status":"Started "+ str(game.game_id)+": "+game_players[0].name + " vs " + game_players[1].name}

def play_game(game):
    print("Playing game "+str(game.game_id))
    sleep(60)
    print("Done playing game "+str(game.game_id))
    for player in game.players:
        player.set_playing(False)

if __name__ == "__main__":
    port = 16200  # Set your desired port number here
    uvicorn.run(app, host="127.0.0.1", port=port)
