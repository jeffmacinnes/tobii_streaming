"""
Goals: 
-open socket connection with glasses.
-send "keep alive messages" to start UDP video stream
-bind UDP stream from socket to Gstream Pipeline
-show feed from glasses
""" 

import sys
import gi
import socket
import signal
import threading
import time

gi.require_version('Gst', '1.0')
from gi.repository import Gst, Gtk, GObject, GLib, Gio
Gst.debug_set_active(True)
Gst.debug_set_default_threshold(4)

# needed for window.get_xid(), xvimagesink.set_window_handle()
from gi.repository import GdkX11, GstVideo


# GLASSES_IP = "fd93:27e0:59ca:16:76fe:48ff:fe05:1d43" # IPv6 address scope global
#GLASSES_IP = "10.46.16.86"  # IPv4 address
GLASSES_IP = "192.168.71.50"
PORT = 49152

# initialize
GObject.threads_init()
Gst.init(None)

# Keep-alive message content used to request live data and live video streams
KA_DATA_MSG = "{\"type\": \"live.data.unicast\", \"key\": \"some_GUID\", \"op\": \"start\"}"
KA_VIDEO_MSG = "{\"type\": \"live.video.unicast\", \"key\": \"some_other_GUID\", \"op\": \"start\"}"


# create UDP socket
def mksock(peer):
	iptype = socket.AF_INET
	if ':' in peer[0]:
		iptype = socket.AF_INET6
	return socket.socket(iptype, socket.SOCK_DGRAM)

# send keep alive message
def send_keepalive_msg(socket, msg, peer):
	while running:
		#print 'Sending ' + msg + ' to target ' + peer[0] + ' socket no: ' + str(socket.fileno()) + '\n'
		socket.sendto(msg, peer)
		time.sleep(1)

# signal handler
def signal_handler(signal, frame):
	stop_sending_msg()
	sys.exit(0)

def stop_sending_msg():
	global running
	running = False

# Class for video player
class VideoPlayer:
	def __init__(self, vidSocket):
		
		# read in the socket
		self.vidSocket = vidSocket

		# set up the drawing area
		self.window = Gtk.Window()
		self.window.connect('destroy', self.quit)
		self.window.set_default_size(800,450)

		self.drawingarea = Gtk.DrawingArea()
		self.window.add(self.drawingarea)

		# Create the GStreamer Pipeline
		self.pipeline = Gst.Pipeline()

		# Create pipeline elements 
		self.udpsrc = Gst.ElementFactory.make('udpsrc', 'udpsrc')
		self.pipeline.add(self.udpsrc)
		self.udpsrc.set_property('socket', Gio.Socket().new_from_fd(self.vidSocket.fileno()))

		self.queue = Gst.ElementFactory.make('queue', 'queue')
		self.pipeline.add(self.queue)

		self.avdec_h264 = Gst.ElementFactory.make('avdec_h264', None)
		self.pipeline.add(self.avdec_h264)

		self.videoconvert = Gst.ElementFactory.make('videoconvert', None)
		self.pipeline.add(self.videoconvert)

		self.xvimagesink = Gst.ElementFactory.make('xvimagesink', 'videosink')
		self.pipeline.add(self.xvimagesink)

		# link all pipeline elements that can be linked without a connection
		self.udpsrc.link(self.queue)

		# end of videopipeline
		self.queue.link(self.avdec_h264)
		self.avdec_h264.link(self.videoconvert)
		self.videoconvert.link(self.xvimagesink)

		# Create bus to get events from GStreamer pipeline
		self.bus = self.pipeline.get_bus()
		self.bus.add_signal_watch()
		self.bus.connect('message::error', self.on_error)

		# This is needed to make the video output in the drawing area
		self.bus.enable_sync_message_emission()
		self.bus.connect('sync-message::element', self.on_sync_message)


	def run(self):
		self.window.show_all()

		# you need to get the xid after window.show_all
		self.xid = self.drawingarea.get_property('window').get_xid()

		# set player playing
		self.pipeline.set_state(Gst.State.PLAYING)
		Gtk.main()

	def quit(self, window):
		self.pipeline.set_state(Gst.State.NULL)
		Gtk.main_quit()

	def demux_added(self, element, pad):
		string = pad.query_caps(None).to_string()
		print string
		if string.startswith('video/'):
			print 'linking video queue to decoder'
			pad.link(self.buffer.get_static_pad("sink"))

	def on_sync_message(self, bus, msg):
		if msg.get_structure().get_name() == 'prepare-window-handle':
			print 'prepare window handle'
			msg.src.set_property('force-aspect-ratio', True)
			msg.src.set_window_handle(self.xid)

	def on_error(self, bus, msg):
		print msg.parse_error()


# init RUNNING var
running = True


### Main program
if __name__ == "__main__":
	signal.signal(signal.SIGINT, signal_handler)

	# define ip/port tuple for glasses socket
	peer = (GLASSES_IP, PORT)

	# create data socket
	data_socket = mksock(peer)
	td = threading.Timer(0, send_keepalive_msg, [data_socket, KA_DATA_MSG, peer])
	td.daemon = True
	td.start()

	# create the socket to send video "keep alive" to glasses
	video_socket = mksock(peer)
	tv = threading.Timer(0, send_keepalive_msg, [video_socket, KA_VIDEO_MSG, peer])
	tv.daemon = True
	tv.start()

	#### create the Gstreamer object
	p = VideoPlayer(video_socket)
	p.run()

	startTime = time.time()
	print startTime
	
	while True:
		#read from video socket (works -- spits out binary)
		#data = video_socket.recv(1024)
		#print data

		#data, address = data_socket.recvfrom(1024)
		#print data

		if time.time()-startTime > 3:
			print 'here'
		
			# read live stream
			p.quit()
			stop_sending_msg()
			sys.exit(0)



	keepGoing = True
	while keepGoing:

		a = raw_input()
		print a
		keepGoing = False;

		stop_sending_msg()
		sys.exit(0)



