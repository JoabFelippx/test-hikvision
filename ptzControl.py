from is_msgs.camera_pb2 import CameraConfig, CameraConfigFields, PTZControl
from is_msgs.common_pb2 import FieldSelector

from is_wire.core import Message, Subscription, Logger
from streamChannel import StreamChannel

import socket

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

def get_ptz_config(channel, subscription, topic):
    """
    Obtém a configuração atual da câmera, incluindo PTZ (Pan, Tilt, Zoom).
    
    Args:
        channel (Channel): Canal de comunicação com o broker.
        subscription (Subscription): Subscription ativa.
        cam_id (int): ID da câmera.

    Returns:
        dict: Dicionário com as informações de PTZ e outras configurações, ou None se falhar.
    """
    selector = FieldSelector(fields=[CameraConfigFields.Value("ALL")])
    
    # Envia a requisição
    channel.publish(
        Message(content=selector, reply_to=subscription),
        topic=topic
    )
    
    try:
        reply = channel.consume(timeout=3.0)
        config = reply.unpack(CameraConfig)

        ptz_info = {
            "ptz_absolute": {
                "x": config.ptzcontrol.absolute.x,
                "y": config.ptzcontrol.absolute.y,
                "z": config.ptzcontrol.absolute.z
            },
            "ptz_step": {
                "x": config.ptzcontrol.step.x,
                "y": config.ptzcontrol.step.y,
                "z": config.ptzcontrol.step.z
            },
            "zoom": config.camera.zoom.ratio,
            "brightness": config.camera.brightness.ratio,
            "saturation": config.camera.saturation.ratio,
            "sharpness": config.camera.sharpness.ratio,
            "white_balance_bu": config.camera.white_balance_bu.ratio,
            "white_balance_rv": config.camera.white_balance_rv.ratio,
            "resolution": {
                "width": config.image.resolution.width,
                "height": config.image.resolution.height
            },
            "fps": config.sampling.frequency.value,
            "channel_id": config.channel_id.value,
            "stream_channel_id": config.stream_channel_id.value,
        }

        # print(f"RPC Status: {reply.status}")
        # print("PTZ Config:", ptz_info)
        return ptz_info

    except socket.timeout:
        print("No reply :(")
        return None
    
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


cam_id = 6

set_topic = f"CameraGateway.{cam_id}.SetConfig"
get_topic = f"CameraGateway.{cam_id}.GetConfig"

broker_uri = "amqp://guest:guest@10.10.2.211:30000"
channel = StreamChannel(uri=broker_uri)

subscription = Subscription(channel)

cam_infos = get_ptz_config(channel, subscription, get_topic)

x = cam_infos["ptz_absolute"]["x"]
y = cam_infos["ptz_absolute"]["y"]
focal = cam_infos["zoom"]

print("Current PTZ Config:")
print(f"X: {x}, Y: {y}, Focal Length: {focal}")

print("Press arrow keys to move the camera, 'i' to zoom in, 'o' to zoom out. Press 'q' to quit.")
while True:

    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if keys[pygame.K_LEFT]:
            x -= 100
            send_ptz_config(channel, set_topic, x, y, focal)
            print('camera x:', x)
        if keys[pygame.K_RIGHT]:
            x += 100
            if x > 3600:
                x = 3600
            send_ptz_config(channel, set_topic, x, y, focal)
            print('camera x:', x)
        if keys[pygame.K_DOWN]:
            y += 100
            send_ptz_config(channel, set_topic, x, y, focal)
            print('camera y:', y)
        if keys[pygame.K_UP]:
            y -= 100
            send_ptz_config(channel, set_topic, x, y, focal)
            print('camera y:', y)
        if keys[pygame.K_i]:
            focal += 10
            send_ptz_config(channel, set_topic, x, y, focal)
            print('camera focal:', focal)
        if keys[pygame.K_o]:
            focal -= 10
            send_ptz_config(channel, set_topic, x, y, focal)
            print('camera focal:', focal)
        if keys[pygame.K_q] or event.type == pygame.QUIT:
            print("Exiting...")
            pygame.quit()
            exit()

    window.fill(0)
    pygame.draw.rect(window, (255, 0, 0), rect)
    pygame.display.flip()
