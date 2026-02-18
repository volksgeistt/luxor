import os
from motor.motor_asyncio import AsyncIOMotorClient

mongo_uri = "mongodb+srv://volksgeistt:Xlwkwf7GshcBoFjK1337@spreadbot.y0dyfkp.mongodb.net/"
mongo_client = AsyncIOMotorClient(mongo_uri)
db = mongo_client['Luxor']