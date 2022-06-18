from gpiozero import Button
from sensorCentral import *
from mongoConnect import database
import datetime
import json
import pandas as pd
import pathlib



sensors = sensorCentral()
pd.set_option('display.max_columns', None)
collection = database()
finalData = pd.DataFrame()


while True:
    data = sensors.get_data(300)

    data_pd = pd.DataFrame([data])

    data_pd.columns = ['Wind Count','Wind Speed (MPH)','Wind Direction','Temperature','Pressure','Humidity','Rainfall']

    data_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    data_pd['data_time'] = data_time

    #filename = "./data/weather_{}.csv".format(datetime.datetime.now().strftime("%Y_%m_%d"))

    #file_test = pathlib.Path(filename)
    #file_test.touch(exist_ok=True)

    collection.insert_weatherData(data_pd)
    #data_pd.to_csv(filename, mode = 'a',header=False,index=False)