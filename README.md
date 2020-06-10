# wxt536
python code for Vaisala wxt536 decoding, MQTT publishing, and wunderground PWS updating

### decodeMod.py:
              connect to WXT-536 via a Digi portserver TS 4 MEI (ethernet serial device)
              poll for data every POLLING_INTERVAL seconds
              Compute MSL pressure from station pressure and altitude
              Construct a JSON string and publish to q MQTT server, topic wxt/SERIAL_NUMBER
              Accept commands to send to WXT-536 device on wxt/SERIAL_NUMBER/cmd
              set station altitude in this file
            
### jsonServer.py:
              subscribe to wxt/SERIAL_NUMBER and build python dict of current observations
              create http server on PORT_NUMBER and return observations as JSON
                
### pwsweather.py:
  subscribe to wxt/SERIAL_NUMBER
                publish observations to www.pwsweather.com every PUBLISHING_INTERVAL seconds
                set pwsweather ID and PASSWORD in this file
                
### wunderground.py:
  subscribe to wxt/SERIAL_NUMBER
                  publish observations to wunderground.com every PUBLISHING_INTERVAL seconds
                  set wunderground ID and PASSWORD in this file
                  
### wxFormula.py:
  all your favorite unit conversions, convert station pressure to MSL pressure, etc.

### wxt536.out:
  some sample data strings as read from wxt-536

### wxt.settings:
  notes on how to configure wxt-536 for ASCII mode
