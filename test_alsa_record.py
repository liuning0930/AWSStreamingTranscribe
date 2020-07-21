import alsaaudio
import sys
import time
import getopt
import alsaaudio

device = 'default'
opts, args = getopt.getopt(sys.argv[1:], 'd:')
for o, a in opts:
    if o == '-d':
        device = a

if not args:
    print('usage: recordtest.py [-d <device>] <file>', file=sys.stderr)
    sys.exit(2)

f = open(args[0], 'wb')

# Open the device in nonblocking capture mode in mono, with a sampling rate of 44100 Hz
# and 16 bit little endian samples
# The period size controls the internal number of frames per period.
# The significance of this parameter is documented in the ALSA api.
# For our purposes, it is suficcient to know that reads from the device
# will return this many frames. Each frame being 2 bytes long.
# This means that the reads below will return either 320 bytes of data
# or 0 bytes of data. The latter is possible because we are in nonblocking
# mode.
inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL,
    channels=1, rate=16000, format=alsaaudio.PCM_FORMAT_S16_LE,
                    periodsize=160, device=device)

loops = 10000000000
while loops > 0:
    loops -= 1
    # Read data from device
    l, data = inp.read()
    if l:
        print(loops)
        ret = f.write(data)

inp.close()
