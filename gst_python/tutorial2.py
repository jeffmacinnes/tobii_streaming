import sys
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, GLib


# initialize
Gst.init(None)

# create the elements
source = Gst.ElementFactory.make("videotestsrc", "source")
sink = Gst.ElementFactory.make("autovideosink", "sink")

# create empty pipeline
pipeline = Gst.Pipeline.new("test-pipeline")

# check to make sure all elements could be built
if not pipeline or not source or not sink:
	print 'Error: Not all elements could be created'
	sys.exit(1)

# build the pipeline
pipeline.add(source)
pipeline.add(sink)
if not source.link(sink):
	print 'Could not link sink to source'
	sys.exit(1)

# modify the source's parameters
source.set_property("pattern", 0)

# start playing
ret = pipeline.set_state(Gst.State.PLAYING)
if ret == Gst.StateChangeReturn.FAILURE:
	print 'Unable to set pipeline to PLAYING STATE'

# wait for EOS of error
bus = pipeline.get_bus()
msg = bus.timed_pop_filtered(
		Gst.CLOCK_TIME_NONE,
		Gst.MessageType.ERROR | Gst.MessageType.EOS
	)


# check if there's a message
if msg:
	t = msg.type 
	if t == Gst.MessageType.ERROR:
		err,dbg = msg.parse_error()
		print 'Error: ' + msg.src.get_name() + " " + err.message
		if dbg:
			print ('debugging info: ' + dbg)
	elif t == Gst.MessageType.EOS:
		print 'End of Stream Reached'
	else:
		print 'Unexpected Error arrived'

pipeline.set_state(Gst.State.NULL)
