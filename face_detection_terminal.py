#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2017 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author: Harald Seipp
#
import time
import json
import subprocess
# For simplicity we do not use SSL/TLS for the MQTT connection as it
# needs server and CA certificate to be set up plus requires TLS1.2 support
# which is not provided out-of-box for Ubuntu 14.04
#import ssl
import boto.s3.connection
import paho.mqtt.client as mqtt
from boto.s3.key import Key

# The callback for when a connection is established with the MQTT server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print("Publish message received from server")

# Set the variables for connecting to the IoT MQTT service
macAddress="nikeshlaptop20" # put in the Mac address of your Laptop here
print("MAC address: " + macAddress)
topic = "iot-2/evt/status/fmt/json"
username = "use-token-auth"
password = "uoaKW-qIUmcBxGw9rK" # put in your Watson IoT service auth-token
organization = "q9h8g4" # put in your Watson IoT service org_id
deviceType = "" # Change to whatever you defined in Watson IoT service

# Creating the client connection
# Set clientID and broker
clientID = "d:" + organization + ":" + deviceType + ":" + macAddress
broker = organization + ".messaging.internetofthings.ibmcloud.com"
mqttc = mqtt.Client(clientID)
# Register callback functions
mqttc.on_connect = on_connect
mqttc.on_message = on_message
# Set authentication values
mqttc.username_pw_set(username, password=password)
# Don't use TLS encryption here, just show how to do it.
#mqttc.tls_set("/home/localuser/ibm.crt", tls_version=ssl.PROTOCOL_TLSv1_2)
#mqttc.connect(host=broker, port=8883, keepalive=60)
mqttc.connect(host=broker, port=1883, keepalive=60)
# Publishing to IBM Internet of Things Foundation
mqttc.loop_start()

# Credentials for accessing the COS service
access_key = '' # Put your COS access key in here
secret_key = '' # Put your COS secret key in here
bucket = '' #  Put your COS bucket name in here

s3client = boto.connect_s3(
  aws_access_key_id = access_key,
  aws_secret_access_key = secret_key,
  host = 's3-api.us-geo.objectstorage.softlayer.net',
  #is_secure = False,
  calling_format = boto.s3.connection.OrdinaryCallingFormat(),
)

try:
    # Not using the loop over here to not exhaust the free API calls/day limit
    #while True:
        print "Taking photo:"
        # Put a temporary path on your local machine over here - for now, the filename
        # needs to be campic.jpg
        photo_taken = subprocess.check_output(['avconv', '-f', 'video4linux2',
                                               '-s', '640x480', '-i', '/dev/video0',
                                               '-ss', '0:0:2', '-frames', '1', '-y',
                                               '/tmp/campic.jpg'])
        print "Uploading file:"
        # Put a temporary path on your local machine over here - for now, the filename
        # needs to be campic.jpg
        testfile = open('/tmp/campic.jpg')
        # currently picture path is hardcoded and will be overwritten with each PUT
        # to save Object Storage space
        b = s3client.get_bucket(bucket)
        k = Key(b)
        k.key = 'campic.jpg'
        k.set_contents_from_file(testfile)
        testfile.close()

        msg = json.JSONEncoder().encode({"d":{"picture_name":"campic.jpg"}})
        mqttc.publish(topic, payload=msg, qos=0, retain=False)
        print "Message published"
        
        # don't send data more than once every 15 seconds to not quickly run into
        # free API calls/day (150) limitation
        #time.sleep(15)
        pass

# Cleanup at program termination (CTRL-C)
except KeyboardInterrupt:
    print "Termination signal received"

print "Waiting 5 seconds for messaging to complete..."
time.sleep(5)
