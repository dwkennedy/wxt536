#!/usr/bin/python3

# subscribe to wxt/SERIAL topic
# as message arrive, decode and appent to JSON file
# if json file doesn't exist for that day, create a new one

import time
import json
import paho.mqtt.client as mqtt
#import metTower
#from netCDF4 import Dataset
import logging
from secret import *

BROKER_ADDRESS = '127.0.0.1'
WXT_SERIAL = 'N3720229' # PTU S/N N3620062.  Which instrument's data to serve
JSON_OUTPUT_DIRECTORY = '/home/doug/netcdf'

# current holds our incoming mqtt data.  it starts out invalid and out-of-date
current = {'time': 0}

class mqttHandler:
    filename = ""
    filehandle = ""
 
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
            logging.critical("failed decoding incoming json")
            #raise

        #  check to see if netcdf file exists
        (tm_year,tm_mon,tm_mday,tm_hour,tm_min,tm_sec,tm_wday,tm_yday,tm_isdst)=time.gmtime(current['time'])
        new_filename = "{}/clamps_sfc_{:04d}{:02d}{:02d}.json".format(JSON_OUTPUT_DIRECTORY,tm_year,tm_mon,tm_mday)
        if (self.filename != new_filename):
           if (self.filename != ''):
              self.filehandle.close()
           self.filename = new_filename
           logging.info("opening/appending file {}".format(self.filename))
           self.filehandle = open(self.filename,'a')
 
        #  insert all the goodies into the netcdf file
        #print("writing {} to {}".format(current['time'],self.filename))
        #print(self.filehandle)
        json.dump(current, self.filehandle) 
        self.filehandle.write('\n')
        self.filehandle.flush()

        #print("closing {}".format(filename))
        #ncfile.close()

    def __init__(self):

      # pub/sub to relavent MQTT topics so we can respond to requests with JSON
      logging.info("init mqttHandler")
      client = mqtt.Client("netcdfListener")
      client.on_message = self.on_message
      client.username_pw_set(MQTT_USERNAME,MQTT_PASSWORD)
      client.connect(BROKER_ADDRESS)
      client.loop_start()
      client.subscribe('wxt/{}'.format(WXT_SERIAL))

def main():
    global current

    FORMAT = '%(asctime)s %(levelname)s: %(message)s'
    logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt='%m/%d/%Y %H:%M:%S')

    # fire up mqttHandler to pub/sub to topics
    # should use class factory to pass robot object to httpHandler
    robot = mqttHandler()

    logging.info("jsonListener.py starts")
    try:
        while True:
           time.sleep(60)  
    except KeyboardInterrupt:
        pass

    logging.info("jsonListener.py stops")


# kick off server when the script is called
if __name__ == '__main__':
    main()

