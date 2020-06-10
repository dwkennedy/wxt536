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
           print("{}: {}".format(time.asctime(),json.dumps(current)))
           s.wfile.write(json.dumps(current).encode('utf-8'))
        except:
           print("something broke in httpHandler!")

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
            #print(json.dumps(current))
        except:
            print("Failed decoding json")

    def __init__(self):

      # pub/sub to relavent MQTT topics so we can respond to requests with JSON
      print ("init mqttHandler")
      client = mqtt.Client("jsonServer")
      client.on_message = self.on_message
      client.connect(BROKER_ADDRESS)
      client.loop_start()
      client.subscribe('wxt/{}'.format(WXT_SERIAL))

def main():
    global current

    # fire up mqttHandler to pub/sub to topics
    # should use class factory to pass robot object to httpHandler
    robot = mqttHandler()

    # start http server and listen for requests
    httpd = HTTPServer((HOST_NAME, PORT_NUMBER), httpHandler)
    print (time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print (time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER))


# kick off server when the script is called
if __name__ == '__main__':
    main()

