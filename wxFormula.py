#!/usr/bin/python3

import math

# convert station pressure to mean sea level pressure given
#   static pressure at station (hPa or mbar) and height above sea level (m)
#   station temperature in C
#   see: https://en.wikipedia.org/wiki/Barometric_formula
#  also formula (3.2) from https://www.wmo.int/pages/prog/www/IMOP/meetings/SI/ET-Stand-1/Doc-10_Pressure-red.pdf

def MSLP(staticPressure, height):

    P = staticPressure*100  # convert hPa to Pa
    Tb = 288.15     # standard temperature
    Lb = -0.0065    # standard temperature lapse rate (K/m)
    hb = 0          # height at bottom of layer b
    R = 8.3144598   # universal gas constant, J/(mol*K)
    g0 = 9.80665    # gravitational acceleration, m/s^2
    M = 0.0289644   # Molar mas of Earth's air, kg/mol
    
    # wikipedia
    exponent = (g0*M)/(R*Lb)
    base = Tb/(Tb+Lb*(height-hb))
    Pb = P / pow(base,exponent)

    #print("P: {:.2f}  Pb: {:.2f}".format(P,Pb))
    return (Pb/100)  # return pressure in hPa or mbar

def dewpoint(T, RH):
    return(243.04*(math.log(RH/100)+((17.625*T)/(243.04+T)))/(17.625-math.log(RH/100)-((17.625*T)/(243.04+T))))

def C2F(C):
    return(((float(C)*9)/5)+32)

def ms2mph(ms):
    return(float(ms)*2.236936)

def mm2in(mm):
    return(float(mm)*0.03937008)

def mbar2inhg(mbar):
    return(float(mbar)*0.02952998)


if (__name__ == "__main__"):
    staticPressure=977.0  # mbar
    height = 375.0        # meters
    print("Static pressure of {} mbar at {} meters is {:.1f} mbar at sea level".format(staticPressure,height,MSLP(staticPressure,height)))

    print("Temp: {}, RH: {} = dewpoint of {:.2f}".format(30,50,dewpoint(30,50)))

