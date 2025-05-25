from is_msgs.camera_pb2 import CameraConfig, CameraConfigFields, PTZControl
from is_msgs.common_pb2 import FieldSelector
from google.protobuf.empty_pb2 import Empty

from is_wire.core import Message, Subscription, Logger
from streamChannel import StreamChannel

import pygame
pygame.init()

window = pygame.display.set_mode((300, 300))
clock = pygame.time.Clock()

rect = pygame.Rect(0, 0, 20, 20)
rect.center = window.get_rect().center

def create_ptz_config_msg(x, y, z):

    config = CameraConfig()

    config.ptzcontrol.absolute.x = x
    config.ptzcontrol.absolute.y = y
    config.ptzcontrol.absolute.z = z

    return config

def get_ptz_config(channel, topic):
    
    log = Logger(name="GetConfig-hikvision")
    
    subscription = Subscription(channel)
    subscription.subscribe(topic=topic)
    
    field = FieldSelector
    
    field.fields = "ALL"
    
    log.info("Getting current PTZ configuration")
    
    msg_get_ptz = Message(content=field, reply_to=subscription)
    
    a = channel.publish(msg_get_ptz, topic)
    
    print(a)
        
def send_ptz_config(channel, topic, x, y, z):
    log = Logger(name="SetConfig-hikvision")

    # Create a subscription to receive messages
    subscription = Subscription(channel)
    
    log.info("Sending message to set PTZ configuration")

    # Create a message to send
    msg_set_ptz = Message(content=create_ptz_config_msg(x, y, z), reply_to=subscription)

    # Send the message
    channel.publish(msg_set_ptz, topic)

    print(msg_set_ptz)



x = 0
y = 0
focal = 0

broker_uri = "amqp://guest:guest@10.10.2.211:30000"
channel = StreamChannel(uri=broker_uri)

get_ptz_config(channel, "CameraGateway.6.GetConfig")


topic = "CameraGateway.6.SetConfig"

print("Press arrow keys to move the camera, 'i' to zoom in, 'o' to zoom out. Press 'q' to quit.")
while True:

    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if keys[pygame.K_LEFT]:
            x -= 100
            send_ptz_config(channel, topic, x, y, focal)
            print('camera x:', x)
        if keys[pygame.K_RIGHT]:
            x += 100
            if x > 3600:
                x = 3600
            send_ptz_config(channel, topic, x, y, focal)
            print('camera x:', x)
        if keys[pygame.K_DOWN]:
            y += 100
            send_ptz_config(channel, topic, x, y, focal)
            print('camera y:', y)
        if keys[pygame.K_UP]:
            y -= 100
            send_ptz_config(channel, topic, x, y, focal)
            print('camera y:', y)
        if keys[pygame.K_i]:
            focal += 10
            send_ptz_config(channel, topic, x, y, focal)
            print('camera focal:', focal)
        if keys[pygame.K_o]:
            focal -= 10
            send_ptz_config(channel, topic, x, y, focal)
            print('camera focal:', focal)

    window.fill(0)
    pygame.draw.rect(window, (255, 0, 0), rect)
    pygame.display.flip()
