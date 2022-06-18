from gpiozero import MCP3008, Button
import numpy as np
import math
import bme280
import smbus2
import time
from datetime import datetime, timedelta
from statistics import mean
import yaml

def get_config():
    with open("config/config.yml", "r") as ymlfile:
        cfg = yaml.safe_load(ymlfile)
    return cfg

class windVane:
    angles = {0.4: 0.0,
            1.4: 22.5,
            1.2:45.0,
            2.8: 67.5,
            2.7: 90.0,
            2.9: 112.5,
            2.2: 135.0,
            2.5: 157.5,
            1.8: 180.0,
            2.0: 202.5,
            0.7: 225.0,
            0.8: 247.5,
            0.1: 270.0,
            0.3: 292.5,
            0.2: 315.0,
            0.6: 337.5}

    angleDir = [[348.75, 11.25, 'N'],
            [11.25, 33.75, 'NNE'],
            [33.75, 56.25, 'NE'],
            [56.25, 78.75, 'ENE'],
            [78.75, 101.25, 'E'],
            [101.25, 123.75, 'ESE'],
            [123.75, 146.25, 'SE'],
            [146.25, 168.75, 'SSE'],
            [168.75, 191.25, 'S'],
            [191.25, 213.75, 'SSW'],
            [213.75, 236.25, 'SW'],
            [236.25, 258.75, 'WSW'],
            [258.75, 281.25, 'W'],
            [281.25, 303.75, 'WNW'],
            [303.75, 326.25, 'NW'],
            [326.25, 348.75, 'NNW']]

    def __init__(self):
        self.channel = get_config()["sensors"]["windVane"]["channel"]
        self.adc = MCP3008(channel=self.channel)

    def get_voltage(self):
        value = round(self.adc.value*3.3,1)
        return value

    def get_angle(self):
        given_value = self.get_voltage()

        temp = self.angles.keys()

        absolute_difference_function = lambda list_value : abs(list_value - given_value)

        closest_value = min(temp, key=absolute_difference_function)

        angle = self.angles[closest_value]
        return angle

    #This funtion is supplied to take a list of angles and return an average angle for the list
    def get_average(self,angles):
        sin_sum = 0.0
        cos_sum = 0.0

        for angle in angles:
            r = math.radians(angle)
            sin_sum += math.sin(r)
            cos_sum += math.cos(r)

        flen = float(len(angles))
        s = sin_sum / flen
        c = cos_sum / flen
        arc = math.degrees(math.atan(s / c))
        average = 0.0

        if s > 0 and c > 0:
            average = arc
        elif c < 0:
            average = arc + 180
        elif s < 0 and c > 0:
            average = arc + 360

        return 0.0 if average == 360 else average

    def get_direction(self,angle):
        angleDir = self.angleDir
        for i in range(len(angleDir)):
            if angleDir[i][0] > angleDir[i][1] and (angle > angleDir[i][0] or angle < angleDir[i][1]):    
                return angleDir[i][2]
            elif (angle < angleDir[i][0] and angle < angleDir[i][1]):
                return angleDir[i][2]

    def close_sensor(self):
        self.adc.close()
        

class bme:
    def __init__(self):
        address = get_config()["sensors"]["bme"]["address"]
        bus = smbus2.SMBus(get_config()["sensors"]["bme"]["port"])

        bme280.load_calibration_params(bus,address)
        self.bme_data = bme280.sample(bus,address)

    def get_temp(self):
        temp_factor = (9/5.0)
        return ((self.bme_data.temperature * temp_factor) + 32)

    def get_pressure(self):
        return self.bme_data.pressure

    def get_humidity(self):
        return self.bme_data.humidity


class rainBucket:

    def __init__(self):
        self.rain_per_tip = get_config()["sensors"]["rainBucket"]["rain_per_trip"]
        self.count = 0
        button = get_config()["sensors"]["rainBucket"]["button"]
        self.rain_sensor = Button(button)
        self.rain_sensor.when_pressed = self.bucket_tipped 

    def bucket_tipped(self):
        self.count += 1

    def reset_rainfall(self):
        self.count = 0

    def get_rain_count(self):
        return self.count

    def calculate_rain(self,count):
        return float(count) * self.rain_per_tip

    def close_sensor(self):
        self.rain_sensor.close()



class windSpeed:
    def __init__(self):
        button = get_config()["sensors"]["windSpeed"]["button"]
        self.radius_in = get_config()["sensors"]["windSpeed"]["radius_in"]
        self.windcount = 0
        self.wind_speed_sensor = Button(5,bounce_time=0.025)
        self.wind_speed_sensor.hold_time = 2
        self.wind_speed_sensor.when_pressed = self.spin

    def spin(self):
        self.windcount += 1

    def reset_wind(self):
        self.windcount = 0

    def get_wind_count(self):
        return self.windcount

    def calculate_speed(self,time_sec, wind_count):
        circum_in = (2 * math.pi) * self.radius_in
        rotations = wind_count / 2.0

        dist_in = circum_in * rotations

        speed = dist_in / time_sec

        speed = speed / 17.6

        return speed

    def close_sensor(self):
        self.wind_speed_sensor.close()


class sensorCentral:
    def __init__(self):
        self.windSpeed = windSpeed()
        self.rain = rainBucket()
        self.bme = bme()
        self.vane = windVane()

    def reset_counts(self):
        self.windSpeed.reset_wind()
        self.rain.reset_rainfall()

    def close_sensors(self):
        self.windSpeed.close_sensor()
        self.rain.close_sensor()
        self.vane.close_sensor()

    def get_data(self,interval):
        temps = []
        pressures = []
        humidites = []
        vane_dirs = []
        startTime = datetime.now()
        endTime = startTime + timedelta(seconds=interval)
        while datetime.now() < endTime:
            temps.append(self.bme.get_temp())
            pressures.append(self.bme.get_pressure())
            humidites.append(self.bme.get_humidity())
            vane_dirs.append(self.vane.get_angle())
        
        wind_count = self.windSpeed.get_wind_count()

        speed = self.windSpeed.calculate_speed(
            interval,
            wind_count
        )

        angle = self.vane.get_average(vane_dirs)
        direction = self.vane.get_direction(angle)

        temp = mean(temps)
        pressure = mean(pressures)
        humidity = mean(humidites)
        rain = self.rain.calculate_rain(
            self.rain.get_rain_count()
        )
        self.reset_counts()

        finalData = [wind_count,speed,direction,temp,pressure,humidity,rain]

        return finalData
        

