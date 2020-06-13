#!/usr/bin/python3

# this server subscribes to mqtt server and retains the last value of each message to serve
#  upload data to pwsweather every PUBLISHING_INTERVAL seconds

import time
import json
import re
import urllib.request
import urllib.error
import urllib.parse
import paho.mqtt.client as mqtt
import math
import wxFormula
import requests
from secret import *
import logging

BROKER_ADDRESS = '127.0.0.1'  # mqtt broker
WXT_SERIAL = 'N3720229' # PTU S/N N3620062
#BASE_URL = "http://www.pwsweather.com/pwsupdate/pwsupdate.php?"
BASE_URL = "http://www.pwsweather.com/pwsupdate/pwsupdate.php"
PUBLISHING_INTERVAL = 120   # publish every X seconds

PWSWEATHER_ID = 'WEATHERBOT'  # station ID
#PWSWEATHER_PASSWORD = secret.PWS_PASSWORD

current = {}  # create empty dictionary of current observations

# documentation for PWSweather update
# GET: https://github.com/cmcginty/PyWeather/blob/master/weather/services/pws.py
# POST: https://github.com/johnny2678/wupws/blob/master/wu-pws.sh

def C2F(C):
    return(((float(C)*9)/5)+32)

def ms2mph(ms):
    return(float(ms)*2.236936)

def mm2in(mm):
    return(float(mm)*0.03937008)

def mbar2inhg(mbar):
    return(float(mbar)*0.02952998)

# this code executes the POST request to PWSweather
def createPOST(wxt):
    # set to missing values
    action = 'updateraw'
    #dateutc = 'now'
    #dateutc = urllib.parse.quote_plus(time.strftime("%Y-%m-%d %H:%M:%S",time.gmtime()))
    dateutc = time.strftime("%Y-%m-%d %H:%M:%S",time.gmtime())
    winddir_avg2m = 0 # 'Dm'
    windspeedmph_avg2m = ms2mph(0) # 'Sm'  # convert from m/s to mph
    windgustmph = ms2mph(0)  # 'Sx'  # convert from m/s to mph
    windgustdir = 0  # 'Dx'
    humidity = 0  # 'Ua'
    tempf = C2F(0)  #  'Ta'
    baromin = mbar2inhg(0) # 'Pa'  # convert mbar to inHg
    softwaretype = 'custom'
    dailyrainin = mm2in(0)  # 'Rc', reset at midnight local time
    rainin = mm2in(0)  # 'Ri', rain intensity in in/hr
    try:
        baromin = mbar2inhg(float(wxt['Pb']['value'])) 
        dailyrainin = mm2in(float(wxt['Rc']['value']))
        dewptf = C2F(float(wxt['Td']['value']))
        humidity = float(wxt['Ua']['value'])
        rainin = mm2in(float(wxt['Ri']['value']))
        tempf = C2F(float(wxt['Ta']['value']))
        winddir_avg2m = wxt['Dm']['value']
        windgustmph = ms2mph(float(wxt['Sx']['value']))
        windspeedmph_avg2m = ms2mph(float(wxt['Sm']['value']))
        windgustdir = wxt['Dx']['value']
    except KeyError:
        logging.critical("Missing parameter. check WXT-536 configuration")
        raise  # re-raise error so the caller knows we've failed

    url = {}
    url['action'] = action
    url['ID'] = PWSWEATHER_ID
    url['PASSWORD'] = PWSWEATHER_PASSWORD
    url['dateutc'] = dateutc
    url['winddir'] = winddir_avg2m
    url['windspeedmph'] = "{:.2f}".format(windspeedmph_avg2m)
    url['windgustmph'] = "{:.2f}".format(windgustmph)
    url['windgustdir'] = windgustdir
    url['humidity'] = "{:.1f}".format(humidity)
    url['dewpt'] = "{:.1f}".format(dewptf)
    url['tempf'] = "{:.2f}".format(tempf)
    url['baromin'] = "{:.3f}".format(baromin)
    url['dailyrainin'] = "{:.3f}".format(dailyrainin)
    url['rainin'] = "{:.3f}".format(rainin)
    url['softwaretype'] = softwaretype

    logging.debug(json.dumps(url))
    return(requests.post(BASE_URL, data = url))
    
# this code creates the GET request to PWSweather
def createGET(wxt):
    # set to missing values
    action = 'updateraw'
    #dateutc = 'now'
    dateutc = urllib.parse.quote_plus(time.strftime("%Y-%m-%d %H:%M:%S",time.gmtime()))
    winddir_avg2m = 0 # 'Dm'
    windspeedmph_avg2m = ms2mph(0) # 'Sm'  # convert from m/s to mph
    windgustmph = ms2mph(0)  # 'Sx'  # convert from m/s to mph
    windgustdir = 0  # 'Dx'
    humidity = 0  # 'Ua'
    tempf = C2F(0)  #  'Ta'
    baromin = mbar2inhg(0) # 'Pa'  # convert mbar to inHg
    softwaretype = 'custom'
    dailyrainin = mm2in(0)  # 'Rc', reset at midnight local time
    rainin = mm2in(0)  # 'Ri', rain intensity in in/hr
    try:
        baromin = mbar2inhg(float(wxt['Pb']['value'])) 
        dailyrainin = mm2in(float(wxt['Rc']['value']))
        dewptf = C2F(float(wxt['Td']['value']))
        humidity = float(wxt['Ua']['value'])
        rainin = mm2in(float(wxt['Ri']['value']))
        tempf = C2F(float(wxt['Ta']['value']))
        winddir_avg2m = wxt['Dm']['value']
        windgustmph = ms2mph(float(wxt['Sx']['value']))
        windspeedmph_avg2m = ms2mph(float(wxt['Sm']['value']))
        windgustdir = wxt['Dx']['value']
    except KeyError:
        logging.critical("missing parameter. check WXT-536 configuration")
        raise  # re-raise error so the caller knows we've failed

    url = ''
    url += "action={}".format(action)
    url += "&ID={}".format(PWSWEATHER_ID)
    url += "&PASSWORD={}".format(PWSWEATHER_PASSWORD)
    url += "&dateutc={}".format(dateutc)
    url += "&winddir={}".format(winddir_avg2m)
    url += "&windspeedmph={:.2f}".format(windspeedmph_avg2m)
    url += "&windgustmph={:.2f}".format(windgustmph)
    url += "&windgustdir={}".format(windgustdir)
    url += "&humidity={:.1f}".format(humidity)
    url += "&dewptf={:.1f}".format(dewptf)
    url += "&tempf={:.2f}".format(tempf)
    url += "&baromin={:.3f}".format(baromin)
    url += "&dailyrainin={:.3f}".format(dailyrainin)
    url += "&rainin={:.3f}".format(rainin)
    url += "&softwaretype={}".format(softwaretype)

    return(BASE_URL + url)

#  get data from current dictionary and return values as JSON
class mqttHandler:

    # now we define the callbacks to handle messages we subcribed to
    def on_message(self, client, userdata, message):
        global current
        #print("message topic: {}".format(message.topic))
        #print("message received: {}".format(message.payload.decode("utf-8")))
        #print("message qos: {0}".format(message.qos))
        #print("message retain flag: {0}".format(message.retain))

        try:
            current = json.loads(message.payload.decode('utf-8'))
            logging.debug(json.dumps(current))
        except:
            logging.warning("failed decoding incoming mqtt json")

    def __init__(self):
        # pub/sub to relavent MQTT topics so we can respond to requests with JSON
        logging.info("registering mqttHandler")
        client = mqtt.Client("pwsweather")
        client.on_message = self.on_message
        client.connect(BROKER_ADDRESS)
        client.loop_start()
        client.subscribe('wxt/{}'.format(WXT_SERIAL))


def main():
    global current
    # fire up mqttHandler to pub/sub to topics
    # should use class factory to pass robot object to httpHandler

    FORMAT = '%(asctime)s %(levelname)s: %(message)s'
    logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt='%m/%d/%Y %H:%M:%S')
    logging.info("pwsweather.py client starts")

    robot = mqttHandler()

    time.sleep(5.1)  # let first wxt message get published
    
    # send update every PUBLISHING_INTERVAL seconds
    while True:
        try:
            timer = time.time()
            logging.info("sending POST request")
            f = createPOST(current)
            logging.info("reply: {}".format(re.sub(r'\n',' ',f.text)))
            current={}  # success publishing, clear current
        except KeyError:
            logging.warning('caught KeyError, missing parameter')
        except urllib.error.URLError as e:
            logging.warning("URLError: {}".format(e))
        except:
            logging.critical("some other bizzare error")
            #raise

        sleepy = PUBLISHING_INTERVAL-(time.time()-timer)
        if(sleepy>0):
           time.sleep(sleepy)

    logging.info("pwsweather.py client stops")


# kick off server when the script is called
if __name__ == '__main__':
    main()
