#!/usr/local/bin/env python
####################################
## Athanasios Athanassiadis
## log pressure using a LabJack
## 10/30/2014
##
## lots of code borrowed from LabJackPython's
## streamTest-threading.py
##
## https://github.com/labjack/LabJackPython/blob/master/Examples/streamTest-threading.py
##
####################################
from __future__ import division

__author__ = 'thanasi'
__version__ = '0.1a'

import numpy as np

import u6
from datetime import datetime
import threading
import Queue
import copy, sys

# MAX_REQUESTS is the number of packets to be read.
MAX_REQUESTS = 5000


## volts to Pascals
## from sensor spec sheet
VoverP = 0.766 / 1000.

## output offset (V)
## from sensor spec sheet
## min:typ:max  -- 0.1 : 0.225 : 0.430
VOFF = 0.225

## convert reading in Volts to pressure in Pascals
VtoP = lambda V: (VtoP-VOFF) / VoverP


## voltage

class StreamDataReader(object):
    def __init__(self, device):
        self.device = device
        self.data = Queue.Queue()
        self.dataCount = 0
        self.missed = 0
        self.running = False

    def readStreamData(self):
        self.running = True

        start = datetime.now()
        self.device.streamStart()
        while self.running:
            # Calling with convert = False, because we are going to convert in
            # the main thread.
            returnDict = self.device.streamData(convert = False).next()

            self.data.put_nowait(copy.deepcopy(returnDict))

            self.dataCount += 1
            if self.dataCount > MAX_REQUESTS:
                self.running = False

        sys.stdout.write("stream stopped.")
        sys.stdout.write("\n")
        sys.stdout.flush()
        self.device.streamStop()
        stop = datetime.now()

        total = self.dataCount * self.device.packetsPerRequest * self.device.streamSamplesPerPacket
        sys.stdout.write("%s requests with %s packets per request with %s samples per packet = %s samples total." % ( self.dataCount, d.packetsPerRequest, d.streamSamplesPerPacket, total ))
        sys.stdout.write("\n")

        sys.stdout.write("%s samples were lost due to errors." % self.missed)
        sys.stdout.write("\n")
        total -= self.missed
        sys.stdout.write("Adjusted number of samples = %s" % total)
        sys.stdout.write("\n")

        runTime = (stop-start).seconds + float((stop-start).microseconds)/1000000
        sys.stdout.write("The experiment took %s seconds." % runTime)
        sys.stdout.write("\n")
        sys.stdout.write("%s samples / %s seconds = %s Hz" % ( total, runTime, float(total)/runTime ))
        sys.stdout.write("\n")
        sys.stdout.flush()



if __name__ == "__main__":

    # At high frequencies ( >5 kHz), the number of samples will be
    # MAX_REQUESTS times 48 (packets per request) times 25 (samples per packet)
    d = u6.U6()

    # For applying the proper calibration to readings.
    d.getCalibrationData()

    sys.stdout.write("configuring U6 stream")
    sys.stdout.write("\n")
    sys.stdout.flush()
    d.streamConfig( NumChannels = 1, ChannelNumbers = [ 0 ], ChannelOptions = [ 0 ], SettlingFactor = 1, ResolutionIndex = 1, SampleFrequency = 50000 )

    sdr = StreamDataReader(d)
    sdrThread = threading.Thread(target = sdr.readStreamData)

    # Start the stream and begin loading the result into a Queue
    sdrThread.start()

    errors = 0
    missed = 0
    while True:
        try:
            # Check if the thread is still running
            if not sdr.running:
                break

            # Pull results out of the Queue in a blocking manner.
            result = sdr.data.get(True, 1)

            # If there were errors, print that.
            if result['errors'] != 0:
                errors += result['errors']
                missed += result['missed']
                sys.stdout.write("+++++ Total Errors: %s, Total Missed: %s" % (errors, missed))
                sys.stdout.write("\n")
                sys.stdout.flush()

            # Convert the raw bytes (result['result']) to voltage data.
            r = d.processStreamData(result['result'])

            # Do some processing on the data to show off.
            sys.stdout.write("Average of " + str(len(r['AIN0'])) +  " reading(s): " + str(sum(r['AIN0'])/len(r['AIN0'])))
            sys.stdout.write("\n")
            sys.stdout.flush()

        except Queue.Empty:
            sys.stdout.write("Queue is empty. Stopping...")
            sys.stdout.write("\n")
            sys.stdout.flush()
            sdr.running = False
            break
        except KeyboardInterrupt:
            sdr.running = False
        except Exception, e:
            print type(e), e
            sdr.running = False
            break


    print sdr.data