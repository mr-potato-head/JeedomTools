#!/usr/bin/python

""" Retrieve GET request from Jeedom and forward them to InfluxDB V2"""

import urllib
import time
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client .client.write_api import SYNCHRONOUS

__author__ = "Jonathan Neuhaus, Guilhem Guyonnet"
__copyright__ = "Copyright 2021"
__license__ = "MIT License"
__version__ = "2.0.0"
__status__ = "Development"

###########################
#    SCRIPT SETTINGS
###########################
# All settings come from the following environment variables
# Set the listening port for GET request
LISTENING_PORT = 1234
# InfluxDB Server parameters
INFLUXDB_SERVER = '127.0.0.1'
INFLUXDB_PORT = 8086
INFLUXDB_ORG = 'JEEDOM'
INFLUXDB_TOKEN = 'admin-token'
INFLUXDB_BUCKET = 'jeedom'
###########################

def resolv_settings():
    if "LISTENING_PORT" in os.environ:
        print('coucou')
        global LISTENING_PORT
        LISTENING_PORT = int(os.environ['LISTENING_PORT'])
    if "INFLUXDB_SERVER" in os.environ:
        global INFLUXDB_SERVER
        INFLUXDB_SERVER = os.environ['INFLUXDB_SERVER']
    if "INFLUXDB_PORT" in os.environ:
        global INFLUXDB_PORT
        INFLUXDB_PORT = int(os.environ['INFLUXDB_PORT'])
    if "INFLUXDB_ORG" in os.environ:
        global INFLUXDB_ORG
        INFLUXDB_ORG = os.environ['INFLUXDB_ORG']
    if "INFLUXDB_TOKEN" in os.environ:
        global INFLUXDB_TOKEN
        INFLUXDB_TOKEN = os.environ['INFLUXDB_TOKEN']
    if "INFLUXDB_BUCKET" in os.environ:
        global INFLUXDB_BUCKET
        INFLUXDB_BUCKET = os.environ['INFLUXDB_BUCKET']

def display_settings():
    print("LISTENING_PORT: " + str(LISTENING_PORT))
    print("INFLUXDB_SERVER: " + INFLUXDB_SERVER)
    print("INFLUXDB_PORT: " + str(INFLUXDB_PORT))
    print("INFLUXDB_ORG: " + str(INFLUXDB_ORG))
    print("INFLUXDB_TOKEN: **********************")
    print("INFLUXDB_BUCKET: " + INFLUXDB_BUCKET)

# This class will handles any incoming request from jeedom
# Request expected (Jeedom Push URL)
# > http://IP_FROM_SERVER:PORT_NUMBER/updateData?name=#cmd_name#&cmd_id=#cmd_id#&val=#value#&location=salon

class JeedomHandler(BaseHTTPRequestHandler):
    """ Handle Jeedom > InfluxDB Requests """

    # Handler for the GET requests
    def do_GET(self):
        # Part 1: Get the correct GET request from jeedom
        try:
            parsed_url = urllib.parse.urlparse(self.path)
            query = urllib.parse.parse_qs(parsed_url.query)

            # Display the query array after parsing (can be useful for debug)
            print(query)

            # Extract the value, the name and the location + add current time
            try:
                val=query["val"][0]
                try:
                    val = float(query["val"][0])
                except:
                    val = query["val"][0]
                name = query["name"][0]
                name = urllib.parse.unquote(name)
                location = query["location"][0]
                act_time = time.time() * 1000000000
            except:
                print('no value in url')
                return
        except:
            print("URL Parsing error: ", sys.exc_info()[0])
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            return

        # Part 2: Write Data to InfluxDB
        if val !='':
            # Prepare point and send it to influx DB
            client = InfluxDBClient(url="http://"+INFLUXDB_SERVER+":"+str(INFLUXDB_PORT)+"/", token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
            write_api = client.write_api(write_options=SYNCHRONOUS)
            point = Point(name).tag("location", location).field("value", val)
            write_api.write(bucket="jeedom", record=[point])
            client.close()

            # Send valid http response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
        return


######################
# ENTRY POINT
######################

if __name__ == '__main__':

    """ Start Jeedom-InfluxDB bridge """
    try:
        # Get and check settings
        resolv_settings()

        # Display settings that will be used
        display_settings()

        # Start the web server to handle the request
        server = HTTPServer(('', LISTENING_PORT), JeedomHandler)
        print('Started Jeedom-InfluxDB bridge on port ', LISTENING_PORT)

        # Wait forever for incoming http requests
        server.serve_forever()

    except KeyboardInterrupt:
        print('^C received, shutting down the Jeedom-InfluxDB bridge ')
        server.socket.close()