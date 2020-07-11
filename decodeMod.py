#!/usr/bin/python3

# poll WXT536 for combination message
# read lines of vaisala formatted ASCII from WXT536
# decode each line into dictionary according to abbreviation (Sn, Pa, etc)
# publish every message to local MQTT
# publish decimated messages to remote MQTT

#  example sentences
#0R1,Dn=160D,Dm=182D,Dx=197D,Sn=3.0M,Sm=4.1M,Sx=5.8M
#0R3,Rc=0.01M,Rd=10s,Ri=0.6M,Hc=0.0M,Hd=0s,Hi=0.0M
#0R1,Dn=174D,Dm=198D,Dx=214D,Sn=1.9M,Sm=2.2M,Sx=2.7M
#0R5,Th=16.0C,Vh=14.1N,Vs=14.3V,Vr=3.621V
#0R1,Dn=162D,Dm=182D,Dx=197D,Sn=1.0M,Sm=1.7M,Sx=2.6M
#0R1,Dn=163D,Dm=179D,Dx=190D,Sn=1.0M,Sm=2.6M,Sx=3.1M
#0R1,Dn=166D,Dm=179D,Dx=189D,Sn=3.1M,Sm=4.0M,Sx=4.4M
#0R5,Th=16.0C,Vh=14.1N,Vs=14.3V,Vr=3.622V
#0R1,Dn=165D,Dm=184D,Dx=202D,Sn=2.5M,Sm=3.3M,Sx=4.0M
#0R1,Dn=176D,Dm=213D,Dx=282D,Sn=0.7M,Sm=1.4M,Sx=2.2M
#0R1,Dn=191D,Dm=205D,Dx=218D,Sn=1.7M,Sm=4.0M,Sx=6.5M
#0R5,Th=15.9C,Vh=14.1N,Vs=14.3V,Vr=3.622V
#0R2,Ta=16.1C,Ua=79.3P,Pa=959.7H

# 0 = instrument id
# R = sentence
# {1,2,3,5}  1=winds 2=PTH 3=rain/hail 5=system voltages
# Dn Wind direction minimum
# Dm Wind direction average
# Dx Wind direction maximum
# Sn Wind speed minimum
# Sm Wind speed average
# Sx Wind speed maximum
# Rc Rain accumulation
# Rd Rain duration
# Ri Rain intensity
# Hc Hail accumulation
# Hd Hail duration
# Hi Hail intensity
# Th Heating temerature
# Vh Heating voltage
# Vs Supply voltage
# Vr 3.5 V ref. voltage
# Ta Air temperature
# Ua Relative humidity
# Pa Air pressure

# see documentation for units

import socket
import io
import time
import asyncio
import logging
import json
import paho.mqtt.client as mqtt
import ssl
import wxFormula
from secret import *

#LOCAL_BROKER_ADDRESS defined in secret.py
REMOTE_BROKER_ADDRESS = 'kennedy.tw'  # remote MQTT broker address
WXT_HOST = '10.0.0.72'    # The WXT serial server hostname or IP address
WXT_PORT = 2101           # The port used by the serial server
WXT_SERIAL = 'N3720229'   # PTU S/N N3620062
WXT_ELEVATION = 375.0     # WXT sensor elevation in meters above MSL
WXT_POLLING_INTERVAL = 5  # seconds between polling
#USE_GPS = True    # optionally read GPS data from MQTT /gps/SERIAL_NUMBER topic
USE_GPS = False    # optionally read GPS data from MQTT /gps/SERIAL_NUMBER topic
GPS_ANTENNA_OFFSET = -7.0 # height of gps antenna over pressure sensor; subtract from gps altitude
                          # to find pressure sensor altitude (meters)
                          # positive: gps antenna ABOVE pressure sensor

# use this variable to lock access to serial device
lock = 0
s = None  # global socket
file = None # global wrapper for socket

# now we define the callbacks to handle messages we subcribed to

# listen for commands to send to Vaisala WXT-53X sensor
def on_message_wxt(client, userdata, message):
    global lock
    global s
    global file

    #print("message received: {0}".format(str(message.payload.decode("ISO-8859-1"))))
    #print("message topic: {0}".format(message.topic))
    #print("message qos: {0}".format(message.qos))
    #print("message retain flag: {0}".format(message.retain))
    command = message.payload.decode('ISO-8859-1')
    logging.info('MQTT sub: %s: %s', message.topic, command)
    command += '\r\n'
    line = ''
    while(lock>0):
        sleep(0.1)
    lock = 1  # lock access to serial port
    try:
        s.send(command.encode('ISO-8859-1'))
        line=file.readline().strip().decode('ISO-8859-1')
    except Exception as e:
        logging.error("MQTT send cmd %s to serial device failed: %s",command.strip(),e)

    lock = 0  # release lock
    logging.info("MQTT response %s",line)

def on_message_gps(client, userdata, message):
    global gps_timeout
    global current_gps

    #print("message received: {0}".format(message.payload.decode("ISO-8859-1")))
    #print("message topic: {0}".format(message.topic))
    #print("message qos: {0}".format(message.qos))
    #print("message retain flag: {0}".format(message.retain))
    logging.debug('MQTT sub: %s: %s', message.topic, message.payload.decode('ISO-8859-1'))
    try:
        current_gps = json.loads(message.payload.decode('ISO-8859-1'))
        gps_timeout = time.time()
        #print('{}: MQTT sub: {}'.format(time.asctime(), json.dumps(current_gps)))
    except Exception as e:
        logging.warning("MQTT: can't decode incoming gps message: %s",e)
        #raise

class SocketIO(io.RawIOBase):
    def __init__(self, sock):
        self.sock = sock
    def read(self, sz=-1):
        if (sz == -1): sz=0x7FFFFFFF
        return self.sock.recv(sz)
    def seekable(self):
        return False

def main():
    global lock
    global s
    global file

    FORMAT = '%(asctime)s %(levelname)s: %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=FORMAT, datefmt='%m/%d/%Y %H:%M:%S')
    logging.info("decodeMod.py starts")
    
    while True:
       try:
          s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          s.settimeout(20)  # 1 second timeout for each line read
          s.connect( (WXT_HOST, WXT_PORT) )  # connect requires a tuple (x,y) as argument
          break # stop retrying connection when successful
       except(ConnectionRefusedError):
          logging.warning("connection refused to WXT-536 serial server")
          time.sleep(5)
    
    file = SocketIO(s)
    
    gps_timeout = 0  # last time gps arrived
    current_gps = {'time': gps_timeout, 'gps_time': gps_timeout}
    
    client = mqtt.Client('pbx-wxt-cmd')
    client.on_message = on_message_wxt
    client.username_pw_set(MQTT_USERNAME,MQTT_PASSWORD)
    client.tls_set(ca_certs='/etc/mosquitto/certs/server.crt',cert_reqs=ssl.CERT_NONE)
    client.connect(LOCAL_BROKER_ADDRESS, port=LOCAL_BROKER_PORT)
    client.loop_start()
    client.subscribe('wxt/{}/cmd'.format(WXT_SERIAL))  # subscribe to command channel
    
    if (USE_GPS):
        client = mqtt.Client('pbx-gps')
        client.on_message = on_message_gps
        client.connect(LOCAL_BROKER_ADDRESS)
        client.loop_start()
        client.subscribe('gps/{}'.format(WXT_SERIAL))  # subscribe to command channel
    
        time.sleep(1.1) # let gps load up a measurement
        old_tick = 0
    
    while True:
        param = {}
        line = ''
    
        if(USE_GPS):
            if((time.time() - gps_timeout) < 1.1):  # did gps time advance?
                if( (WXT_POLLING_INTERVAL - (gps_timeout % WXT_POLLING_INTERVAL)) < 1.5) :  # is it almost time?
                    sleepy = WXT_POLLING_INTERVAL - (gps_timeout % WXT_POLLING_INTERVAL) # YES it's time, sleep the last bit then poll sensor
                    logging.debug("FINAL SLEEPING %s",sleepy)
                    time.sleep(sleepy)
                    param = {'time': current_gps['time']} # reset param; 'time' marks when poll sent
                else:
                    if(old_tick != gps_timeout):
                        logging.debug("GPS TICK %s",gps_timeout)
                        old_tick = gps_timeout
                    time.sleep(0.1)  # NOT time, sleep 100ms and try again
                    continue
            else:  # GPS time did not advance, check GPS timeout
                if((time.time() - gps_timeout) > 3):  # new gps not seen, has it been too long?
                    sleepy = WXT_POLLING_INTERVAL - (time.time() % WXT_POLLING_INTERVAL) # trigger on pc clock
                    logging.debug("GIVING UP ON GPS %s",sleepy)
                    time.sleep(sleepy)
                    param = {'time': int(time.time())} # reset params; 'time' marks when poll sent
                else:
                    #logging.debug("WAIT FOR GPS")
                    time.sleep(0.1)  #no gps timeout yet, sleep 100ms and try again
                    continue
        else:
            # use pc clock to time polling of wxt
            sleepy = WXT_POLLING_INTERVAL - (time.time() % WXT_POLLING_INTERVAL)
            if(sleepy>0):
                time.sleep(sleepy)
                logging.debug("Sleeping for %s",sleepy)
    
        logging.debug("waiting to reserve serial port")
        while(lock>0):
            time.sleep(0.1)
        lock = 1
        logging.debug("flushing wxt input buffer")
        s.setblocking(False)
        while True:
           try:
              cruft = s.recv(0x7FFFFFFF).decode('ISO-8859-1')
              logging.debug("cruft: %s", cruft)  # flush input buffer
           except(BlockingIOError):
              #logging.debug("no cruft")
              break
        s.settimeout(WXT_POLLING_INTERVAL/2)
        logging.debug("sending 0R command")
        s.send(u'0R\r\n'.encode())  # send command to return all sentences
        logging.debug("reading sentences")
        param = {'time': int(time.time())} # reset params; timer marks when poll sent
        for index in range(4):  # read four lines of response (0R1,0R2,0R3,0R5)
           try:
              line=file.readline().decode('ISO-8859-1')
           except:
              logging.warning("timeout reading from WXT-536")
              break
           #logging.debug(line.strip())
           chunks = line.strip().split(',')
           chunks = chunks[1:]  # drop initial 0R[1235]
           for chunk in chunks:
              try:
                (label, content) = chunk.split('=',1)
                value = content[:-1]
                unit = content[-1]
                param[label] = {'value': value, 'unit': unit}
              except:
                logging.debug("bad chunk: %s", chunk)
                break

        lock = 0  # release serial port lock
    
        # validate each parameter, convert to float
        try:
            param['Ta']['value'] = wxFormula.safe_float(param['Ta']['value'] )
            param['Pa']['value'] = wxFormula.safe_float(param['Pa']['value'] )
            param['Ua']['value'] = wxFormula.safe_float(param['Ua']['value'] )
            param['Sx']['value'] = wxFormula.safe_float(param['Sx']['value'] )
            param['Sm']['value'] = wxFormula.safe_float(param['Sm']['value'] )
            param['Sn']['value'] = wxFormula.safe_float(param['Sn']['value'] )
            param['Dx']['value'] = wxFormula.safe_int(param['Dx']['value'] )
            param['Dm']['value'] = wxFormula.safe_int(param['Dm']['value'] )
            param['Dn']['value'] = wxFormula.safe_int(param['Dn']['value'] )
            param['Rc']['value'] = wxFormula.safe_float(param['Rc']['value'] )
            param['Ri']['value'] = wxFormula.safe_float(param['Ri']['value'] )
            param['Rd']['value'] = wxFormula.safe_int(param['Rd']['value'] )
            param['Hc']['value'] = wxFormula.safe_float(param['Hc']['value'] )
            param['Hd']['value'] = wxFormula.safe_int(param['Hd']['value'] )
            param['Hi']['value'] = wxFormula.safe_float(param['Hi']['value'] )
            param['Th']['value'] = wxFormula.safe_float(param['Th']['value'] )
            param['Vh']['value'] = wxFormula.safe_float(param['Vh']['value'] )
            param['Vs']['value'] = wxFormula.safe_float(param['Vs']['value'] )
            param['Vr']['value'] = wxFormula.safe_float(param['Vr']['value'] )
        except KeyError as e:
            logging.debug("missing key %s",e)
    
        # compute and publish derived parameters
        logging.debug("derived parameters")
        try:
            # compute dewpoint from measured temp and RH
            dewpt = wxFormula.dewpoint(float(param['Ta']['value']), float(param['Ua']['value']))
            dewpt = round(dewpt,1)
            param['Td'] = {'value': dewpt, 'unit': 'C'}
        except:
            logging.warning("error computing dewpoint")
        try:
            # compute MSL pressure from station elevation and station pressure
            if(USE_GPS):
                MSLPressure = wxFormula.MSLP(float(param['Pa']['value']), float(current_gps['alt_egm2008'])-GPS_ANTENNA_OFFSET)
            else:
                MSLPressure = wxFormula.MSLP(float(param['Pa']['value']), float(WXT_ELEVATION))
            MSLPressure = round(MSLPressure,2)
        except:
            MSLPressure = None
            logging.warning("error computing MSL pressure")
    
        param['Pb'] = {'value': MSLPressure, 'unit': 'H'}
    
        if(USE_GPS):
            # add some gps parameters
            param['gps_time'] = current_gps['gps_time']
            param['lat'] = current_gps['lat']
            param['lon'] = current_gps['lon']
            param['alt_msl'] = current_gps['alt_msl']
            param['alt_egm2008'] = current_gps['alt_egm2008']
            param['alt_wgs84'] = current_gps['alt_wgs84']
            param['geo_sep'] = current_gps['geo_sep']
            param['geo_sep_egm2008'] = current_gps['geo_sep_egm2008']
            param['spd_kts'] = current_gps['spd_kts']
            param['course'] = current_gps['course']
            param['pitch'] = current_gps['pitch']
            param['roll'] = current_gps['roll']
            param['mag_heading'] = current_gps['mag_heading']
            param['true_heading'] = current_gps['true_heading']
            param['internal_pres'] = current_gps['internal_pres']
            param['internal_temp'] = current_gps['internal_temp']
            param['declination'] = current_gps['declination']
    
        try:    
            mqttString = 'wxt/{} {}'.format(WXT_SERIAL, json.dumps(param))
            logging.info("MQTT pub: %s",mqttString)
            client.publish('wxt/{}'.format(WXT_SERIAL), json.dumps(param))
        except:
            logging.error("MQTT pub: failure") 
    
        logging.debug("wait for next polling interval")
    
        if(USE_GPS):
            time.sleep(0.5)
     
# kick off server when the script is called
if __name__ == '__main__':
    main()

