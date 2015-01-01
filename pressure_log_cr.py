#!/usr/local/bin/env python
############################
## A G Athanassiadis
## Oct 2014
##
############################
from __future__ import division

import numpy as np
import u6
from datetime import datetime
import threading
import Queue
import copy, sys, os



## Constants
############################

## analog channel to use
AIN_CH = 0

## volts to Pascals
## from sensor spec sheet
V_by_P = 0.766 / 1000.  ## V/Pa

## output offset (V)
## from sensor spec sheet
## min:typ:max  -- 0.1 : 0.225 : 0.430

V_offset = 0.225    ## volts

## sensor accuracy
## from spec sheet
sensor_accuracy = 4.6 * 0.05    ## (V)
sensor_accuracy_p = 4.6 / V_by_P * 0.05 ## (Pa)

## convert reading in Volts to pressure in Pascals
# VtoP = lambda V: (V - V_offset) / V_by_P   ## output in Pa


## gain can be any of [0,1,2,3]
## corresponding to [1x, 10x, 100x, 1000x] gain
## with 1x corresponding to +/- 10V measurement range
gain_index = 0

## resolution index
## 0-8 provide good resolution at high speed
## 9-12 provide higher resolution at lower speeds
## this is all gain dependent
# res_index = 10       ## with 1x gain, this should give 20.6bit resolution @ 71.4Hz
res_index = 8


## settling factor
## how long the ADC waits after a step change before saving samples
## 0 (auto) - 9(10ms)
settling_factor = 3     ## 100us delay

## how long to collect data for
runTime = 15    ## (seconds)


## feedback command
cmd = u6.AIN24AR(AIN_CH, ResolutionIndex = res_index,
                    GainIndex = gain_index,
                    SettlingFactor = settling_factor)



## output file
# filename = "/users/thanasi/Desktop/testdata2.npz"
filepath = "/Users/thanasi/Dropbox (MIT)/data/vortex_pressure/"


if __name__ == "__main__":

    ## get
    notes = sys.argv[1]

    # initialize device
    d = u6.U6()


    try:
        # For applying the proper calibration to readings.
        d.getCalibrationData()


        data = []
        res = []
        gains = []
        times = []

        start_time = datetime.now()
        dt = 0
        while dt < runTime:
            ## get input voltage
            f = d.getAIN(AIN_CH, resolutionIndex=res_index, gainIndex=gain_index)   ## volts

            dt = datetime.now() - start_time ## datetime object
            dt = dt.seconds + float(dt.microseconds)/1000000.   ## seconds
            times.append(dt)

            data.append(f)
            # data.append(f['AIN'])
            # res.append(f['ResolutionIndex'])
            # gains.append(f['GainIndex'])


        nSamples = len(data)
        sys.stdout.write("%0ss per sample\n" % (dt/nSamples))
        sys.stdout.write("%4.3f samples/sec\n" % (nSamples/dt))
        sys.stdout.flush()

        # numSamples = len(data)
        # vData = [d.binaryToCalibratedAnalogVoltage(gains[i], data[i], False, res[i]) for i in range(numSamples)]

        nData = np.array(data)      ## volts
        nTimes = np.array(times)    ## seconds
        # nPress = VtoP(nData)        ## pascals
        # nRes = np.array(res)
        # nGains = np.array(gains)
        # np.savez(filename, data=nData, res=nRes, gains=nGains, times=times)


        ## name the file based on start time and the fact that is the pressure data
        filename = start_time.strftime("%Y.%m.%d.%H%M%S.pbundle")

        ## don't overwrite existing data
        i = 0
        while os.path.exists("%s%s-%d.npz" % (filepath,filename,i)):
            i += 1

        ## output voltage, pressure, and time data
        # np.savez("%s%s-%d.npz" % (filepath,filename,i),
        #          data=nData, press=nPress, times=nTimes, notes=notes)

        np.savez("%s%s-%d.npz" % (filepath,filename,i),
                 data=nData, times=nTimes, notes=notes)

    ## clean up if we run into issues
    ## that way there are no problems re-running
    except Exception, e:
        print "Caught an exception", e
        pass

    d.close()