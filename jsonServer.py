#!/usr/bin/python

# create http server  (documented at https://docs.python.org/2/library/basehttpserver.html#BaseHTTPServer.BaseHTTPRequestHandler)
# accept commands encoded in URL
#
# return mqtt message content as JSON
# the web page will format and display the JSON data
# and periodically update via the URL
#
# this server subscribes to mqtt server and retains the last value of each message to serve
#

import time
import BaseHTTPServer
import json
import re
from urllib import unquote
import paho.mqtt.client as mqtt

# define our ROS master hostname, and the port our http server will listen on
HOST_NAME = '0.0.0.0'
PORT_NUMBER = 4444
BROKER_ADDRESS = '127.0.0.1'
WXT_SERIAL = 'N3720229' # PTU S/N N3620062
TIMEOUT = 20  # seconds before considering current data stale

current = {'Rd':{'value':'0.0'},'Rc':{'value':'0.0'},'Ri':{'value':'0.0'},'validFlag':0}
current['valid'] = time.time() - TIMEOUT  # stale data to begin with

# this code creates the http server and dispatches commands that are received
class httpHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_HEAD(s):
        s.send_response(200)
        s.send_header("Content-type", "application/json")
        s.send_header("Access-Control-Allow-Origin", "*")
        s.end_headers()

    def do_GET(s):
        """Respond to a GET request."""
        s.send_response(200)
        s.send_header("Content-type", "application/json")
        s.send_header("Access-Control-Allow-Origin", "*")
        s.end_headers()
        #key = unquote(s.path)
        #key = key[1:]   # remove leading '/'
        #print("Trying {0}".format(key))
        if ((time.time() - float(current['valid']))<TIMEOUT):
           current['validFlag'] = 1;
           #print ("{} - {} = {}".format(time.time(),current['valid'],(time.time()-float(current['valid']))))
        else:
           current['validFlag'] = 0;
           #print ("{} - {} = {}".format(time.time(),current['valid'],(time.time()-float(current['valid']))))
       
        try:
           s.wfile.write(json.dumps(current,s.wfile))
           print(json.dumps(current))
        except:
           pass

#  get data from current dictionary and return values as JSON
class mqttHandler:

    # now we define the callbacks to handle messages we subcribed to
    def on_message(self, client, userdata, message):
        #print("message received: {0}".format(str(message.payload.decode("utf-8"))))
        #print("message topic: {0}".format(message.topic))
        #print("message qos: {0}".format(message.qos))
        #print("message retain flag: {0}".format(message.retain))
        # remove leading 'wxt/WXT_SERIAL'
        try:
           components = message.topic.split('/')
           message.topic = str(components[2].decode('utf-8'))
           message.payload = message.payload.decode('utf-8')
        except:
           print("Malformed message topic " + message.topic);

        #print('MQTT: {0}: {1}'.format(message.topic, message.payload))
        #current[str(message.topic)] = json.loads(message.payload);
        #lastValidTimestamp = float(current[str(message.topic)]['timestamp'])
        current[message.topic] = json.loads(message.payload)
        current['valid'] = time.time()

    def __init__(self):

      # pub/sub to relavent MQTT topics so we can respond to requests with JSON
      print ("init mqttHandler")
      client = mqtt.Client("jsonServer")
      client.on_message = self.on_message
      client.connect(BROKER_ADDRESS)
      client.loop_start()
      client.subscribe('wxt/{}/#'.format(WXT_SERIAL))

# kick off server when the script is called
if __name__ == '__main__':


    # fire up mqttHandler to pub/sub to topics
    # should use class factory to pass robot object to httpHandler
    robot = mqttHandler()

    # start http server and listen for requests
    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), httpHandler)
    print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)


