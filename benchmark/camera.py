import numpy as np
import time, json, random, string
from math import ceil, sin, cos
import paho.mqtt.client as mqtt
from utils import *

def rand_norm(mu, sig):
    res = random.gauss(mu, sig)
    return round(res, 3)

def euler2quat(x, y, z):
    quat = []
    quat += [sin(x/2)*cos(y/2)*cos(z/2) - cos(x/2)*sin(y/2)*sin(z/2)]
    quat += [cos(x/2)*sin(y/2)*cos(z/2) + sin(x/2)*cos(y/2)*sin(z/2)]
    quat += [cos(x/2)*cos(y/2)*sin(z/2) - sin(x/2)*sin(y/2)*cos(z/2)]
    quat += [cos(x/2)*cos(y/2)*cos(z/2) + sin(x/2)*sin(y/2)*sin(z/2)]
    return quat

class Camera(object):
    def __init__(self, name, scene, color):
        super().__init__()
        self.name = f"camera_{rand_num(4)}_{name}"
        self.scene = scene
        self.pos = [0,3,0]
        self.rot = [0,0,0,0]
        self.color = color
        self.lats = []
        self.lat = None
        self.bytes_sent = 0
        self.bytes_recvd = 0
        self.sent = 0
        self.recvd = 0
        self.id = 0
        self.client = mqtt.Client(self.name, clean_session=True, transport="websockets")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def connect(self, broker, port):
        self.client.connect(broker, port)
        self.client.loop_start()

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

    def on_connect(self, client, userdata, flags, rc):
        client.subscribe(f"realm/s/{self.scene}/#")

    def on_message(self, client, userdata, message):
        msg = message.payload.decode()
        arena_json = json.loads(msg)
        self.bytes_recvd += len(msg)
        if arena_json["object_id"] == self.name:
            dt = (time_ms() - arena_json["timestamp"]) # ms
            self.lats += [dt] # ms
            self.lat = np.mean(self.lats)
            self.recvd += 1

    def get_avg_lat(self):
        return self.lat

    def get_bytes_sent(self):
        return self.bytes_sent

    def get_bytes_recvd(self):
        return self.bytes_recvd

    def get_packets_sent(self):
        return self.sent

    def get_packets_recvd(self):
        return self.recvd

    def move(self):
        self.pos[0] += rand_norm(0, 0.1)
        self.pos[1] += rand_norm(0, 0.05)
        self.pos[2] += rand_norm(0, 0.1)

        self.rot = euler2quat(rand_norm(0, 6.28), rand_norm(0, 6.28), rand_norm(0, 6.28))

        arena_json = self.create_json()
        self.bytes_sent += len(json.dumps(arena_json)) # bytes
        self.sent += 1
        self.client.publish(f"realm/s/{self.scene}/{self.name}", arena_json)

    def create_json(self):
        res = {}
        res["object_id"] = self.name
        res["action"] = "create"
        res["type"] = "object"
        res["timestamp"] = time_ms()

        res["data"] = {}
        res["data"]["object_type"] = "camera"
        res["data"]["color"] = self.color

        res["data"]["position"] = {}
        res["data"]["position"]["x"] = self.pos[0]
        res["data"]["position"]["y"] = self.pos[1]
        res["data"]["position"]["z"] = self.pos[2]

        res["data"]["rotation"] = {}
        res["data"]["rotation"]["x"] = self.rot[0]
        res["data"]["rotation"]["y"] = self.rot[1]
        res["data"]["rotation"]["z"] = self.rot[2]
        res["data"]["rotation"]["w"] = self.rot[3]

        return json.dumps(res)