#!/usr/bin/env python3

# Script to plot the waypoints, GFs and routes

import inspect
import os
import sqlite3
import sys

import folium


# def log_error():
#     print("Error: " + inspect.currentframe().f_code.co_name + "()")


class Route:
    def __init__(self, cfg):
        try:
            self.db = sqlite3.connect('asdo_config.db')
            self.load_data()
        except Exception as e:
            print("Error: sqlite3 connect failed: " + repr(e))
            sys.exit(1)

    def load_data(self):
        try:
            c = self.db.cursor()
            self.waypoints = {}
            self.odometry = {}

            # select the waypoint info from DB
            for wp in c.execute("select waypoint_name, waypoint_lat, waypoint_long, waypoint_radius from waypoint "
                                "order by waypoint_name asc"):
                wp_name, lat, lng, r = wp
                self.waypoints[wp_name.lower()] = (lat, lng, r)

        except Exception as e:
            print(e)
            print("You need a valid asdo_config.db in pwd: " + os.getcwd())
            raise

    def plot_waypoints(self, map):
        for wp in self.waypoints:
            lat, lng, r = self.waypoints[wp]

            # Add wp marker to the map
            folium.Marker([lat, lng], popup=wp + ", gf=" + str(r) + "m").add_to(map)
            folium.Circle((lat, lng), radius=r, color='red').add_to(map)

    def init_map(self):
        # Centre the map on the central wp location
        gps = list(self.waypoints.values())

        lat_mean = sum(v[0] for v in gps) / float(len(gps))
        lng_mean = sum(v[1] for v in gps) / float(len(gps))
        lat_range = (min(gps, key=lambda item: item[0])[0],
                     max(gps, key=lambda item: item[0])[0])
        lng_range = (min(gps, key=lambda item: item[1])[1],
                     max(gps, key=lambda item: item[1])[1])

        map = folium.Map(prefer_canvas=True, zoom_start=10, location=(lat_mean, lng_mean))

        return map

    def wp_valid(self, wp, to, direction):
        if wp not in self.waypoints:
            print("Error: WP '" + wp + "' unknown")
            return False
        if to not in self.waypoints:
            print("Error: " + wp + ": " + direction.upper() + " '" + to + "' unknown")
            return False

    def plot_routes(self, map):
        c = self.db.cursor()
        self.routes = {}
        self.routes_up = []
        self.routes_down = []

        # Read (lowercase wp) routes into up/down arrays
        for route in c.execute("select waypoint_name, up_station_name, up_distance, down_station_name, "
                               "down_distance from route order by waypoint_name asc"):
            try:
                wp_name, up, up_dist, down, down_dist = route
                [wp_name, up, down] = [x.lower() for x in (wp_name, up, down)]
            except Exception as e:
                print("sql route")
                print(e)
                continue

            if up and up.strip():
                self.routes_up.append((wp_name, up))
            elif down and down.strip():
                self.routes_down.append((wp_name, down))
            else:
                print("Error with route: '" + route + "'")

        for r in self.routes_up:
            wp, up = r
            if not self.wp_valid(wp, up, "UP"):
                continue

            if (up, wp) in self.routes_down:
                self.routes_down.remove((up, wp))
                folium.PolyLine([(self.waypoints[wp][:2], self.waypoints[up][:2])],
                                color="black",
                                weight=5,
                                fill_opacity=0.5,
                                opacity=1,
                                line_opacity=0.5,
                                tooltip=wp + " <-> " + up
                                ).add_to(map)
            else:
                folium.PolyLine([(self.waypoints[wp][:2], self.waypoints[up][:2])],
                                color="green",
                                weight=5,
                                fill_opacity=0.5,
                                opacity=1,
                                line_opacity=0.5,
                                tooltip=wp + " UP " + up
                                ).add_to(map)

        for r in self.routes_down:
            wp, down = r
            if not self.wp_valid(wp, down, 'DOWN'):
                continue

            folium.PolyLine([(self.waypoints[wp][:2], self.waypoints[down][:2])],
                            color="yellow",
                            weight=5,
                            fill_opacity=0.5,
                            opacity=1,
                            line_opacity=0.5,
                            tooltip=wp + " DOWN " + down
                            ).add_to(map)


def show_help():
    print("Usage:")
    print(os.path.basename(__file__))
    print("Reads the asdo_config.db file and plots the wp and routes in a map")
    print("")


def main(argv):
    show_help()

    r = Route('')

    map = r.init_map()

    r.plot_routes(map)
    r.plot_waypoints(map)

    map.save('map.html')
    print("\nDone: open map.html in browser")


if __name__ == "__main__":
    main(sys.argv[1:])
