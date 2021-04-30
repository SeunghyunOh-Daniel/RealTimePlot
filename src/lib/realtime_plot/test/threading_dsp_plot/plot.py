#!/usr/bin/env python3
'''
Real-time plot demo using sine waves.
Copyright (C) 2015 Simon D. Levy
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
'''

import numpy as np

from real_time_plot import RealtimePlotter

# Simple example with threading
count = 0


class Plotter(RealtimePlotter):
    def __init__(self, sampling_frequency):
        RealtimePlotter.__init__(self, [(-1, +1)],
                                 size=100,
                                 time=1,
                                 sampling_frequency=sampling_frequency,
                                 show_yvals=True,
                                 window_name='Graph demo',
                                 yticks=[(-1, 0, +1)],
                                 styles=[''],
                                 ylabels=['Plot'],
                                 interval_msec=1e-4)

        self.xcurr = 0
        self.yvals = []

        self.sampling_freq = 0
        self._time_current = 0
        self._amplitudes = []

    def getValues(self):
        return self._getWaves(1), None

    def _getWave(self, k):
        size = len(self.x)
        xval = (float(self.xcurr) % size) / size
        return np.sin(2 * k * np.pi * xval)

    def _getWaves(self, array):
        global count
        if len(self.yvals) == 0:
            return None
        else:
            count = count + 1
            yval = self.yvals[0]
            self.yvals = self.yvals[1:]
            # print(f"{count}: {yval}")
            return yval

    def update_frame(self):
        return self._get_amplitudes(), None

    def _get_amplitudes(self):
        try:
            frame = self._amplitudes[0]
            self._amplitudes = self._amplitudes[1:]
            return frame

        except IndexError:
            return None

    def get_frame_(self, frame):
        self._amplitudes.append(frame)



# import time
#
#
# def _print_time():
#     print(f"From print_time {time.time}")
#
# time_get_updated = 0


# def update(plotter, thread_variable=None):
#     from time import sleep
#     while True:
#         global time_get_updated
#         # if -> flag == 0 --> wait to change? being possible?
#         print(f"Frame Update Time: {time.perf_counter()}")
#         print(f"Frame Update Period: {time.perf_counter() - time_get_updated}")
#         # if len(thread_variable.lockedValue) != 0:
#         #     if thread_variable.flag == 1:
#         #         print(thread_variable.lockedIndex, thread_variable.lockedValue[0])
#         #         thread_variable.flag = 0
#         plotter.xcurr += 1
#         sleep(1)
# #
# if __name__ == '__main__':
#     import threading
#
#     plotter = Plotter()
#
#     thread = threading.Thread(target=update, args=(plotter, ))
#     thread.daemon = True
#     thread.start()
#
#     plotter.start()