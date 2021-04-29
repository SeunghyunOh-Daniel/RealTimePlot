"""
Real-time scrolling multi-plot over time.

Requires: matplotlib
          numpy

Adapted from example in http://stackoverflow.com/questions/8955869/why-is-plotting-with-matplotlib-so-slow

Copyright (C) 2015 Simon D. Levy

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
"""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import threading
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

try:
    from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk as nav_tool
except:
    from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg as nav_tool

import time
import queue


class tkThread(threading.Thread):

    def __init__(self, queue, var, operation_mode, interval, shared_queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self._shared_queue = shared_queue
        self.flag = True
        self.var = var
        self.operation_mode = operation_mode
        self.interval = interval

    def stop(self):
        self.flag = False

    # start in Thread class
    def run(self):
        while self.flag:
            if self._shared_queue.empty():
                print("No Data")
                self.queue.put((0, ), "No Data")
                pass
            else:
                frame = self._shared_queue.get_nowait()
                self.queue.put(frame, "Data")
            time.sleep(self.interval)
        else:
            print("No Run")
            args = (None, "Stop")
            self.queue.put(args)


def _check_param(nrows, propvals, propname, dflt):
    """
    Check number of rows and domain of values
    """
    retval = [dflt] * nrows
    if propvals:
        if len(propvals) != nrows:
            raise Exception('Provided %d ylims but %d %s' % (nrows, len(propvals), propname))
        else:
            retval = propvals
    return retval


class RealtimePlotter(tk.Frame):
    """
    Real-time scrolling multi-plot over time.  Your data-acquisition code should run on its own thread,
    to prevent blocking / slowdown.
    """
    sampling_frequency = 0

    def handleClose(self, event):
        """
        Automatically called when user closes plot window.
        Override to do you own shutdown.
        """

        self.is_open = False

    def __init__(self,
                 parent,
                 ylims,
                 size=100,
                 time=1,
                 sampling_frequency=None,
                 frame=None,
                 phase_limits=None,
                 show_yvals=False,
                 window_name=None,
                 styles=None,
                 ylabels=None,
                 yticks=[],
                 legends=[],
                 interval_msec=0.001,
                 shared_queue=None):
        """
        Initializes a multi-plot with specified Y-axis limits as a list of pairs; e.g.,
        [(-1,+1), (0.,5)].  Optional parameters are:

        size             size of display (X axis) in arbitrary time steps
        time             unit time if plot same time in plot (sec)
        phaselims        xlim,ylim for phase plot
        show_yvals       display Y values in plot if True
        window_name      name to display at the top of the figure
        styles           plot styles (e.g., 'b-', 'r.'; default='b-')
        yticks           Y-axis tick / grid positions
        legends          list of legends for each subplot
        interval_msec    animation update in milliseconds

        For overlaying plots, use a tuple for styles; e.g., styles=[('r','g'), 'b']
        """

        # Variable for GUI
        super().__init__()

        self.parent = parent
        self.var = tk.IntVar()
        self.interval = tk.DoubleVar()
        self.queue = queue.Queue()
        self.block_size = 0
        self.my_thread = None
        self.id_after = None
        self.operation_mode = ('Exponential', 'Normal',)
        self._shared_queue = shared_queue
        # Row count is provided by Y-axis limits
        nrows = len(ylims)

        # Bozo filters
        styles = _check_param(nrows, styles, 'styles', 'b-')
        ylabels = _check_param(nrows, ylabels, 'ylabels', '')
        yticks = _check_param(nrows, yticks, 'yticks', [])
        self.legends = _check_param(nrows, legends, 'legends', [])
        if sampling_frequency is None:
            raise ValueError

        # Get the current plot
        self.fig = plt.gcf()

        # Set up subplots
        self.axes = [None] * nrows
        ncols = 2 if phase_limits else 1
        self.sideline = None

        if phase_limits:
            side = plt.subplot(1, 2, 1)
            # Phase Plot square shape
            side.set_aspect('equal')
            self.sideline = side.plot(y, y, 'o', animated=True)
            side.set_xlim(phase_limits[0])
            side.set_ylim(phase_limits[1])

        # locate the axes(plot)
        for k in range(nrows):
            self.axes[k] = plt.subplot(nrows, ncols, ncols * (k + 1))
        self.window_name = 'RealtimePlotter' if window_name is None else window_name

        # Set up handler for window-close events
        self.fig.canvas.mpl_connect('close_event', self.handleClose)
        self.is_open = True

        self.sampling_frequency = sampling_frequency
        len_xaxis = int(time * self.sampling_frequency)
        self.t = np.arange(0, len_xaxis)
        amplitudes = np.zeros(len_xaxis)

        self.lines = []
        for j in range(len(styles)):
            style = styles[j]
            ax = self.axes[j]
            legend = self.legends[j] if len(self.legends) > 0 else None
            styles_for_row = style if type(style) == tuple else [style]
            for k in range(len(styles_for_row)):
                label = legend[k] if legend and len(legend) > 0 else ''
                self.lines.append(ax.plot(self.t, amplitudes, styles_for_row[k], label=label)[0])
                # , animated=True
            if legend is not None and len(legend) > 0:
                ax.legend()

        # Create baselines, initially hidden
        self.baselines = [axis.plot(self.t, amplitudes, 'k', animated=True)[0] for axis in self.axes]
        self.baseflags = [False] * nrows

        # Add properties as specified
        # Set axis limits, ticks, gridlines, hide x axis tics and lables
        for axis, ylabel, ylim, ytick in zip(self.axes, ylabels, ylims, yticks):
            axis.set_xlim((0, len_xaxis))
            axis.set_ylim(ylim)
            axis.yaxis.set_ticks(ytick)
            axis.yaxis.grid(True if yticks else False)
            axis.xaxis.set_visible(False)

        # Allow interval specification
        self.interval_msec = interval_msec

        # Add axis text if indicated
        self.axis_texts = [axis.text(0.8, ylim[1] - .1 * (ylim[1] - ylim[0]), '') for axis, ylim in
                           zip(self.axes, ylims)] \
            if show_yvals else []

        # combine Figure to Canvas
        self.canvas = FigureCanvasTkAgg(self.fig, self.parent)

        toolbar = nav_tool(self.canvas, self.parent)
        toolbar.update()

        self.canvas.tkcanvas.pack(fill=tk.BOTH, expand=1)

    def quit(self):
        if self.my_thread is not None:
            if threading.active_count() != 0:
                self.my_thread.stop()
        self.after_cancel(self.id_after)
        self.id_after = None
        self.parent.destroy()

    def launch_thread(self):
        """
        Starts the realtime plotter.
        """
        self.on_realtime_plot()

    def on_realtime_plot(self, evt=None):
        if self.my_thread is not None:
            if threading.active_count() != 0:
                self.my_thread.stop()
        self.my_thread = tkThread(self.queue, self.var, self.operation_mode, 0.1, self._shared_queue)
        self.my_thread.start()
        self.periodic_call()

    def periodic_call(self):

        self.checkqueue()
        if self.my_thread.is_alive():
            self.id_after = self.after(1, self.periodic_call)
        else:
            pass

    def checkqueue(self):
        while self.queue.qsize():
            try:
                args = self._update_frame()
                # Draw the line ? ax ?

                # args = self.queue.get()
                # self.a.clear()
                # self.a.grid(True)
                #
                # if args[0] is not None:
                #     self.a.step(list(range(100)), list(args[0]))
                #     self.a.set_ylim(0, 0.5)
                #     self.a.set_title(args[1], weight='bold', loc='left')
                # else:
                #     self.a.set_title(args[1], weight='bold', loc='left')
                #     self.a.set_ylim(0, 0.5)

                self.canvas.draw()

            except queue.Empty:
                pass

    def getValues(self):
        """
        Override this method to return actual Y values at current time.
        """

        return

    def get_frame(self, frame):

        return

    def showBaseline(self, axid, value):
        """
        Shows a baseline of specified value for specified row of this multi-plot.
        """

        self._axis_check(axid)

        self.baselines[axid].set_ydata(value * np.ones(self.x.shape))
        self.baseflags[axid] = True

    def hideBaseline(self, axid):
        """
        Hides the baseline for the specified row of this multi-plot.
        """

        self._axis_check(axid)

        self.baseflags[axid] = False

    def _axis_check(self, axid):

        nrows = len(self.lines)

        if axid < 0 or axid >= nrows:
            raise Exception('Axis index must be in [0,%d)' % nrows)

    @classmethod
    def roll(cls, getter, setter, line, newval):
        data = getter(line)
        data = np.roll(data, -1 * len(newval))
        data[-1 * len(newval):] = newval
        setter(data)

    # Update x value
    @classmethod
    def rollx(cls, line, newval):
        RealtimePlotter.roll(line.get_xdata, line.set_xdata, line, newval)

    # Update y value
    @classmethod
    def rolly(cls, line, newval):
        RealtimePlotter.roll(line.get_ydata, line.set_ydata, line, newval)

    # Update frame value
    @classmethod
    def rollframe(cls, line, new_frame):
        RealtimePlotter.roll(line.get_ydata, line.set_ydata, line, new_frame)

    def _update_frame(self, frame_bias=0):

        def _update(frame):
            # Time domain
            yvals = frame[1], None
            # Current Point and Represent Text
            # for k, text in enumerate(self.axis_texts):
            #     text.set_text('%+f' % yvals[k])

            for row, line in enumerate(self.lines, start=1):
                RealtimePlotter.rollframe(line, yvals[row - 1])

        frame = self.queue.get()
        if frame[0] == 0:
            if self.block_size == 0:
                pass
            else:
                frame = (self.block_size, np.zeros(self.block_size))
                _update(frame)
        else:
            if self.block_size != frame[0]:
                self.block_size = frame[0]
                _update(frame)
            else:
                _update(frame)

        # sideline(for phase), lines, baseline, text
        return (self.sideline if self.sideline is not None else []) + \
               self.lines + [baseline for baseline, flag in zip(self.baselines, self.baseflags) if flag] + \
               self.axis_texts
