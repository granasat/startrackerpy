#!/usr/bin/env python3

from v4l2 import *
import fcntl
import mmap
import select
import time
import sys
from PIL import Image

vd = open('/dev/video0', 'rb+', buffering=0)


print(">> get device capabilities")
cp = v4l2_capability()
fcntl.ioctl(vd, VIDIOC_QUERYCAP, cp)

print("Draiver:", "".join((chr(c) for c in cp.driver)))
print("Name:", "".join((chr(c) for c in cp.card)))
print("Is a video capture device?", bool(cp.capabilities & V4L2_CAP_VIDEO_CAPTURE))
print("Supports read() call?", bool(cp.capabilities &  V4L2_CAP_READWRITE))
print("Supports streaming?", bool(cp.capabilities & V4L2_CAP_STREAMING))

print(">> device setup")
fmt = v4l2_format()
fmt.type = V4L2_BUF_TYPE_VIDEO_CAPTURE
fmt.fmt.pix.pixelformat = V4L2_PIX_FMT_GREY
fmt.fmt.pix.field = V4L2_FIELD_INTERLACED
fcntl.ioctl(vd, VIDIOC_G_FMT, fmt)  # get current settings
print("width:", fmt.fmt.pix.width, "height", fmt.fmt.pix.height)
print("pxfmt:", "V4L2_PIX_FMT_YUYV" if fmt.fmt.pix.pixelformat == V4L2_PIX_FMT_YUYV else fmt.fmt.pix.pixelformat)
print("pxfmt:", "V4L2_PIX_FMT_GREY5" if fmt.fmt.pix.pixelformat == V4L2_PIX_FMT_GREY else fmt.fmt.pix.pixelformat)
print("bytesperline:", fmt.fmt.pix.bytesperline)
print("sizeimage:", fmt.fmt.pix.sizeimage)
fcntl.ioctl(vd, VIDIOC_S_FMT, fmt)  # set whatever default settings we got before

print(">>> streamparam")  ## somewhere in here you can set the camera framerate
parm = v4l2_streamparm()
parm.type = V4L2_BUF_TYPE_VIDEO_CAPTURE
# parm.parm.capture.capability = V4L2_CAP_TIMEPERFRAME
fcntl.ioctl(vd, VIDIOC_S_PARM, parm) # Set params
fcntl.ioctl(vd, VIDIOC_G_PARM, parm) # Get params

ctrl = v4l2_control()
# ctrl.V4L2_CID_GAMMA = 400
fcntl.ioctl(vd, VIDIOC_G_CTRL, ctrl) # Set controls
fcntl.ioctl(vd, VIDIOC_S_CTRL, ctrl) # Set controls

print(">> init mmap capture")
req = v4l2_requestbuffers()
req.type = V4L2_BUF_TYPE_VIDEO_CAPTURE
req.memory = V4L2_MEMORY_MMAP
req.count = 1  # nr of buffer frames
fcntl.ioctl(vd, VIDIOC_REQBUFS, req)  # tell the driver that we want some buffers
print("req.count", req.count)

# setup a buffer
buf = v4l2_buffer()
buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE
buf.memory = V4L2_MEMORY_MMAP
buf.index = 0
fcntl.ioctl(vd, VIDIOC_QUERYBUF, buf)
mm = mmap.mmap(vd.fileno(), buf.length, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, offset=buf.m.offset)
fcntl.ioctl(vd, VIDIOC_QBUF, buf)

# Start streaming
buf_type = v4l2_buf_type(V4L2_BUF_TYPE_VIDEO_CAPTURE)
fcntl.ioctl(vd, VIDIOC_STREAMON, buf_type)

# Capture frame
buf = v4l2_buffer()
buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE
buf.memory = V4L2_MEMORY_MMAP
fcntl.ioctl(vd, VIDIOC_DQBUF, buf)  # get image from the driver queue

data = bytes(mm.read())
print(len(data))
image = Image.frombytes("L", (1280, 960), bytes(data))
image.save("v4l2_image.TIFF")

fcntl.ioctl(vd, VIDIOC_STREAMOFF, buf_type)
vd.close()
