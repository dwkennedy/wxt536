#!/usr/bin/python3

# this server subscribes to mqtt server and retains the last value of each message to serve
#  upload data to wunderground every minute

import time
import json
import re
import urllib.request
import urllib.error
import urllib.parse
import paho.mqtt.client as mqtt
import math
import wxFormula
import logging
from secret import *

BROKER_ADDRESS = '127.0.0.1'  # mqtt broker
WXT_SERIAL = 'N3720229' # PTU S/N N3620062
BASE_URL = "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php?"
# optional for realtime update
#BASE_URL = "https://rtupdate.wunderground.com/weatherstation/updateweatherstation.php?"
PUBLISHING_INTERVAL = 120   # publish every X seconds

#WUNDERGROUND_ID secret.WUNDERGROUND_ID # station ID
#WUNDERGROUND_PASSWORD = secret.WUNDERGROUND_PASSWORD

current = {}  # create empty dictionary of current observations

# documentation for wunderground PWS update
# https://support.weather.com/s/article/PWS-Upload-Protocol?language=en_US

def C2F(C):
    return(((float(C)*9)/5)+32)

def ms2mph(ms):
    return(float(ms)*2.236936)

def mm2in(mm):
    return(float(mm)*0.03937008)

def mbar2inhg(mbar):
    return(float(mbar)*0.02952998)



# this code creates the GET request to wunderground
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
    rainin = mm2in(0)  # 'Ri', rain intensity 
    try:
        winddir_avg2m = wxt['Dm']['value']
        windspeedmph_avg2m = ms2mph(float(wxt['Sm']['value']))
        windgustdir = wxt['Dx']['value']
        windgustmph = ms2mph(float(wxt['Sx']['value']))
        tempc = float(wxt['Ta']['value'])
        humidity = float(wxt['Ua']['value'])
        dewptf = C2F(float(wxt['Td']['value']))
        tempf = C2F(float(wxt['Ta']['value']))
        if (wxt['Pb']['value'] is not None):
            baromin = mbar2inhg(float(wxt['Pb']['value'])) 
        dailyrainin = mm2in(float(wxt['Rc']['value']))
        rainin = mm2in(float(wxt['Ri']['value']))

        url = ''
        url += "action={}".format(action)
        url += "&ID={}".format(WUNDERGROUND_ID)
        url += "&PASSWORD={}".format(WUNDERGROUND_PASSWORD)
        url += "&dateutc={}".format(dateutc)
        url += "&winddir={}".format(winddir_avg2m)
        url += "&windspeedmph={:.2f}".format(windspeedmph_avg2m)
        url += "&winddir_avg2m={}".format(winddir_avg2m)
        url += "&windspeedmph_avg2m={:.2f}".format(windspeedmph_avg2m)
        url += "&winddir_avg2m={}".format(winddir_avg2m)
        url += "&windgustmph={:.2f}".format(windgustmph)
        url += "&windgustdir={}".format(windgustdir)
        url += "&humidity={:.1f}".format(humidity)
        url += "&dewptf={:.1f}".format(dewptf)
        url += "&tempf={:.2f}".format(tempf)
        if(wxt['Pb']['value'] is not None):
            url += "&baromin={:.3f}".format(baromin)
        url += "&dailyrainin={:.3f}".format(dailyrainin)
        url += "&rainin={:.3f}".format(rainin)
        url += "&softwaretype={}".format(softwaretype)
        # optional for realtime wunderground server
        #url += "&realtime=1&rtfreq={}".format(PUBLISHING_INTERVAL)
    
    except KeyError:
        url = ''
        logging.warning("Missing parameter. check WXT-536 configuration")
        #raise  # re-raise error so the caller knows we've failed

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
            logging.warning("wunderground.py failed decoding WXT json")

    def __init__(self):
        # pub/sub to relavent MQTT topics so we can respond to requests with JSON
        logging.info("registering mqttHandler")
        client = mqtt.Client("wunderground")
        client.on_message = self.on_message
        client.username_pw_set(MQTT_USERNAME,MQTT_PASSWORD)
        client.connect(BROKER_ADDRESS)
        client.loop_start()
        client.subscribe('wxt/{}'.format(WXT_SERIAL))


def main():
    global current

    FORMAT = '%(asctime)s %(levelname)s: %(message)s'
    logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt='%m/%d/%Y %H:%M:%S')

    logging.info("wunderground.py client starts")

    # fire up mqttHandler to pub/sub to topics
    # should use class factory to pass robot object to httpHandler
    robot = mqttHandler()

    time.sleep(5.1)  # let first messages get published
    
    # send update every PUBLISHING_INTERVAL seconds
    while True:
        try:
            last_time = time.time()
            url = createGET(current)
            logging.info("sending GET request: {}".format(url))
            f = urllib.request.urlopen(str(url))
            logging.info("reply: {}".format(f.read().strip().decode('utf-8')))
            current={}  # success publishing, clear current
        except KeyError:
            logging.warning('missing parameter in wxt message: {}'.format(json.dumps(wxt)))
        except urllib.error.URLError as e:
            logging.warning("URLError: {}".format(e))
        except Exception as e:
            logging.critical("bizzare error: {}".format(e))
            #raise

        sleep_time = PUBLISHING_INTERVAL-(time.time()-last_time)
        if(sleep_time > 0):
            time.sleep(sleep_time)
        else:
            # i think this could happen if there was a big delay in publishing (>PUBLISHING_INTERVAL secs)
            #  or maybe the system clock had a big adjustment
            logging.critical("How did I get a negative sleep_time? time.time(): {} last_time:{} sleep_time: {}".format(time.time(),last_time,sleep_time))
            #break
     
    logging.info("wunderground.py client stops")

# kick off server when the script is called
if __name__ == '__main__':
    main()
