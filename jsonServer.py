#!/usr/bin/python3

# create http server
# return mqtt message content as JSON
# the web page will format and display the JSON data
# and periodically update via this server
#
# this server subscribes to mqtt server and retains the last value of each message to serve
#

import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import re
#from urllib.parse import unquote
import paho.mqtt.client as mqtt
import logging

HOST_NAME = '0.0.0.0'
PORT_NUMBER = 4444
BROKER_ADDRESS = '127.0.0.1'
WXT_SERIAL = 'N3720229' # PTU S/N N3620062.  Which instrument's data to serve
TIMEOUT = 20  # seconds before considering current data stale

current = {'valid': 0, 'time': 0}

# this code creates the http server and dispatches commands that are received
class httpHandler(BaseHTTPRequestHandler):

    def do_HEAD(s):
        s.send_response(200)
        s.send_header("Content-type", "application/json")
        s.send_header("Access-Control-Allow-Origin", "*")
        s.end_headers()

    def do_GET(s):
        global current

        """Respond to a GET request."""
        s.send_response(200)
        s.send_header("Content-type", "application/json")
        s.send_header("Access-Control-Allow-Origin", "*")
        s.end_headers()

        if ((time.time() - float(current['time']))<TIMEOUT):
           current['valid'] = 1;
           #print ("{} - {} = {}".format(time.time(),current['valid'],(time.time()-float(current['valid']))))
        else:
           current['valid'] = 0;
           #print ("{} - {} = {}".format(time.time(),current['valid'],(time.time()-float(current['valid']))))
      
        try:
           logging.debug(json.dumps(current))
           s.wfile.write(json.dumps(current).encode('utf-8'))
        except:
           logging.critical("something broke in httpHandler!")
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
    logging.info("jsonServer.py starts - %s:%s" % (HOST_NAME, PORT_NUMBER))

    # fire up mqttHandler to pub/sub to topics
    # should use class factory to pass robot object to httpHandler
    robot = mqttHandler()

    while True:
       # start http server and listen for requests
       httpd = HTTPServer((HOST_NAME, PORT_NUMBER), httpHandler)

       for foo in range(20):
          httpd.handle_request()
       httpd.server_close()
       logging.info("jsonServer.py restarting - %s:%s" % (HOST_NAME, PORT_NUMBER))

    logging.info("jsonServer.py stops - %s:%s" % (HOST_NAME, PORT_NUMBER))


# kick off server when the script is called
if __name__ == '__main__':
    main()

