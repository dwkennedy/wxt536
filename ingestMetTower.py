#!/usr/bin/python3
"""
This is an module which reads met data in JSON
and writes surface, accelerometer, compass
and other data to a netCDF file.

Create CLAMPS2 surface data file using the netCDF Python API.
http://unidata.github.io/netcdf4-python/netCDF4/index.html

Modelled after Dave Turner's IDL program, tower_ingest.pro
except it reads JSON instead of raw strings from instruments

Doug Kennedy <doug.kennedy@noaa.gov> 20200609
"""

import time
import sys
import json
from netCDF4 import Dataset
from numpy import arange, dtype # array module from http://numpy.scipy.org

# create a new netcdf file and load in data (python dict containing obs)
def create(filename, data):
    # create new netCDF file for writing, initialize for met tower data and return handle
    #ncfile = Dataset(filename,'w',clobber=False) 
    ncfile = Dataset(filename,'w',clobber=True) 
    # assign global attributes
    ncfile.Data_source = "CLAMPS-2 serial datastream ingest"
    ncfile.Author = "Python3: Doug Kennedy, doug.kennedy@noaa.gov; IDL: Dave Turner, dave.turner@noaa.gov"
    ncfile.Warning = "Wind speed direction needs offset applied to account for the trailer heading -- this has not been applied to these data"
    ncfile.History = "Created " + time.asctime(time.gmtime()) + " UTC"

    # create Dimensions
    ncfile.createDimension("time", None)
  
    # create Variables and Attributes

    #vid = ncdf_vardef(fid,'base_time',/long)
    #  ncdf_attput,fid,vid,'long_name','Time since 1/1/1970 at 00:00:00 UTC'
    #  ncdf_attput,fid,vid,'units','seconds'
    base_time = ncfile.createVariable("base_time",'i4')
    base_time.units = "seconds"
    base_time.long_name = "Time since 1/1/1970 at 00:00:00 UTC"

    #vid = ncdf_vardef(fid,'time_offset',/double,dim)
    #  ncdf_attput,fid,vid,'long_name','Time since base_time'
    #  ncdf_attput,fid,vid,'units','seconds'
    time_offset = ncfile.createVariable('time_offset','f8',('time'))
    time_offset.units = "seconds"
    time_offset.long_name = "Time since base_time"

    #vid = ncdf_vardef(fid,'hour',/double,dim)
    #  ncdf_attput,fid,vid,'long_name','Time of day'
    #  ncdf_attput,fid,vid,'units','hour [UTC]'
    hour = ncfile.createVariable('hour','f8',('time'))
    hour.units = "hour [UTC]"
    hour.long_name = 'Time of day'

    #vid = ncdf_vardef(fid,'sfc_pres',/float,dim)
    #  ncdf_attput,fid,vid,'long_name','Surface pressure'
    #  ncdf_attput,fid,vid,'units','mb'
    sfc_pres = ncfile.createVariable('sfc_pres','f4',('time'))
    sfc_pres.units = "mb"
    sfc_pres.long_name = 'Surface pressure'

    #vid = ncdf_vardef(fid,'sfc_temp',/float,dim)
    #  ncdf_attput,fid,vid,'long_name','Surface temperature'
    #  ncdf_attput,fid,vid,'units','C'
    sfc_temp = ncfile.createVariable('sfc_temp','f4',('time'))
    sfc_temp.units = "C"
    sfc_temp.long_name = 'Surface temperature'

    #vid = ncdf_vardef(fid,'sfc_rh',/float,dim)
    #  ncdf_attput,fid,vid,'long_name','Surface relative humidity'
    #  ncdf_attput,fid,vid,'units','%'
    sfc_rh = ncfile.createVariable('sfc_rh','f4',('time'))
    sfc_rh.units = "%"
    sfc_rh.long_name = 'Surface relative humidity'

    #vid = ncdf_vardef(fid,'sfc_wspd',/float,dim)
    #  ncdf_attput,fid,vid,'long_name','Surface wind speed'
    #  ncdf_attput,fid,vid,'units','m/s'
    sfc_wspd = ncfile.createVariable('sfc_wspd','f4',('time'))
    sfc_wspd.units = "m/s"
    sfc_wspd.long_name = 'Surface wind speed'

    #vid = ncdf_vardef(fid,'sfc_wdir',/float,dim)
    #  ncdf_attput,fid,vid,'long_name','Surface wind direction'
    #  ncdf_attput,fid,vid,'units','degrees'
    sfc_wdir = ncfile.createVariable('sfc_wdir','f4',('time'))
    sfc_wdir.units = "degrees"
    sfc_wdir.long_name = 'Surface wind direction'

    #vid = ncdf_vardef(fid,'rain_rate',/float,dim)
    #ncdf_attput,fid,vid,'long_name','Surface rain rate'
    #ncdf_attput,fid,vid,'units','mm/hr'
    rain_rate = ncfile.createVariable('rain_rate','f4',('time'))
    rain_rate.units = "mm/hr"
    rain_rate.long_name = 'Surface rain rate'

    #vid = ncdf_vardef(fid,'lat',/float,dim)
    #ncdf_attput,fid,vid,'long_name','GPS latitude'
    #ncdf_attput,fid,vid,'units','degrees north'
    lat = ncfile.createVariable('lat','f8',('time'))
    lat.units = "degrees north"
    lat.long_name = 'GPS latitude'

    #vid = ncdf_vardef(fid,'lon',/float,dim)
    #ncdf_attput,fid,vid,'long_name','GPS longitude'
    #ncdf_attput,fid,vid,'units','degrees east'
    lon = ncfile.createVariable('lon','f8',('time'))
    lon.units = "degrees east"
    lon.long_name = 'GPS longitude'

    alt = ncfile.createVariable('alt','f4',('time'))
    alt.units = "m MSL"
    alt.long_name = 'GPS altitude'

    internal_pres = ncfile.createVariable('internal_pres','f4',('time'))
    internal_pres.units = "mb"
    internal_pres.long_name = 'Pressure inside trailer'
    internal_pres.comment = 'reference value only; uncalibrated measurement'

    internal_temp = ncfile.createVariable('internal_temp','f4',('time'))
    internal_temp.units = "C"
    internal_temp.long_name = 'Temperature inside trailer'
    internal_temp.comment = 'reference value only; uncalibrated measurement'

    roll = ncfile.createVariable('roll','f4',('time'))
    roll.units = 'degrees'
    roll.long_name = 'Roll of the trailer'

    pitch = ncfile.createVariable('pitch','f4',('time'))
    pitch.units = 'degrees'
    pitch.long_name = 'Pitch of the trailer'

    heading = ncfile.createVariable('heading','f4',('time'))
    heading.units = 'degrees from north'
    heading.long_name = 'Magnetic heading of the trailer'

    bt = data[0]['time']
    base_time.assignValue( (data[0]['time']) )

    idx = 0
    for item in data:
        time_offset[idx] = data[idx]['time'] - bt
        (tm_year,tm_mon,tm_mday,tm_hour,tm_min,tm_sec,tm_wday,tm_yday,tm_isdst) \
              = time.gmtime(data[idx]['time'])
        hour[idx] = float(tm_hour)+float(tm_min)/60+float(tm_sec)/3600
        sfc_pres[idx] = data[idx]['Pa']['value']
        sfc_temp[idx] = data[idx]['Ta']['value']
        sfc_rh[idx] = data[idx]['Ua']['value']
        sfc_wdir[idx] = data[idx]['Dm']['value']
        sfc_wspd[idx] = data[idx]['Sm']['value']
        rain_rate[idx] = data[idx]['Ri']['value']
        lat[idx] = 35.240195
        lon[idx] = 97.421875
        alt[idx] = 375.0
        internal_pres[idx] = 0.0
        internal_temp[idx] = 0.0
        roll[idx] = 0.0
        pitch[idx] = 0.0
        heading[idx] = 0.0
        idx = idx+1
    return(ncfile)

"""
  # IDL code to stick readings into the netcdf file
 
  ncdf_control,fid,/endef
  ncdf_varput,fid,'base_time',long(secs(0))
  ncdf_varput,fid,'time_offset',secs-long(secs(0))
  ncdf_varput,fid,'hour',hour
  ncdf_varput,fid,'sfc_pres',float(reform(data(18,*)))
  ncdf_varput,fid,'sfc_temp',float(reform(data(16,*)))
  ncdf_varput,fid,'sfc_rh',float(reform(data(17,*)))
  ncdf_varput,fid,'sfc_wspd',float(reform(data(15,*)))
  ncdf_varput,fid,'sfc_wdir',float(reform(data(14,*)))
  ncdf_varput,fid,'rain_rate',float(reform(data(21,*)))
  ncdf_varput,fid,'lat',float(reform(data(6,*)))
  ncdf_varput,fid,'lon',float(reform(data(7,*)))
  ncdf_varput,fid,'alt',float(reform(data(8,*)))
  ncdf_varput,fid,'internal_pres',float(reform(data(10,*)))
  ncdf_varput,fid,'internal_temp',float(reform(data(9,*)))
  ncdf_varput,fid,'roll',float(reform(data(12,*)))
  ncdf_varput,fid,'pitch',float(reform(data(11,*)))
  ncdf_varput,fid,'heading',float(reform(data(13,*)))
  ncdf_close,fid
"""

def main(files):
    for input_filename in files:
        # read each file of json strings into array
        data = []
        print("opening {}".format(input_filename))
        file = open(input_filename, 'r')
        for line in file:
             data.append(json.loads(line))
        file.close()
        print("{} lines read".format(len(data)))
        (tm_year,tm_mon,tm_mday,tm_hour,tm_min,tm_sec,tm_wday,tm_yday,tm_isdst) = time.gmtime(data[0]['time'])
        output_filename = "clampsmetC2.a1.{:04d}{:02d}{:02d}.{:02d}{:02d}{:02d}.cdf".format(tm_year,tm_mon,tm_mday,tm_hour,tm_min,tm_sec)
        print("creating {}".format(output_filename))
        ncfile = create(output_filename, data)
        print("closing {}".format(output_filename))
        ncfile.close()

if (__name__ == '__main__'):
    if(len(sys.argv)<2):
        print("usage: {} [FILE]...".format(sys.argv[0]))
    else:
        main(sys.argv[1:])

