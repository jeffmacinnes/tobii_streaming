import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, GLib
import time


pipeline = None
bus = None
message = None



# initialize
Gst.init(None)

# build the pipeline
pipeline = Gst.parse_launch("playbin uri=https://www.freedesktop.org/software/gstreamer-sdk/data/media/sintel_trailer-480p.webm")


# start playing
pipeline.set_state(Gst.State.PLAYING)

# wait until EOS or error
bus = pipeline.get_bus()
msg = bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)

# free resources
pipeline.set_state(Gst.State.NULL)


