import time
import socket
import threading
import signal
import sys
import gi
import time

gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import Gst
from gi.repository import GObject, GdkX11, GstVideo, Gio
Gst.init(None)

timeout = 1.0
running = True


# GLASSES_IP = "fd93:27e0:59ca:16:76fe:48ff:fe05:1d43" # IPv6 address scope global
GLASSES_IP = "10.46.16.86"  # IPv4 address
GLASSES_ID = "192.168.71.50"
PORT = 49152


# Keep-alive message content used to request live data and live video streams
KA_DATA_MSG = "{\"type\": \"live.data.unicast\", \"key\": \"some_GUID\", \"op\": \"start\"}"
KA_VIDEO_MSG = "{\"type\": \"live.video.unicast\", \"key\": \"some_other_GUID\", \"op\": \"start\"}"


# Gstreamer pipeline definition used to decode and display the live video stream
# PIPELINE_DEF = "udpsrc do-timestamp=true name=src blocksize=1316 closefd=false buffer-size=5600 !" \
#                "mpegtsdemux !" \
#                "queue !" \
#                "avdec_h264 max-threads=0 !" \
#                "videoconvert !" \
#                "xvimagesink name=video"

PIPELINE_DEF = "udpsrc do-timestamp=true name=src blocksize=1316 buffer-size=5600 !" \
               "mpegtsdemux !" \
               "queue !" \
               "avdec_h264 max-threads=0 !" \
               "videoconvert !" \
               "xvimagesink name=video"


# Create UDP socket
def mksock(peer):
    iptype = socket.AF_INET
    if ':' in peer[0]:
        iptype = socket.AF_INET6
    return socket.socket(iptype, socket.SOCK_DGRAM)


# Callback function
def send_keepalive_msg(socket, msg, peer):
    while running:
        print("Sending " + msg + " to target " + peer[0] + " socket no: " + str(socket.fileno()) + "\n")
        socket.sendto(msg, peer)
        time.sleep(timeout)


def signal_handler(signal, frame):
    stop_sending_msg()
    sys.exit(0)


def stop_sending_msg():
    global running
    running = False


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    peer = (GLASSES_IP, PORT)

    # Create socket which will send a keep alive message for the live data stream
    data_socket = mksock(peer)
    td = threading.Timer(0, send_keepalive_msg, [data_socket, KA_DATA_MSG, peer])
    td.start()

    # Create socket which will send a keep alive message for the live video stream
    video_socket = mksock(peer)
    tv = threading.Timer(0, send_keepalive_msg, [video_socket, KA_VIDEO_MSG, peer])
    tv.start()

    # Create gstreamer pipeline and connect live video socket to it
    pipeline = Gst.Pipeline()
    
    udpsrc = Gst.ElementFactory.make('udpsrc', 'src')
    udpsrc.set_property('socket', Gio.Socket().new_from_fd(video_socket.fileno()))
    pipeline.add(udpsrc)

    tsparse = Gst.ElementFactory.make('tsparse', None)
    pipeline.add(tsparse)

    demux = Gst.ElementFactory.make('tsdemux', None)
    pipeline.add(demux)

    queue = Gst.ElementFactory.make('queue', None)
    pipeline.add(queue)

    h264 = Gst.ElementFactory.make('avdec_h264', None)
    pipeline.add(h264)

    videoConvert = Gst.ElementFactory.make('videoconvert', None)
    pipeline.add(videoConvert)

    imagesink = Gst.ElementFactory.make('xvimagesink', None)
    pipeline.add(imagesink)

    udpsrc.link(tsparse)
    tsparse.link(demux)
    demux.link(queue)
    queue.link(h264)
    h264.link(videoConvert)
    videoConvert.link(imagesink)

    # print 'ere'
    # pipeline = None
    # try:
    #     pipeline = Gst.parse_launch(PIPELINE_DEF)
    # except Exception, e:
    #     print e
    #     stop_sending_msg()
    #     sys.exit(0)
    # print 'here'
    # #src = pipeline.get_by_name("src")
    # #src.set_property("sockfd", video_socket.fileno())

    pipeline.set_state(Gst.State.PLAYING)

    startTime = time.time()

    while running:
        # Read live data
        data, address = data_socket.recvfrom(1024)
        print (data)

        state_change_return, state, pending_state = pipeline.get_state(0)
        print state

        #if Gst.STATE_CHANGE_FAILURE == state_change_return:
        #    stop_sending_msg()
        #print time.time() - startTime
        if time.time()-startTime > 3:
        	stop_sending_msg()