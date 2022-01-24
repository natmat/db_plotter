#!/usr/bin/env python3

# Script to plot the waypoints, GFs and routes

import os
import sqlite3
import sys

import folium

colour_wp =         'blue'
colour_route_bi =   'black'
colour_route_down = 'red'
colour_route_up =   'green'

# def log_error():
#     print("Error: " + inspect.currentframe().f_code.co_name + "()")

class WayPoint:
    waypoints = {}

    @classmethod
    def insert(cls, wp):
        if wp.name not in cls.waypoints:
            cls.waypoints[wp.name] = (wp.lat, wp.lng, wp.r)
        else:
            print("Error: can't add duplicate wp: " + wp.name)

    def __init__(self, name, lat, lng, r):
        self.name = name
        self.lat = lat
        self.lng = lng
        self.r = r
        WayPoint.insert(self)

    @classmethod
    def get_centre(self):
        if len(WayPoint.waypoints) == 0:
            print("Error: no waypoints")
            sys.exit(1)

        gps = list(self.waypoints.values())
        lat_mean = sum(v[0] for v in gps) / float(len(gps))
        lng_mean = sum(v[1] for v in gps) / float(len(gps))
        return (lat_mean, lng_mean)

    @classmethod
    def get_range(cls):
        gps = list(cls.waypoints.values())
        lat_range = (min(gps, key=lambda item: item[0])[0],
                     max(gps, key=lambda item: item[0])[0])
        lng_range = (min(gps, key=lambda item: item[1])[1],
                     max(gps, key=lambda item: item[1])[1])
        return (lat_range, lng_range)

    @classmethod
    def plot_waypoints(cls, map):
        for wp in cls.waypoints:
            # Add wp marker to the map
            lat, lng, r = cls.waypoints[wp]
            folium.Marker([lat, lng], popup=wp + ", gf=" + str(r) + "m").add_to(map)
            folium.Circle((lat, lng), radius=r, color=colour_wp).add_to(map)

    @classmethod
    def exists(cls, name):
        return (name in cls.waypoints)


class Map (folium.folium.Map):
    def __init__(self, lat, lng):
        # Centre the map on the central wp location
        folium.Map(prefer_canvas=True, zoom_start=10, location=(lat, lng))


class Route:
    
    routes = {}
    routes_up = []
    routes_down = []
    
    def __init__(self, config):
        try:
            self.db = sqlite3.connect(config)
            self.load_data()
        except Exception as e:
            print("Error: sqlite3 connect failed: " + repr(e))
            sys.exit(1)

    def load_data(self):
        try:
            c = self.db.cursor()

            # select the waypoint info from DB
            for wp in c.execute("select waypoint_name, waypoint_lat, waypoint_long, waypoint_radius from waypoint "
                                "order by waypoint_name asc"):
                name, lat, lng, r = wp
                WayPoint(name, lat, lng, r)

        except Exception as e:
            print(e)
            print("You need a valid asdo_config.db in pwd: " + os.getcwd())
            raise

    def init_map(self):
        # Centre the map on the central wp location
        lat_mean, lng_mean = WayPoint.get_centre()
        map = folium.Map(prefer_canvas=True, zoom_start=10, location=(lat_mean, lng_mean))

        return map

    @classmethod
    def is_valid(cls, wp, to, direction):
        if not WayPoint.exists(wp):
            print("Error: WP '" + wp + "' unknown")
            return False
        if not WayPoint.exists(to):
            print("Error: " + wp + ": " + direction.upper() + " '" + to + "' unknown")
            return False
        return True

    def plot_routes(self, map):
        c = self.db.cursor()

        for route in c.execute("select waypoint_name, up_station_name, up_distance, down_station_name, "
                               "down_distance from route order by waypoint_name asc"):
            try:
                wp_name, up, up_dist, down, down_dist = route
            except Exception as e:
                print("sql route")
                print(e)
                continue

            if up and up.strip():
                Route.routes_up.append((wp_name, up))
            elif down and down.strip():
                Route.routes_down.append((wp_name, down))
            else:
                print("Error with route: '" + route + "'")

        for r in Route.routes_up:
            wp, up = r
            if not Route.is_valid(wp, up, "UP"):
                continue

            if (up, wp) in Route.routes_down:
                folium.PolyLine([(WayPoint.waypoints[wp][:2], WayPoint.waypoints[up][:2])],
                                color=colour_route_bi,
                                weight=5,
                                tooltip="[" + wp + "] UpDown [" + up + "]"
                                ).add_to(map)
            else:
                folium.PolyLine([(WayPoint.waypoints[wp][:2], WayPoint.waypoints[up][:2])],
                                color=colour_route_up,
                                weight=5,
                                tooltip="[" + wp + "] Up [" + up + "]"
                                ).add_to(map)

        for r in Route.routes_down:
            wp, down = r
            if not Route.is_valid(wp, down, 'DOWN'):
                continue

            if (down, wp) in Route.routes_up:
                continue

            folium.PolyLine([(WayPoint.waypoints[wp][:2], WayPoint.waypoints[down][:2])],
                            color=colour_route_down,
                            weight=5,
                            tooltip="[" + wp + "] Down [" + down + "]"
                            ).add_to(map)


def show_help():
    print("Usage:")
    print(os.path.basename(__file__))
    print("Reads the asdo_config.db file and plots the wp and routes in a map")
    print("")


def main(argv):
    show_help()

    route = Route('asdo_config.db')

    lat, lng = WayPoint.get_centre()
    map = folium.Map(prefer_canvas=True, zoom_start=10, location=(lat, lng))
    WayPoint.plot_waypoints(map)
    route.plot_routes(map)

    map.save('map.html')
    print("\nDone: open map.html in browser")


if __name__ == "__main__":
    main(sys.argv[1:])
