# Fast API application for darts scoring app
import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uuid
import uvicorn
import json

# ponyorm for database
from pony.orm import Database, Required, Optional, PrimaryKey, Set, db_session, commit

db = Database()


class Player(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Optional(str)
    score = Required(int, default=0)
    darts = Optional(int, default=0)
    turn = Required(bool, default=False)
    games_played = Set('Game', reverse='players')
    games_won = Set('Game', reverse='winner')
    darts_thrown = Set('Dart', reverse='player')
    games_created = Set('Game', reverse='creator')


class Game(db.Entity):
    id = PrimaryKey(int, auto=True)
    creator = Required(Player, reverse='games_created')
    players = Set(Player, reverse='games_played')
    winner = Optional(Player, reverse='games_won')
    scored = Required(bool, default=False)
    date = Required(datetime.datetime, default=datetime.datetime.now)
    darts = Set('Dart', reverse='game')
    legs = Set('Leg', reverse='game')
    open_to_join = Required(bool, default=True)


class Leg(db.Entity):
    id = PrimaryKey(int, auto=True)
    game = Required(Game)
    darts = Set('Dart', reverse='leg')


class Dart(db.Entity):
    id = PrimaryKey(int, auto=True)
    player = Required(Player)
    game = Required(Game)
    score = Required(int)
    multiplier = Required(int)
    date = Required(datetime.datetime, default=datetime.datetime.now)
    leg = Required(Leg)


db.bind(provider='sqlite', filename='db.sqlite', create_db=True)
db.generate_mapping(create_tables=True)


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


# Game Endpoints for game creation and joining

# Create a Game
@app.post("/game")
@db_session
def create_game(request: dict):
    creator = Player.get(id=request['player']['id'])
    game = Game(scored=request['scored'], creator=creator)
    game.players.add(creator)
    commit()
    return game.to_dict()


# Get a Game
@app.get("/game/{game_id}")
@db_session
def get_game(game_id: str):
    return Game[game_id].to_dict()

# Join a Game
@app.post("/game/join")
@db_session
def join_game(request: dict):
    game = Game[request['game_id']]
    player = Player.get(id=request['player']['id'])
    game.players.add(player)
    commit()
    return game.to_dict()

# start a game
@app.post("/game/start")
@db_session
def start_game(request: dict):
    game = Game[request['game']['id']]
    if game.creator.id == request['requestor']['id']:
        game.open_to_join = False
        commit()
    return game.to_dict()


# get all the players in a game by game id
@app.get("/game/{game_id}/players")
@db_session
def get_players(game_id: str):  
    return [Player[player.id].to_dict() for player in Game[game_id].players] 



# Update a Game
@app.put("/game/{game_id}")
@db_session
def update_game(game_id: str, request: dict):
    game = Game[game_id]
    game.set(**request)
    return game.to_dict()


# Create a leg
@app.post("/leg")
@db_session
def create_leg(request: dict):
    leg = Leg(game=Game[request['game_id']])
    leg_id = leg.id
    return Leg[leg_id].to_dict()


# Get a leg
@app.get("/leg/{leg_id}")
@db_session
def get_leg(leg_id: str):
    return Leg[leg_id].to_dict()


# Update a leg
@app.put("/leg/{leg_id}")
@db_session
def update_leg(leg_id: str, request: dict):
    leg = Leg[leg_id]
    leg.set(**request)
    return leg.to_dict()


# Create a dart
@app.post("/dart")
@db_session
def create_dart(request: dict):
    dart = Dart(player=Player[request['player_id']], game=Game[request['game_id']], score=request['score'],
                multiplier=request['multiplier'])
    dart_id = dart.id
    return Dart[dart_id].to_dict()


# Get a dart
@app.get("/dart/{dart_id}")
@db_session
def get_dart(dart_id: str):
    return Dart[dart_id].to_dict()


# Update a dart
@app.put("/dart/{dart_id}")
@db_session
def update_dart(dart_id: str, request: dict):
    dart = Dart[dart_id]
    dart.set(**request)
    return dart.to_dict()


# Delete a dart
@app.delete("/dart/{dart_id}")
@db_session
def delete_dart(dart_id: str):
    dart = Dart[dart_id]
    dart.delete()
    return {"status": f"{dart_id} deleted"}


# Create a player - #DONE
@app.post("/player")
@db_session
def create_player(request: dict):
    player = Player(name=request['player']['name'])
    commit()
    return {'id': player.id, 'name': player.name}


# Get a player
@app.get("/player/{player_id}")
@db_session
def get_player(player_id: str):
    return Player[player_id].to_dict()


# Update a player
@app.put("/player/{player_id}")
@db_session
def update_player(player_id: str, request: dict):
    player = Player[player_id]
    player.set(**request)
    return player.to_dict()


# ANALYTICS API

# Get all games
@app.get("/games")
@db_session
def get_games():
    games = Game.select()
    return [game.to_dict() for game in games]


# Get all players
@app.get("/players")
@db_session
def get_players():
    players = Player.select()
    return [player.to_dict() for player in players]


# Get all darts
@app.get("/darts")
@db_session
def get_darts():
    darts = Dart.select()
    return [dart.to_dict() for dart in darts]


# Get all legs
@app.get("/legs")
@db_session
def get_legs():
    legs = Leg.select()
    return [leg.to_dict() for leg in legs]


# Get all players in a game
@app.get("/game/{game_id}/players")
@db_session
def get_players_in_game(game_id: str):
    players = Game[game_id].players
    return [player.to_dict() for player in players]


# UI/UX API

# Get all darts by game
@app.get("/dart/{game_id}")
@db_session
def get_darts(game_id: int):
    darts = [dart.to_dict() for dart in Dart.select(lambda d: d.game.id == game_id)]
    return darts


# Get all darts by player
@app.get("/dart/{player_id}")
@db_session
def get_darts(player_id: int):
    darts = [dart.to_dict() for dart in Dart.select(lambda d: d.player.id == player_id)]
    return darts


# Get all darts by player and game
@app.get("/dart/{player_id}/{game_id}")
@db_session
def get_darts(player_id: int, game_id: int):
    darts = [dart.to_dict() for dart in Dart.select(lambda d: d.player.id == player_id and d.game.id == game_id)]
    return darts


# Start a Game

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
