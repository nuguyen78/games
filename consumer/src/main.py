import pymongo
import pika
from dotenv import load_dotenv
from fastapi import FastAPI

app = FastAPI()

load_dotenv()

# Constants
MONGODB_URL = "mongodb+srv://admin:admin@wab.d99xhsu.mongodb.net/?retryWrites=true&w=majority"
RABBITMQ_URL = "amqp://guest:guest@rabbitmq:5672"


client = pymongo.MongoClient(MONGODB_URL)
db = client.get_database('wab')
collection = db.get_collection('rabbit')

#Pripojeni k rabbitmq
params = pika.URLParameters(RABBITMQ_URL)
connection = pika.BlockingConnection(params)
channel = connection.channel()
channel.queue_declare(queue="game", durable=True)

def on_message_callback(channel, method, properties, body):
    collection.insert_one({
        'msg': body.decode("utf-8")
    })
    
channel.basic_consume(queue="game",
                      auto_ack=True,
                      on_message_callback=on_message_callback)
channel.start_consuming()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8002)