import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, Gtk

# needed for window.get_xid(), xvimagesink.set_window_handle()
from gi.repository import GdkX11, GstVideo

GObject.threads_init()
Gst.init(None)


# Class for video player
class VideoPlayer:
	def __init__(self):
		self.window = Gtk.Window()
		print type(self.window)
		self.window.connect('destroy', self.quit)
		self.window.set_default_size(800,450)

		self.drawingarea = Gtk.DrawingArea()
		self.window.add(self.drawingarea)

		# Create the GStreamer Pipeline
		#self.pipeline = Gst.Pipeline()
		self.player = Gst.ElementFactory.make("playbin", "player")


		# Create bus to get events from GStreamer pipeline
		self.bus = self.player.get_bus()
		self.bus.add_signal_watch()
		self.bus.connect('message::error', self.on_error)

		# This is needed to make the video output in the drawing area
		self.bus.enable_sync_message_emission()
		self.bus.connect('sync-message::element', self.on_sync_message)

		# Create Gstreamer Elements
		self.player.set_property("uri", "https://www.freedesktop.org/software/gstreamer-sdk/data/media/sintel_trailer-480p.webm")


	def run(self):
		self.window.show_all()

		# you need to get the xid after window.show_all
		self.xid = self.drawingarea.get_property('window').get_xid()

		# set player playing
		self.player.set_state(Gst.State.PLAYING)
		Gtk.main()

	def quit(self, window):
		self.player.set_state(Gst.State.NULL)
		Gtk.main_quit()

	def on_sync_message(self, bus, msg):
		if msg.get_structure().get_name() == 'prepare-window-handle':
			print 'prepare window handle'
			msg.src.set_property('force-aspect-ratio', True)
			msg.src.set_window_handle(self.xid)

	def on_error(self, bus, msg):
		print msg.parse_error()

testGst = VideoPlayer()
testGst.run()




