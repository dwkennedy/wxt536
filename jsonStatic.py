#!/usr/bin/python3

# subscribe to mqtt message content, publish to webservr diretory as JSON
# the web page will format and display the JSON data
# and periodically update via the webserver (not directly to this program)
#

import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import re
#from urllib.parse import unquote
import paho.mqtt.client as mqtt
import logging

BROKER_ADDRESS = '127.0.0.1'
WXT_SERIAL = 'N3720229' # PTU S/N N3620062.  Which instrument's data to serve
TIMEOUT = 20  # seconds before considering current data stale
TARGET_FILENAME = '/var/www/html/wx/wx.json'
current = {'valid': 0, 'time': 0}

def write_JSON(wxt):
        
        if ((time.time() - float(current['time']))<TIMEOUT):
           wxt['valid'] = 1;
        else:
           wxt['valid'] = 0;
      
        try:
           logging.info(json.dumps(wxt))
           file = open(TARGET_FILENAME,'w',encoding='utf-8')
           file.write(json.dumps(wxt))
           file.close()
        except Exception as e:
           logging.critical("Failed to write file in output directory! %s", e)
           raise


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
            write_JSON(current) 
        except:
            print("Failed decoding json")

    def __init__(self):

      # pub/sub to relavent MQTT topics so we can respond to requests with JSON
      logging.info("init mqttHandler")
      client = mqtt.Client("jsonServer")
      client.on_message = self.on_message
      client.connect(BROKER_ADDRESS)
      client.loop_start()
      client.subscribe('wxt/{}'.format(WXT_SERIAL))

def main():
    global current

    FORMAT = '%(asctime)s %(levelname)s: %(message)s'
    logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt='%m/%d/%Y %H:%M:%S')
    logging.info("jsonServer.py starts - %s", TARGET_FILENAME)

    # fire up mqttHandler to pub/sub to topics
    # should use class factory to pass robot object to httpHandler
    robot = mqttHandler()

    while True:
        time.sleep(20) 
        write_JSON(current)  # in case we aren't getting new data from mqtt broker

    logging.info("jsonServer.py stops - %s", TARGET_FILENAME)


# kick off server when the script is called
if __name__ == '__main__':
    main()

