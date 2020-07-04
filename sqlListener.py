#!/usr/bin/python3

# this server subscribes to mqtt server and inserts each arriving record
#  into an sql database

import time
import os
import json
import re
import paho.mqtt.client as mqtt
import math
from wxFormula import *
import logging
import sqlite3
from secret import *

# LOCAL_BROKER_ADDRESS set in secret.py
WXT_SERIAL = 'N3720229' # PTU S/N N3620062

# documentation for sqlListener PWS update
# https://support.weather.com/s/article/PWS-Upload-Protocol?language=en_US

def C2F(C):
    return(((float(C)*9)/5)+32)

def ms2mph(ms):
    return(float(ms)*2.236936)

def mm2in(mm):
    return(float(mm)*0.03937008)

def mbar2inhg(mbar):
    return(float(mbar)*0.02952998)



# this code creates the GET request to sqlListener
def createSQL(wxt):
    # set to missing values
    #time = time.time()
    try:
        sql = "INSERT INTO WX (TIME, WINDDIRMIN, WINDSPDMIN, \
WINDDIRAVE, WINDDIRAVE, \
WINDDIRMAX, WINDSPDMAX, \
TEMPERATURE, HUMIDITY, DEWPOINT, PRESSURE, \
RAINAMT24H, RAININTENSITY, RAINDURATION, \
HAILAMT24H, HAILINTENSITY, HAILDURATION) \
VALUES ("

        sql += "{}".format(safe_int(wxt['time']))
        sql += ",{}".format(float(wxt['Dn']['value']))
        sql += ",{}".format(float(wxt['Sn']['value']))
        sql += ",{}".format(float(wxt['Dx']['value']))
        sql += ",{}".format(float(wxt['Sx']['value']))
        sql += ",{}".format(float(wxt['Dm']['value']))
        sql += ",{}".format(float(wxt['Sm']['value']))
        sql += ",{}".format(float(wxt['Ta']['value']))
        sql += ",{}".format(float(wxt['Ua']['value']))
        sql += ",{}".format(float(wxt['Td']['value']))
        sql += ",{}".format(float(wxt['Pa']['value']))
        sql += ",{}".format(float(wxt['Rc']['value']))
        sql += ",{}".format(float(wxt['Ri']['value']))
        sql += ",{}".format(float(wxt['Rd']['value']))
        sql += ",{}".format(float(wxt['Hc']['value']))
        sql += ",{}".format(float(wxt['Hi']['value']))
        sql += ",{}".format(float(wxt['Hd']['value']))
        sql += ");"
    
    except KeyError as e:
        sql = ''
        logging.warning("Missing parameter. check WXT-536 configuration: {}".format(e))
        raise  # re-raise error so the caller knows we've failed

    return(sql)

#  get data from current dictionary and return values as JSON
class mqttHandler:

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        logging.info("mqttHandler connected with result code "+str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe('wxt/{}'.format(WXT_SERIAL))

    # the callback to handle messages we subcribed to
    def on_message(self, client, userdata, message):
        #print("message topic: {}".format(message.topic))
        #print("message received: {}".format(message.payload.decode("utf-8")))
        #print("message qos: {0}".format(message.qos))
        #print("message retain flag: {0}".format(message.retain))

        try:
            db = sqlite3.connect(DATABASE_FILE)
            current = json.loads(message.payload.decode('utf-8'))
            logging.debug(json.dumps(current))
            sql = createSQL(current)
            logging.info("inserting record in database: {}".format(sql))
            db.execute(sql)
            db.commit()
            db.close()
        except KeyError:
            logging.warning('missing parameter in wxt message: {}: {}'.format(json.dumps(wxt)),e)
        except Exception as e:
            logging.critical("bizzare error: {}".format(e))
            raise

    def __init__(self):
        # pub/sub to relavent MQTT topics so we can respond to requests with JSON
        logging.info("mqttHandler init client sqlListener-{}".format(os.getpid()))
        client = mqtt.Client("sqlListener-{}".format(os.getpid()))
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.username_pw_set(MQTT_USERNAME,MQTT_PASSWORD)
        client.connect(LOCAL_BROKER_ADDRESS, port=LOCAL_BROKER_PORT, keepalive=60)
        client.loop_start()

def main():

    FORMAT = '%(asctime)s %(levelname)s: %(message)s'
    logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt='%m/%d/%Y %H:%M:%S')

    logging.info("sqlListener.py client starts")

    #db = sqlite3.connect(DATABASE_FILE)

    # fire up mqttHandler to pub/sub to topics
    # should use class factory to pass robot object to httpHandler
    robot = mqttHandler()

    try:
       while True:
          time.sleep(60) 
    except KeyboardInterrupt as e:
       pass
    except Exception as e:
       logging.critical("sqlListener.py stops with exception %s",e)
  
    logging.info("sqlListener.py client stops")

# kick off server when the script is called
if __name__ == '__main__':
    main()
