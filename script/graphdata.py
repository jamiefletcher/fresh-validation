#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 James Fletcher
# All rights reserved.
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""Read weather data files (as csv) and format them into one JSON file.

Retrieves 24 hours of meteorological data for Toronto Pearson Airport
(YYZ) from: (1) the SENES WRF-NMM operational weather forecast model
            (2) the corresponding Environment Canada observing record

A single JSON file containing both datasets is produced, which feeds the
graphs on the SENES weather model validation website."""

# Version:    1.2.2
# Change Log:
# 28Feb2015 * Added functionality for parsing total precip csv files
# 21Feb2015 * Added error handling for output files to main()
# 04Feb2015 * Refactored csv parsing to be part of 'MetStation' class
# 03Feb2015 * Converted csv file lists to be part of a new object class
#             called 'MetStation'
#           * Added functionality for reading the precip type data files

import csv
import json
from datetime import datetime
#from pytz import timezone

class MetStation(object):
    def __init__(self, name, hourly_obs_file, hourly_fcst_file,
                 hourly_obs_precip_file, hourly_fcst_precip_file,
                 daily_obs_precip_file, daily_fcst_precip_file):
        """Create a new meteorological station"""
        self.name = name
        self.hourly_data_files = '', hourly_obs_file, hourly_fcst_file
        self.hourly_precip_files = '', hourly_obs_precip_file, hourly_fcst_precip_file
        self.daily_precip_files = '', daily_obs_precip_file, daily_fcst_precip_file

    def __str__(self):
        return self.name

    def get_name(self):
        return self.name

    def read_hourly_data(self):
        # Define data element IDs
        obs, forecast = 1, 2

        date = None
        air_temp = 'Air Temperature (°C)', [],[]
        rel_hum = 'Relative Humidity (%)', [],[]
        wind_dir  = 'Wind Direction (degrees)', [],[]
        wind_speed = 'Wind Speed (km/h)', [],[]
        stn_press = 'Station Pressure (kPa)', [],[]

        for i in (obs, forecast):
            n_line = 0
            with open(self.hourly_data_files[i]) as data_file:
                for row in data_file:
                    if n_line > 0:
                        column = row.split()
                        if not date:
                            date = datetime(int(column[0]), int(column[1]),
                                            int(column[2])).strftime('%B %d, %Y')
                        air_temp[i].append(round(float(column[4]),2))
                        rel_hum[i].append(round(float(column[5]),2))
                        wind_dir[i].append(round(float(column[6]),2))
                        wind_speed[i].append(round(float(column[7]),2))
                        stn_press[i].append(round(float(column[8]),2))
                    n_line += 1

        wind_freq = 'Wind Frequency (%)', \
                    get_wind_frequency(wind_dir[obs]), \
                    get_wind_frequency(wind_dir[forecast])

        return date, air_temp, rel_hum, wind_speed, stn_press, wind_freq

    def read_hourly_precip_type(self):
        # Define data element IDs
        obs, forecast = 1, 2

        rain = 'Rain', [],[]
        snow = 'Snow', [],[]

        for i in (obs, forecast):
            n_line = 0
            with open(self.hourly_precip_files[i]) as data_file:
                for row in data_file:
                    if n_line > 0:
                        column = row.split()
                        snow[i].append(int(column[1]))
                        rain[i].append(int(column[2]))
                    n_line += 1

        if len(rain[obs]) != len(snow[obs]) and \
           len(rain[forecast]) != len(snow[forecast]):
            raise ValueError('Mismatch in precipitation types.')

        precip_type = 'Precipitation Type', \
                      ['--' for i in rain[obs]], \
                      ['--' for i in rain[forecast]]

        for i in (obs, forecast):
            n_elements = len(precip_type[i])
            for p in xrange(n_elements):
                if rain[i][p] == 1 and snow[i][p] == 1:
                    precip_type[1][p] = 'Rain / Snow'
                elif rain[i][p] == 1:
                    precip_type[i][p] = 'Rain'
                elif snow[i][p] == 1:
                    precip_type[i][p] = 'Snow'

        return rain, snow, precip_type

    def read_daily_precip_total(self):
        # Define data element IDs
        obs, forecast = 1, 2

        total_precip = 'Total Precipitation (mm)', [],[]

        for i in (obs, forecast):
            n_line = 0
            with open(self.daily_precip_files[i]) as data_file:
                for row in data_file:
                    if n_line > 0:
                        column = row.split()
                        if i == obs:
                            total_precip[i].append(round(float(column[5]),2))
                        elif i == forecast:
                            total_precip[i].append(round(float(column[3]),2))
                    n_line += 1

        return total_precip

def get_wind_frequency(directions):
    """Return the frequency distribution among the 16 wind sectors.

    Args:
      directions (list): wind directions    >=0 AND <=360 degrees

    Returns:
      wind_freq  (list): frequency distribution (as %) among the
                         16 wind sectors
    """
    # Define wind sectors
    sectors = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
               'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']

    # Initialize each sector count to 0
    wind_freq = [0 for s in sectors]

    for d in directions:
        if (d < 0) or (d > 360):
            raise ValueError('Wind direction out of range.')
        if d < 11.25:
            wind_freq[sectors.index('N')] += 1
        elif d < 33.75:
            wind_freq[sectors.index('NNE')] += 1
        elif d < 56.25:
            wind_freq[sectors.index('NE')] += 1
        elif d < 78.75:
            wind_freq[sectors.index('ENE')] += 1
        elif d < 101.25:
            wind_freq[sectors.index('E')] += 1
        elif d < 123.75:
            wind_freq[sectors.index('ESE')] += 1
        elif d < 146.25:
            wind_freq[sectors.index('SE')] += 1
        elif d < 168.75:
            wind_freq[sectors.index('SSE')] += 1
        elif d < 191.25:
            wind_freq[sectors.index('S')] += 1
        elif d < 213.75:
            wind_freq[sectors.index('SSW')] += 1
        elif d < 236.25:
            wind_freq[sectors.index('SW')] += 1
        elif d < 258.75:
            wind_freq[sectors.index('WSW')] += 1
        elif d < 281.25:
            wind_freq[sectors.index('W')] += 1
        elif d < 303.75:
            wind_freq[sectors.index('WNW')] += 1
        elif d < 326.25:
            wind_freq[sectors.index('NW')] += 1
        elif d < 348.75:
            wind_freq[sectors.index('NNW')] += 1
        else:
            wind_freq[sectors.index('N')] += 1

    count = len(directions)
    for s in sectors:
        wind_freq[sectors.index(s)] = \
            round(wind_freq[sectors.index(s)] / float(count) * 100, 2)

    return wind_freq

def unix_date_stamp(yyyy, mm, dd, hh=0, tz='UTC'):
    """Returns a UTC Unix date stamp based on an input date/time.

    Args:
      yyyy (int):  Year       >=1970
      mm   (int):  Month      >=1 AND <=12
      dd   (int):  Day        >=1 AND <=31
      hh   (int):  Hour       >=0 AND <=23  Default: 0
      tz   (str):  Time Zone                Default: 'UTC'

    Returns:
      ds (int): The coresponding Unix date stamp in milliseconds since
                1-Jan-1970 at 00:00 UTC.
    """
    epoch = datetime(1970, 1, 1)
    yyyy = int(yyyy)
    mm = int(mm)
    dd = int(dd)
    hh = int(hh)

    if yyyy < 1970 or yyyy > 9999:
        raise ValueError('ERROR! Year out of range')
    if mm < 1 or mm > 12:
        raise ValueError('ERROR! Month out of range')
    if dd < 1 or dd > 31:
        raise ValueError('ERROR! Day out of range')
    if hh < 0 or hh >23:
        raise ValueError('ERROR! Hour out of range')

    dt = datetime(yyyy, mm, dd, hh)

    if tz is not 'UTC':
        dt = timezone(tz).localize(dt)

    ds = dt.toordinal()*24 + hh - epoch.toordinal()*24
    return ds * 3600 * 1000

def main(testing = False):
    if testing:
        file_path = '/path/to/testing/'
        file_date = '18022015'
    else:
        # Observations data are available 1 day after they are recorded
        file_date = datetime.fromordinal(
                    datetime.now().toordinal() - 1
                    ).strftime('%d%m%Y')
        file_path = '/path/to/production/'

    # Define meteorological stations
    stations = []

    stn_toronto_pearson = MetStation('Toronto_Pearson',
        file_path + 'observations/hourly/archive/PA.obs.' + file_date,
        file_path + 'grads/archive/PA.fcst.' + file_date,
        file_path + 'observations/hourly/archive/PA.prec.obs.' + file_date + '.table',
        file_path + 'grads/archive/PA.precip.fcst.' + file_date + '.table',
        file_path + 'observations/daily/archive/PA.prec.dlyobs.' + file_date,
        file_path + 'grads/archive/PA.dlyprec.fcst.' + file_date
    )
    stations.append(stn_toronto_pearson)

    # Populate station data from csv files and write to JSON
    for s in stations:
        try:
            date, air_temp, rel_hum, wind_speed, stn_press, wind_freq = \
                s.read_hourly_data()
            rain, snow, precip_type = s.read_hourly_precip_type()
            total_precip = s.read_daily_precip_total()
        except Exception as e:
            print 'Error reading data files.', e
            return 1

        stn_data = []
        stn_data.append(air_temp)
        stn_data.append(rel_hum)
        stn_data.append(wind_speed)
        stn_data.append(stn_press)
        stn_data.append(wind_freq)
        stn_data.append(rain)
        stn_data.append(snow)
        stn_data.append(precip_type)
        stn_data.append(total_precip)

        # Dump paired obs/forecast data to a JSON file
        try:
            with open(file_path + 'script/' + s.get_name() + '.json', 'w') as outfile:
                json.dump((date, stn_data),
                          outfile,
                #          sort_keys = True,
                #          indent = 2,
                #          ensure_ascii = False
                )
            print datetime.now().strftime('%d-%b-%Y %H:%M:%S %Z'),
            print s.get_name() + '.json updated successfully.'
        except Exception as e:
            print 'Error writing JSON file.', e
            return 1
    return 0

if __name__ == '__main__':
    main()
