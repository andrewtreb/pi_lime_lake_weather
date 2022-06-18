import pymongo
from bson.objectid import ObjectId
import os
import pandas

class database:
    def __init__(self):
        mongoKey = os.getenv('MONGOKEY')
        mongoString = 'mongodb+srv://website_service:{}' \
            '@limelakeanalytics.eclfe.mongodb.net/' \
            'myFirstDatabase?retryWrites=true&w=majority' \
            .format(mongoKey)
        print(mongoString)
        self.client = pymongo.MongoClient(mongoString,connectTimeoutMS=40000)

        self.db = self.client.limeLakeAnalytics
        self.weatherData = self.db.weatherData


    def get_weatherData(self):
        return self.weatherData.find()

    def insert_weatherData(self,data):
        insertList = data.to_dict(orient='records')
        self.weatherData.insert_many(insertList)

