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
import json
import paho.mqtt.client as mqtt
import wxFormula

LOCAL_BROKER_ADDRESS = '127.0.0.1'  # MQTT broker address
REMOTE_BROKER_ADDRESS = 'kennedy.tw'  # remote MQTT broker address
WXT_HOST = '10.0.0.72'  # The WXT serial server hostname or IP address
WXT_PORT = 2101         # The port used by the serial server
WXT_SERIAL = 'N3720229' # PTU S/N N3620062
WXT_ELEVATION = 375.0   # WXT sensor elevation in meters above MSL
WXT_POLLING_INTERVAL = 5  # seconds between polling

# now we define the callbacks to handle messages we subcribed to
def on_message_wxt(client, userdata, message):
    print("message received: {0}".format(str(message.payload.decode("ISO-8859-1"))))
    print("message topic: {0}".format(message.topic))
    print("message qos: {0}".format(message.qos))
    print("message retain flag: {0}".format(message.retain))
    command = message.payload.decode('ISO-8859-1')
    print('{}: MQTT sub: {}: {}'.format(time.asctime(), message.topic, command))
    command += '\r\n'
    try:
        s.send(command.encode('ISO-8859-1'))
    except:
        print("{}: MQTT command send to serial server failed".format(time.asctime()))

def on_message_gps(client, userdata, message):
    global gps_timeout
    global current_gps

    #print("message received: {0}".format(message.payload.decode("ISO-8859-1")))
    #print("message topic: {0}".format(message.topic))
    #print("message qos: {0}".format(message.qos))
    #print("message retain flag: {0}".format(message.retain))
    #print('{}: MQTT sub: {}: {}'.format(time.asctime(), message.topic, message.payload.decode('ISO-8859-1')))
    try:
        current_gps = json.loads(message.payload.decode('ISO-8859-1'))
        gps_timeout = time.time()
        #print('{}: MQTT sub: {}'.format(time.asctime(), json.dumps(current_gps)))
    except:
        print("{}: MQTT can't decode incoming gps message".format(time.asctime()))
        raise

class SocketIO(io.RawIOBase):
    def __init__(self, sock):
        self.sock = sock
    def read(self, sz=-1):
        if (sz == -1): sz=0x7FFFFFFF
        return self.sock.recv(sz)
    def seekable(self):
        return False

print ('{}: {}'.format(time.asctime(), "decode.py starts"))
while True:
   try:
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.settimeout(20)  # 1 second timeout for each line read
      s.connect( (WXT_HOST, WXT_PORT) )  # connect requires a tuple (x,y) as argument
      break
   except(ConnectionRefusedError):
      print("{}: {}".format(time.asctime(),"connection refused to WXT-536 serial server"))
      time.sleep(5)

file = SocketIO(s)
#file = open("test.out","r")

gps_timeout = 0  # last time gps arrived
current_gps = {'time': gps_timeout, 'gps_time': gps_timeout}

client = mqtt.Client('pbx-wxt')
client.on_message = on_message_wxt
client.connect(LOCAL_BROKER_ADDRESS)
client.loop_start()
client.subscribe('wxt/{}/cmd'.format(WXT_SERIAL))  # subscribe to command channel

client = mqtt.Client('pbx-gps-client')
client.on_message = on_message_gps
client.connect(LOCAL_BROKER_ADDRESS)
client.loop_start()
client.subscribe('gps/{}'.format(WXT_SERIAL))  # subscribe to command channel

time.sleep(1.1) # let gps load up a measurement
old_tick = 0

while True:
    param = {}
    line = ''

    if((time.time() - gps_timeout) < 1.1):  # did gps time advance?
        if( (WXT_POLLING_INTERVAL - (gps_timeout % WXT_POLLING_INTERVAL)) < 1.5) :  # is it almost time?
            sleepy = WXT_POLLING_INTERVAL - (gps_timeout % WXT_POLLING_INTERVAL) # YES it's time, sleep the last bit then poll sensor
            print ("FINAL SLEEPING {} *************************".format(sleepy))
            time.sleep(sleepy)
            param = {'time': current_gps['time']} # reset param; 'time' marks when poll sent
        else:
            if(old_tick != gps_timeout):
               print ("GPS TICK {} *****************************".format(gps_timeout))
               old_tick = gps_timeout
            time.sleep(0.1)  # NO, sleep 200ms and try again
            continue
    else:  # GPS time did not advance, check GPS timeout
        if((time.time() - gps_timeout)>3):  # new gps not seen, has it been too long?
            sleepy = WXT_POLLING_INTERVAL - (time.time() % WXT_POLLING_INTERVAL) # trigger on pc clock
            print("GIVING UP ON GPS {} *************************".format(sleepy))
            time.sleep(sleepy)
            param = {'time': int(time.time())} # reset params; 'time' marks when poll sent
        else:
            #print ("WAIT FOR GPS *******************************")
            time.sleep(0.1)  #no gps timeout yet, sleep 200ms and try again
            continue

    print("----- flushing socket at {}".format(time.asctime()));
    s.setblocking(False)
    while True:
       try:
          cruft = s.recv(0x7FFFFFFF).decode('ISO-8859-1')
          #print("cruft: " + cruft)  # flush input buffer
       except(BlockingIOError):
          #print("no cruft")
          break
    s.settimeout(WXT_POLLING_INTERVAL/2)
    print("----- sending 0R command");
    s.send(u'0R\r\n'.encode())  # send command to return all sentences
    print("+++++ reading sentences");
    param = {'time': int(time.time())} # reset params; timer marks when poll sent
    for index in range(4):  # read four lines of response (0R1,0R2,0R3,0R5)
       try:
          line=file.readline().decode('ISO-8859-1')
       except:
          print("{}: timeout reading from WXT-536".format(time.asctime()))
          break
       #print(line.strip())
       chunks = line.strip().split(',')
       chunks = chunks[1:]  # drop initial 0R[1235]
       for chunk in chunks:
          try:
            (label, content) = chunk.split('=',1)
            value = content[:-1]
            unit = content[-1]
            param[label] = {'value': value, 'unit': unit}
          except:
            print("bad chunk: " + chunk)
            break

    # compute and publish derived parameters
    print("----- derived parameters")
    try:
        # compute dewpoint from measured temp and RH
        dewpt = wxFormula.dewpoint(float(param['Ta']['value']), float(param['Ua']['value']))
        dewpt = float(int(dewpt*10))/10
        param['Td'] = {'value': dewpt, 'unit': 'C'}
    except:
        print("error computing dewpoint")
    try:
        # compute MSL pressure from station elevation and station pressure
        MSLPressure = wxFormula.MSLP(float(param['Pa']['value']), float(WXT_ELEVATION))
        MSLPressure = float(int(MSLPressure*10))/10
        param['Pb'] = {'value': MSLPressure, 'unit': 'H'}
    except:
        print("error computing MSL pressure")

    # add some gps parameters
    param['gps_time'] = current_gps['gps_time']
    param['lat'] = current_gps['lat']
    param['lon'] = current_gps['lon']
    param['alt_msl'] = current_gps['alt_msl']
    param['geo_sep'] = current_gps['geo_sep']
    param['spd_kts'] = current_gps['spd_kts']
    param['course'] = current_gps['course']
    param['pitch'] = current_gps['lat']
    param['roll'] = current_gps['roll']
    param['mag_heading'] = current_gps['mag_heading']
    param['true_heading'] = current_gps['true_heading']
    param['internal_pres'] = current_gps['internal_pres']
    param['internal_temp'] = current_gps['internal_temp']
    param['declination'] = current_gps['declination']

    try:    
        mqttString = 'wxt/{} {}'.format(WXT_SERIAL, json.dumps(param))
        print("MQTT pub: {}".format(mqttString))
        client.publish('wxt/{}'.format(WXT_SERIAL), json.dumps(param))
    except:
        print("MQTT pub: failure") 

    print("----- finished publishing at {}".format(time.asctime()));
    print("+++++ wait for next polling interval")
    time.sleep(0.5)
 

