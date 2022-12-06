# Fast API application for darts scoring app
import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uuid
import uvicorn
import json

# ponyorm for database
from pony.orm import Database, Required, Optional, PrimaryKey, Set, db_session

db = Database()


class Player(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    score = Required(int, default=501)
    darts = Optional(int, default=0)
    turn = Required(bool, default=False)
    games_played = Set('Game', reverse='players')
    games_won = Set('Game', reverse='winner')
    darts_thrown = Set('Dart', reverse='player')


class Game(db.Entity):
    id = PrimaryKey(int, auto=True)
    players = Set(Player)
    winner = Optional(Player)
    format = Required(str)
    date = Required(datetime.datetime, default=datetime.datetime.now)
    darts = Set('Dart', reverse='game')


class Dart(db.Entity):
    id = PrimaryKey(int, auto=True)
    player = Required(Player)
    game = Required(Game)
    score = Required(int)
    multiplier = Required(int)
    date = Required(datetime.datetime, default=datetime.datetime.now)


db.bind(provider='sqlite', filename='database.sqlite', create_db=True)

try:
    db.generate_mapping(create_tables=True)
except:
    db.generate_mapping(create_tables=False)

app = FastAPI()

origins = [
    "*"
    ]

app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_origins=origins,
        )


# Endpoints

# @app.get("/")
# def read_root():
#     some_int = 5
#     return {"Hello": some_int}
#
# Create a Player
@app.post("/player")
@db_session
def create_player(request: dict):
    player = Player(name=request['name'])
    return player.to_dict()


# Get all players
@app.get("/players")
@db_session
def get_players():
    players = [player.to_dict() for player in Player.select()]
    return players


# Create a Game
@app.post("/game")
@db_session
def create_game(request: dict):
    game = Game(format=request['format'])
    for player in request['players']:
        game.players.add(Player[player])
    game_id = game.id
    return Game[game_id].to_dict()


# Throw a dart
@app.post("/dart")
@db_session
def throw_dart(request: dict):
    dart = Dart(player=Player[request['player_id']], game=Game[request['game_id']], score=request['score'],
                multiplier=request['multiplier'])
    return dart.to_dict()


# Get all darts by game
@app.get("/dart/{game_id}")
@db_session
def get_darts(game_id: int):
    darts = [dart.to_dict() for dart in Dart.select(lambda d: d.game.id == game_id)]
    return darts


# Start a Game

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
