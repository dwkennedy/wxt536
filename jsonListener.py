#!/usr/bin/python3

# subscribe to wxt/SERIAL topic
# as message arrive, decode and appent to JSON file
# if json file doesn't exist for that day, create a new one

import time
import os
import json
import paho.mqtt.client as mqtt
import logging
from secret import *

#LOCAL_BROKER_ADDRESS defined in secret.py
WXT_SERIAL = 'N3720229' # PTU S/N N3620062.  Which instrument's data to serve
JSON_OUTPUT_DIRECTORY = '/home/doug/netcdf'


class mqttHandler:
    # keep track of current filename/handle. close old file/open new at start of new day
    filename = ""
    filehandle = ""

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

        # current holds our incoming mqtt data.  it starts out invalid and out-of-date
        current = {'time': 0}

        try:
            current = json.loads(message.payload.decode('utf-8'))
            logging.debug(json.dumps(current))
        except:
            logging.critical("mqttHandler failed decoding incoming json")
            return
            #raise

        #  check to see if json file exists
        (tm_year,tm_mon,tm_mday,tm_hour,tm_min,tm_sec,tm_wday,tm_yday,tm_isdst)=time.gmtime(current['time'])
        new_filename = "{}/clamps_sfc_{:04d}{:02d}{:02d}.json".format(JSON_OUTPUT_DIRECTORY,tm_year,tm_mon,tm_mday)
        if (self.filename != new_filename):
           if (self.filename != ''):
              self.filehandle.close()
           self.filename = new_filename
           logging.info("mqttHandler opening/appending file {}".format(self.filename))
           self.filehandle = open(self.filename,'a')
 
        #  insert all the goodies into the json file
        #print("writing {} to {}".format(current['time'],self.filename))
        #print(self.filehandle)
        json.dump(current, self.filehandle) 
        self.filehandle.write('\n')
        self.filehandle.flush()

        #print("closing {}".format(filename))

    def __init__(self):
        # pub/sub to relavent MQTT topics so we can respond to requests with JSON
        logging.info("mqttHandler init client json-listener-%s", os.getpid())
        client = mqtt.Client("json-listener-{}".format(os.getpid()))
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.username_pw_set(MQTT_USERNAME,MQTT_PASSWORD)
        logging.info('mqttHandler connecting to %s',LOCAL_BROKER_ADDRESS)
        client.connect(LOCAL_BROKER_ADDRESS)
        #client.subscribe('wxt/{}'.format(WXT_SERIAL))
        client.loop_start();  # blocking loop function to handle callbacks, reconnects, etc
        logging.debug('mqttHandler loop started')

def main():
    FORMAT = '%(asctime)s %(levelname)s: %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=FORMAT, datefmt='%m/%d/%Y %H:%M:%S')

    logging.info("jsonListener.py starts")

#    paho = mqtt.Client('fridge-consumer-%s',(os.getpid()))
#    paho.on_message = on_message
#    paho.on_connect = on_connect
#    paho.username_pw_set(PAHO_USERNAME,PAHO_PASSWORD)
#    paho.connect(LOCAL_BROKER_ADDRESS)
#    paho.subscribe('fridge')  # subscribe to fridge status

    # fire up mqttHandler to pub/sub to topics, reconnect when needed
    robot = mqttHandler()

    while True:
           logging.debug("mark")
           time.sleep(60)
    #except KeyboardInterrupt:
    #    pass

    logging.info("jsonListener.py stops")


# kick off server when the script is called
if __name__ == '__main__':
    main()

