#!/usr/bin/env python3

# Script to plot the navMan status delta if greater than TIME_DELTA

import datetime
import folium
import json
import os
import re
import sys

TIME_DELTA = 2


def parse_line(line):
    # navMan lines have {} and datetime
    # {"application": "navMan", "latitude": 0, "longitude": 0, "odometer": 0, "confidence": 0, "ragCode": 1} 2022-02-09 00:00:01
    regex = re.compile('^.*({.*})\s+(.*$)')
    data = regex.search(line)
    (msg, created_at) = data.groups()
    return (msg, created_at)


time_prev = datetime.datetime.now() - datetime.timedelta(days=1)
time_prev = time_prev.replace(microsecond=0)

def time_diff(time_now):
    # Calc the diff in seconds between successive
    global time_prev

    fmt = '%Y-%m-%d %H:%M:%S'
    tstamp1 = datetime.datetime.strptime(str(time_prev), fmt)
    tstamp2 = datetime.datetime.strptime(time_now, fmt)

    return abs(tstamp2 - tstamp1).total_seconds()


def parse_log_file(map, eyebos_log='eyebos.log') -> object:
    global time_prev, TIME_DELTA

    with open(eyebos_log) as fp:
        line = fp.readline()
        while line:
            # {"application":"navMan","latitude":0,"longitude":0,"odometer":0,"confidence":0,"ragCode":1} 2022-02-09 00:00:01
            if "navMan" in line:
                # print("{}: {}".format(cnt, line.strip()))
                (msg, created) = parse_line(line)

                diff = time_diff(created)
                if (diff < 3600) and (diff > TIME_DELTA):
                    try:
                        gps = json.loads(msg)
                    except Exception as e:
                        print("Error: " + repr(e))
                        return

                    try:
                        lat = gps['latitude']
                        lng = gps['longitude']
                    except Exception as e:
                        print("Error: " + repr(e))

                    plot_timestamp(map, (lat, lng), str(created), diff)

                time_prev = created

            line = fp.readline()


def plot_timestamp(map, gps, time_str, diff):
    (lat, lng) = gps
    print(lat, lng, diff)
    try:
        # folium.Marker([lat, lng], popup=time_str, icon=folium.Icon(color='blue')).add_to(map)
        folium.Circle((lat, lng), tooltip=str(diff), radius=(100*diff), color='red').add_to(map)
    except Exception as e:
        print("Error: " + repr(e))


def show_help():
    print("Usage:")
    print(os.path.basename(__file__))
    print("""
Reads the eyebos.log file and plots circles where navMan msg detla is > TIME_DELTA
    
Select data with this command:
    mysql -uroot -peb eyebos_stadler -e \"SELECT data, created_at from unit_statuses where created_at > DATE_SUB(CURRENT_DATE(),INTERVAL 1 DAY)\" > eyebos.log
""")


def new_map():
    return folium.Map(prefer_canvas=True, zoom_start=10, location=(52.630886, 1.297355))


def main(argv):
    eyebos_log = argv[0] if len(argv) else 'eyebos.log'
    show_help()

    asdo_map = new_map()
    try:
        parse_log_file(asdo_map, eyebos_log)
    except Exception as e:
        print("Error: " + repr(e))
        sys.exit(1)

    map_web = 'map-' + eyebos_log + '.html'
    print("Saving to " + map_web)
    asdo_map.save(map_web)
    print("\nDone: open " + map_web + " in browser")


if __name__ == "__main__":
    main(sys.argv[1:])
