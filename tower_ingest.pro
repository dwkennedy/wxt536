;+
; $Id: $
;
; Abstract:
;	This script reads in the tower data from the CLAMPS-2 system, and
;   ingests it into netCDF
;
; Author:
;	Dave Turner, NOAA/NSSL
;
;-
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
pro write_ncdf, outfile, secs, data, fields

  systime2ymdhms,secs,hour=hour,yy,mm,dd
  hour = (dd-dd(0))*24 + hour

  print,'  Creating the file '+outfile
  fid = ncdf_create(outfile, /clobber)
  dim = ncdf_dimdef(fid,'time',/unlimited)
  vid = ncdf_vardef(fid,'base_time',/long)
    ncdf_attput,fid,vid,'long_name','Time since 1/1/1970 at 00:00:00 UTC'
    ncdf_attput,fid,vid,'units','seconds'
  vid = ncdf_vardef(fid,'time_offset',/double,dim)
    ncdf_attput,fid,vid,'long_name','Time since base_time'
    ncdf_attput,fid,vid,'units','seconds'
  vid = ncdf_vardef(fid,'hour',/double,dim)
    ncdf_attput,fid,vid,'long_name','Time of day'
    ncdf_attput,fid,vid,'units','hour [UTC]'
  vid = ncdf_vardef(fid,'sfc_pres',/float,dim)
    ncdf_attput,fid,vid,'long_name','Surface pressure'
    ncdf_attput,fid,vid,'units','mb'
  vid = ncdf_vardef(fid,'sfc_temp',/float,dim)
    ncdf_attput,fid,vid,'long_name','Surface temperature'
    ncdf_attput,fid,vid,'units','C'
  vid = ncdf_vardef(fid,'sfc_rh',/float,dim)
    ncdf_attput,fid,vid,'long_name','Surface relative humidity'
    ncdf_attput,fid,vid,'units','%'
  vid = ncdf_vardef(fid,'sfc_wspd',/float,dim)
    ncdf_attput,fid,vid,'long_name','Surface wind speed'
    ncdf_attput,fid,vid,'units','m/s'
  vid = ncdf_vardef(fid,'sfc_wdir',/float,dim)
    ncdf_attput,fid,vid,'long_name','Surface wind direction'
    ncdf_attput,fid,vid,'units','degrees'
  vid = ncdf_vardef(fid,'rain_rate',/float,dim)
    ncdf_attput,fid,vid,'long_name','Surface rain rate'
    ncdf_attput,fid,vid,'units','mm/hr'
  vid = ncdf_vardef(fid,'lat',/float,dim)
    ncdf_attput,fid,vid,'long_name','GPS latitude'
    ncdf_attput,fid,vid,'units','degrees north'
  vid = ncdf_vardef(fid,'lon',/float,dim)
    ncdf_attput,fid,vid,'long_name','GPS longitude'
    ncdf_attput,fid,vid,'units','degrees east'
  vid = ncdf_vardef(fid,'alt',/float,dim)
    ncdf_attput,fid,vid,'long_name','GPS altitude'
    ncdf_attput,fid,vid,'units','m MSL'
  vid = ncdf_vardef(fid,'internal_pres',/float,dim)
    ncdf_attput,fid,vid,'long_name','Pressure inside trailer'
    ncdf_attput,fid,vid,'units','mb'
    ncdf_attput,fid,vid,'comment','reference value only; uncalibrated measurement'
  vid = ncdf_vardef(fid,'internal_temp',/float,dim)
    ncdf_attput,fid,vid,'long_name','Temperature inside trailer'
    ncdf_attput,fid,vid,'units','C'
    ncdf_attput,fid,vid,'comment','reference value only; uncalibrated measurement'
  vid = ncdf_vardef(fid,'roll',/float,dim)
    ncdf_attput,fid,vid,'long_name','Roll of the trailer'
    ncdf_attput,fid,vid,'units','degrees'
  vid = ncdf_vardef(fid,'pitch',/float,dim)
    ncdf_attput,fid,vid,'long_name','Pitch of the trailer'
    ncdf_attput,fid,vid,'units','degrees'
  vid = ncdf_vardef(fid,'heading',/float,dim)
    ncdf_attput,fid,vid,'long_name','Magnetic heading of the trailer'
    ncdf_attput,fid,vid,'units','degrees from north'
  ncdf_attput,fid,/global,'Data_source','CLAMPS-2 serial datastream ingest'
  ncdf_attput,fid,/global,'Author','Dave Turner, dave.turner@noaa.gov'
  ncdf_attput,fid,/global,'Warning','Wind speed direction needs offset applied '+$
  	'to account for the trailer heading -- this has not been applied to these data'
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
end
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
pro tower_ingest, filenames, date, indir, outdir, rootname

  pushd,indir
  files = file_search(filenames, count=count)
  if(count le 0) then begin
    print,'Error in tower_ingest: no data files found'
    popd
    return
  endif

  on_ioerror, keepgoing

  	; Loop over the different files, reading in the data
  tmpfile = 'tmpfile'
  for ii=0L,count-1 do begin
    print,'Reading file ',ii+1,' of ',count,format='(4x,A,I0,A,I0)'
    file_copy,files(ii),'tmpfile',/overwrite
    spawn,'wc -l '+tmpfile,result
    nlines = long(result(n_elements(result)-1))*10
    lines = replicate(' ',nlines)
    openr,lun,tmpfile,/get_lun
    readf,lun,lines
    keepgoing:
    free_lun,lun
    n = strlen(lines)
    foo = where(n gt 0, nfoo)
    if(nfoo le 0) then begin
      print,'Warning from tower_ingest: all data in file '+files(i)+' is missing'
      continue
    endif
    print,nfoo,' lines read in',format='(6x,I0,A)'
    lines = lines(foo)
    fchar = strmid(lines,0,1)
    foo = where(fchar eq '$', nfoo)
    if(nfoo le 0) then begin
      print,'Warning from tower_ingest: all data lines in file '+files(i)+' have bad fchar'
      continue
    endif
    print,nfoo,' lines read in',format='(6x,I0,A)'
    lines = lines(foo)

    	; Get the header of each line, as this will trigger different reading functions
    header = strmid(lines,1,5)

	; Now decode the various messages
	; Keep the indices from the file, as I will need those to
	; assign dates/times to the data from the met tower
    gps = where(header eq 'GPGGA' or header eq 'GPRMC', ngps)
    fields = ['yy','mm','dd','hh','nn','ss', $		; GPS messages
		'GPS_lat','GPS_lon','GPS_alt', $	; GPS messages
		'itemp','ipres','pitch','roll','magdir', $      ; Internal values
		'wdir','wspd','otemp','orh','opres', $		; Met station
		'svolt','hvolt','rintn','rdur','raccum']	; Met station

	; Allocate memory for the data, and fill it with missing values
    data = dblarr(n_elements(fields), ngps)
    data = data*0 - 999.

	; Loop over the different lines of data, filling in the arrays
    gidx = -1L
    for i=0L,n_elements(header)-1 do begin
      if(header(i) eq 'GPGGA') then begin
        parts = str_sep(lines(i),',')
	if(n_elements(parts) eq 15) then begin
	  hhmmss = long(parts(1))
	  lat    = double(parts(2))
	  latns  = parts(3)
	  lon    = double(parts(4))
	  lonew  = parts(5)
	  dq     = fix(parts(6))
	  alt    = float(parts(9))
	  altu   = parts(10)
	  goed   = float(parts(11))
	  	; Decode the hhmmss into hh/nn/ss
	  hh = hhmmss / 10000L
	  ns = hhmmss - hh*10000L
	  nn = ns / 100
	  ss = ns - nn*100
	  	; Decode the latitude/longitude information
	  tmp = lat
	  lat = fix(lat)/100 
	  lat = lat + (tmp-lat*100)/60.
	  if(latns eq 'S' or latns eq 's') then lat *= -1
	  tmp = lon
	  lon = fix(lon)/100 
	  lon = lon + (tmp-lon*100)/60.
	  if(lonew eq 'W' or lonew eq 'w') then lon *= -1
	  	; Get the true altitude
	  alt += goed
          if((dq eq 1 or dq eq 2) and (altu eq 'M' or altu eq 'm')) then begin
	    gidx += 1
	    data([3,4,5,6,7,8],gidx) = [hh,nn,ss,lat,lon,alt]
	  endif
	endif
      endif else if(header(i) eq 'GPRMC') then begin
        parts = str_sep(lines(i),',')
	if(n_elements(parts) eq 13) then begin
	  hhmmss = long(parts(1))
	  dq     = parts(2)
	  lat    = double(parts(3))
	  latns  = parts(4)
	  lon    = double(parts(5))
	  lonew  = parts(6)
	  ddmmyy = long(parts(9))
	  	; Decode the ddmmyy into yyyy/mm/dd
	  dd = ddmmyy / 10000L
	  my = ddmmyy - dd*10000L
	  mm = my / 100
	  yy = my - mm*100
	  yy += 2000
	  	; Decode the hhmmss into hh/nn/ss
	  hh = hhmmss / 10000L
	  ns = hhmmss - hh*10000L
	  nn = ns / 100
	  ss = ns - nn*100
	  	; Decode the latitude/longitude information
	  tmp = lat
	  lat = fix(lat)/100 
	  lat = lat + (tmp-lat*100)/60.
	  if(latns eq 'S' or latns eq 's') then lat *= -1
	  tmp = lon
	  lon = fix(lon)/100 
	  lon = lon + (tmp-lon*100)/60.
	  if(lonew eq 'W' or lonew eq 'w') then lon *= -1
          if(dq eq 'a' or dq eq 'A') then begin
	    gidx += 1
	    data([0,1,2,3,4,5,6,7],gidx) = [yy,mm,dd,hh,nn,ss,lat,lon]
	  endif
	endif
      endif else if(header(i) eq 'PCLMP') then begin
        parts = str_sep(lines(i),',')
	if(n_elements(parts) eq 6) then begin
	  iroll   = float(parts(1))
	  ipitch  = float(parts(2))
	  imagdir = float(parts(3))
	  ipres   = float(parts(4))
	  itemp   = float(parts(5))
	  data([9,10,11,12,13],gidx) = [itemp,ipres,ipitch,iroll,imagdir]
	endif
      endif else if(header(i) eq 'WIMWV') then begin
        parts = str_sep(lines(i),',')
	if(n_elements(parts) eq 6) then begin
	  wdir  = float(parts(1))
	  wspd  = float(parts(3))
	  wspdu = parts(4)
	  dq    = strmid(parts(5),0,1)
	  if((dq eq 'A' or dq eq 'a') and (wspdu eq 'M' or wspdu eq 'm')) then begin
	    data([14,15],gidx) = [wdir,wspd]
	  endif
	endif
      endif else if(header(i) eq 'WIXDR') then begin
        parts = str_sep(lines(i),',')
	if(n_elements(parts) eq 17) then begin
	  if(parts(1) eq 'C' and parts(5) eq 'U' and parts(9) eq 'U') then begin
	    svolt  = float(parts(6))
	    hvolt  = float(parts(10))
	    data([19,20],gidx) = [svolt,hvolt]
	  endif
	endif else if(n_elements(parts) eq 13) then begin
	  if(parts(1) eq 'C' and parts(5) eq 'H' and parts(9) eq 'P') then begin
	    atemp  = float(parts(2))
	    arh    = float(parts(6))
	    apres  = float(parts(10))
	    data([16,17,18],gidx) = [atemp,arh,apres]
	  endif
	endif else if(n_elements(parts) eq 25) then begin
	  if(parts(1) eq 'V' and parts(5) eq 'Z' and parts(9) eq 'R') then begin
	    racum  = float(parts(2)) 	; mm accumulation
	    rdur   = float(parts(6))    ; sec duration
	    rints  = float(parts(10))   ; mm/hr intensity
	    data([21,22,23],gidx) = [rints,rdur,racum]
	  endif
	endif else print,'Unknown number of parts in WIXDR: '+ $
			string(format='(I6,2x,I3)',i,n_elements(parts))
      endif else if(header(i) eq 'ulti-') then begin
      	foo = 0		; Do nothing here
      endif else begin
        print,'Warning from tower_ingest: this is a header that I do not know: '+header(i)
      endelse
    endfor

    	; Concatenate the data together
    if(ii eq 0) then ddata = data $
    else ddata = transpose([transpose(ddata),transpose(data)])
  endfor
  popd
  data = ddata

    	; If there is no time-of-day info, then the sample is missing and remove it
  hour = data(3,*) + data(4,*)/60. + data(5,*)/3600.
  foo = where(hour ge 0, nfoo)
  if(nfoo le 0) then begin
    stop,'This should not happen, I think'
  endif
  data = data(*,foo)
  hour = data(3,*) + data(4,*)/60. + data(5,*)/3600.
  ymd  = data(0,*)*10000L + data(1,*)*100 + data(2,*)
  hms  = data(3,*)*10000L + data(4,*)*100 + data(5,*)
  ymdhms2systime,data(0,*),data(1,*),data(2,*),data(3,*),data(4,*),data(5,*),secs

	; Let's fill in holes of the data, starting with the yy/mm/dd fields
  dhour = hour(1:n_elements(hour)-1) - hour(0:n_elements(hour)-2)
  foo = where(dhour lt 0, nfoo)
  sidx = 0L
  for j=0,nfoo-1 do begin
    eidx = foo(j)
    bar  = lindgen(eidx-sidx+1)+sidx
    feh  = where(data(0,bar) gt 0, nfeh)
    if(nfeh le 0) then stop,'wow -- I did not see this happening'
    data(0,bar) = data(0,bar(feh(0)))
    data(1,bar) = data(1,bar(feh(0)))
    data(2,bar) = data(2,bar(feh(0)))
    sidx = eidx+1
  endfor
  if(sidx lt n_elements(hour)-1) then begin
    eidx = n_elements(hour)-1
    bar  = lindgen(eidx-sidx)+sidx+1
    feh  = where(data(0,bar) gt 0, nfeh)
    if(nfeh le 0) then stop,'wow -- I did not see this happening'
    data(0,bar) = data(0,bar(feh(0)))
    data(1,bar) = data(1,bar(feh(0)))
    data(2,bar) = data(2,bar(feh(0)))
  endif

	; Select all of the data for the desired date
  foo = where(ymd eq date, nfoo)
  if(nfoo le 1) then begin
    print,'Error: Unable to find any samples for this date -- aborting'
    return
  endif
  ymd  = ymd(foo)
  hms  = hms(foo)
  secs = secs(foo)
  hour = hour(foo)
  data = data(*,foo)

  outfile = string(format='(A,A,A,A,I0,A,I6.6,A)', $
	outdir,'/',rootname,'.',ymd(0),'.',hms(0),'.cdf')
  write_ncdf, outfile, secs, data, fields



  return
end
