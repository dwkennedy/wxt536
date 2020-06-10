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

BROKER_ADDRESS = '127.0.0.1'  # mqtt broker
WXT_SERIAL = 'N3720229' # PTU S/N N3620062
BASE_URL = "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php?"
# optional for realtime update
#BASE_URL = "https://rtupdate.wunderground.com/weatherstation/updateweatherstation.php?"
PUBLISHING_INTERVAL = 300   # publish every X seconds

WUNDERGROUND_ID = 'KOKNORMA6'  # station ID
WUNDERGROUND_PASSWORD = '78ce9f30'

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
    try:
        winddir_avg2m = wxt['Dm']['value']
        windspeedmph_avg2m = ms2mph(float(wxt['Sm']['value']))
        windgustdir = wxt['Dx']['value']
        windgustmph = ms2mph(float(wxt['Sx']['value']))
        tempc = float(wxt['Ta']['value'])
        humidity = float(wxt['Ua']['value'])
        dewptf = C2F(float(wxt['Td']['value']))
        tempf = C2F(float(wxt['Ta']['value']))
        baromin = mbar2inhg(float(wxt['Pb']['value'])) 
        dailyrainin = mm2in(float(wxt['Rc']['value']))
    except KeyError:
        print("Missing parameter. check WXT-536 configuration")
        raise  # re-raise error so the caller knows we've failed

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
    url += "&baromin={:.3f}".format(baromin)
    url += "&dailyrainin={:.3f}".format(dailyrainin)
    url += "&softwaretype={}".format(softwaretype)
    # optional for realtime wunderground server
    #url += "&realtime=1&rtfreq={}".format(PUBLISHING_INTERVAL)

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
            #print(json.dumps(current))
        except:
            print("Failed decoding json")

    def __init__(self):
        # pub/sub to relavent MQTT topics so we can respond to requests with JSON
        print("{}: {}".format(time.asctime(), "init mqttHandler"))
        client = mqtt.Client("wunderground")
        client.on_message = self.on_message
        client.connect(BROKER_ADDRESS)
        client.loop_start()
        client.subscribe('wxt/{}'.format(WXT_SERIAL))


def main():
    global current
    # fire up mqttHandler to pub/sub to topics
    # should use class factory to pass robot object to httpHandler

    robot = mqttHandler()

    # send update every minute
    print("{}: {}".format(time.asctime(), "Wunderground client starts"))
    time.sleep(5.1)  # let first messages get published
    timer = time.time()
    
    while True:
        try:
            url = createGET(current)
            print("{}: {}".format(time.asctime(), url))
            f = urllib.request.urlopen(str(url))
            print("{}: {}".format(time.asctime(), f.read().strip().decode('utf-8')))
            current={}  # success publishing, clear current
        except KeyError:
            print('caught KeyError, missing parameter')
        except urllib.error.URLError as e:
            print("URLError: {}".format(e))
        except:
            print("some other bizzare error")

        time.sleep(PUBLISHING_INTERVAL-(time.time()-timer))
        timer = time.time()

    print("{}: {}".format(time.asctime(), "Wunderground client stops"))


# kick off server when the script is called
if __name__ == '__main__':
    main()
