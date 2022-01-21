#!/usr/bin/env python3

# Script to plot the waypoints, GFs and routes

import folium
import inspect
import os
from polycircles import polycircles
import simplekml
import sqlite3
import sys


def log_error():
    print("Err: " + inspect.currentframe().f_code.co_name + "()")


class Route:
    def __init__(self, cfg):
        try:
            self.db = sqlite3.connect('asdo_config.db')
            self.load_data()
            self.earth_radius = 6371000.0
        except Exception as e:
            print(repr(e))
            sys.exit(1)

    def load_data(self):
        try:
            c = self.db.cursor()
            self.waypoints = {}
            self.odometry = {}
            self.routes = {}

            for wp in c.execute("select waypoint_name, waypoint_lat, waypoint_long, waypoint_radius from waypoint"):
                self.waypoints[wp[0]] = (wp[1], wp[2], wp[3])

            for row in c.execute("select waypoint_name, up_station_name, up_distance, down_station_name, down_distance from route"):
                wp_name, up, up_dist, down, down_dist = row
                if wp_name in self.routes:
                    if up and up.strip():
                        self.routes[wp_name][0:2] = [up, up_dist]
                    else:

                        self.routes[wp_name][2:4] = [down, down_dist]
                else:
                    self.routes[wp_name] = list(row[1:])


        except Exception as e:
            print(e)
            print("You need a valid asdo_config.db in pwd: " + os.getcwd())
            raise

    def plot_waypoints(self, map):
      # self.plot_kml()

      for wp in self.waypoints:
        lat, lng, r = self.waypoints[wp]
        # print (lat, lng, r)
        folium.Marker([lat, lng], popup=wp + ", gf=" + str(r) + "m").add_to(map)
        folium.Circle((lat, lng), radius=r, color='red').add_to(map)
        # folium.Circle((lat, lng), radius=r*5, color='yellow').add_to(map)

      # print (lat_range, lng_range)


    def init_map(self):
        gps = list(self.waypoints.values())

        lat_mean = sum(v[0] for v in gps) / float(len(gps))
        lng_mean = sum(v[1] for v in gps) / float(len(gps))
        lat_range = (min(gps, key=lambda item: item[0])[0],
                     max(gps, key=lambda item: item[0])[0])
        lng_range = (min(gps, key=lambda item: item[1])[1],
                     max(gps, key=lambda item: item[1])[1])

        map = folium.Map(prefer_canvas=True, zoom_start=11, location=(lat_mean, lng_mean))

        return map

    def plot_routes(self, map):
        for d in 'down', 'up':
            for r in self.routes:
                print(r + ": " + str(self.routes[r]))

                x = self.routes[r][0:4]
                wp_up, up_dist, wp_down, down_dist = self.routes[r][0:4]
                try:
                    if d == 'up':
                        # If the up/down is valid, that plot between the points
                        if wp_up and wp_up.strip():
                            folium.PolyLine([(self.waypoints[r][:2], self.waypoints[wp_up][:2])],
                                            color="#FFD700",
                                            weight=10,
                                            line_opacity=0.5,
                                            tooltip=r + " >>up>> " + wp_up + ": " + str(up_dist) + "m"
                                            ).add_to(map)
                    else:
                        if wp_down and wp_down.strip():
                            folium.PolyLine([(self.waypoints[r][:2], self.waypoints[wp_down][:2])],
                                            color="#87CEEB",
                                            weight=30,
                                            fill_opacity=0.5,
                                            tooltip=r + " >>down>> " + wp_down + ": " + str(down_dist)
                                            ).add_to(map)
                except Exception as e:
                    lat, lng, r = self.waypoints[r]
                    folium.Circle((lat, lng), radius=50, color='Orange').add_to(map)
                    print("Error: plotting route data: " + str(r))
                    print(self.routes[r][0:4])


    def plot_kml(self):
        kml = simplekml.Kml()
        for w in self.waypoints:
            lat, lng, r = self.waypoints[w]
            # print(w, lng, lat)
            kml.newpoint(name=w, coords=[(lng, lat)])

            polycircle = polycircles.Polycircle(latitude=lat,
                                                longitude=lng,
                                                radius=r,
                                                number_of_vertices=36)
            pol = kml.newpolygon(name=w, outerboundaryis=polycircle.to_kml())
            pol.style.polystyle.color = simplekml.Color.changealphaint(200, simplekml.Color.green)
        kml.save("db_plot.kml")


def show_help():
    print("")
    print(os.path.basename(__file__) +
          ' -s <start_at> -e <go_to> [-d <direction>] [-p <points>]')
    print("")


def createPlacemark(kmlDoc, row, order):
    placemarkElement = kmlDoc.createElement('Placemark')
    extElement = kmlDoc.createElement('ExtendedData')
    placemarkElement.appendChild(extElement)

def main(argv):
    r = Route('')

    map = r.init_map()

    r.plot_routes(map)
    r.plot_waypoints(map)

    map.save('map.html')

    # try:
    #     r.move_between( start_at, go_to, direction, points )
    #     print(e)


if __name__ == "__main__":
    main(sys.argv[1:])
