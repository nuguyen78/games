from fastapi import FastAPI
from typing import List
from pymongo.mongo_client import MongoClient
from .schema import Game
import pika
import os
from bson import ObjectId

app = FastAPI()

# Mongo client init
uri = "mongodb+srv://admin:admin@wab.d99xhsu.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri)
db = client.get_database("wab")
game_collection = db.get_collection('games')

#Osetreni zda jsme pripojeni
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

#Funkce pro odeslani zpravy do fronty rabbitmq
def send_message(message):
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    params=pika.URLParameters(rabbitmq_url)
    connection=pika.BlockingConnection(params)
    channel=connection.channel()

    channel.queue_declare(queue="game", durable=True)

    channel.basic_publish(exchange="", routing_key="game", body=message)

    connection.close()


#Endpointy
@app.get("/games/", response_model=list[Game])
async def get_all_games():
    result = list(db.games.find())
    return result

@app.post('/newGame', response_model=Game, status_code=201)
def add_film(game:Game):
    game_dict = game.dict(by_alias=True)
    inserted_game = game_collection.insert_one(game_dict)
    game_message=Game(**game_dict, id=inserted_game.inserted_id)

    # Send message to rabbitmq
    send_message(f"New game added: {game_message}")

    return game_message

# Endpoint to update a game
@app.put('/games/{_id}', response_model=Game)
async def update_game_endpoint(_id: str, updated_game: Game):
    obj_id = ObjectId(_id)
    existing_game = game_collection.find_one({"_id": obj_id})

    if existing_game:
        # Update the existing game with the data from the request
        updated_data = updated_game.dict(exclude_unset=True, by_alias=True)
        updated_data["_id"] = obj_id  # Add the game_id to the updated_data

        result = game_collection.update_one({"_id": obj_id}, {"$set": updated_data})

        if result.modified_count > 0:
            # Fetch the updated game from the database
            updated_game = game_collection.find_one({"_id": obj_id})
            send_message(f"Game updated: {updated_data}")
            return updated_game
        else:
            raise Exception(status_code=500, detail="Failed to update the game")

    raise Exception(status_code=404, detail="Game not found")

@app.delete('/games/{_id}', response_model=dict)
def delete_film(_id: str):
    obj_id = ObjectId(_id)
    deleted_game = game_collection.find_one({"_id": obj_id})
    if(game_collection.delete_one({"_id": obj_id})):
        send_message(f"Game deleted: {deleted_game}")
        return {"message": "Game deleted"}
    else:
        raise Exception(status_code=404, detail="Failed to delete game")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8001)
