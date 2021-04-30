"""
Real-time Plot over time.

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

# --------------------------------------------------------------------------------------------------------------------------------------

# Library
import matplotlib.pyplot as plt
import numpy as np
import threading
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

try:
    from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk as nav_tool
except:
    from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg as nav_tool

import queue


# --------------------------------------------------------------------------------------------------------------------------------------

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
                 total_time=1,
                 sampling_rate=44100,
                 frame=None,
                 phase_limits=None,
                 show_yvals=False,
                 window_name=None,
                 styles=None,
                 ylabels=None,
                 yticks=[],
                 legends=[],
                 interval=0.001):
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
        interval         update in milliseconds
        sampling_rate    The number of points per 1 second

        For overlaying plots, use a tuple for styles; e.g., styles=[('r','g'), 'b']
        """

        # For implementing to tkinter
        super().__init__()

        # Variable for getting from GUI
        self.parent = parent
        self.var = tk.IntVar()
        # self.interval = tk.DoubleVar()
        self.queue_plot = queue.Queue()

        """ 
        block_size: Window size of FFT
        """
        self.block_size = 0
        self.thread_UpdatePlotFrame = None
        self.id_after_tk = None

        self.operation_mode = ('Exponential', 'Normal',)
        self.queue_shared = queue.Queue()

        # Row count is provided by Y-axis limits
        nrows = len(ylims)

        # Bozo filters
        styles = _check_param(nrows, styles, 'styles', 'b-')
        ylabels = _check_param(nrows, ylabels, 'ylabels', '')
        yticks = _check_param(nrows, yticks, 'yticks', [])
        self.legends = _check_param(nrows, legends, 'legends', [])

        # Get the current plot
        self.fig = plt.gcf()

        # Set up subplots
        self.axes = [None] * nrows
        ncols = 2 if phase_limits else 1
        self.sideline = None

        """
        PREPARING...
            - Phase Domain
        if phase_limits:
            side = plt.subplot(1, 2, 1)
            # Phase Plot square shape
            side.set_aspect('equal')
            self.sideline = side.plot(y, y, 'o', animated=True)
            side.set_xlim(phase_limits[0])
            side.set_ylim(phase_limits[1])
        """

        # Locate the axes for plotting
        for k in range(nrows):
            self.axes[k] = plt.subplot(nrows, ncols, ncols * (k + 1))
        self.window_name = 'RealtimePlotter' if window_name is None else window_name

        # Set up handler for window-close events
        self.fig.canvas.mpl_connect('close_event', self.handleClose)
        self.is_open = True

        # Initialize x-axis, y-axis based on sampling-rate
        self.sampling_rate = sampling_rate
        len_xaxis = int(total_time * self.sampling_rate)
        self.xaxis = np.arange(0, len_xaxis)
        yaxix = np.zeros(len_xaxis)

        # Draw the axes
        self.lines = []
        for j in range(len(styles)):
            style = styles[j]
            ax = self.axes[j]
            legend = self.legends[j] if len(self.legends) > 0 else None
            styles_for_row = style if type(style) == tuple else [style]

            for k in range(len(styles_for_row)):
                label = legend[k] if legend and len(legend) > 0 else ''
                self.lines.append(ax.plot(self.xaxis, yaxix, styles_for_row[k], label=label)[0])
                # If want a animation option, add "animated=True"

            if legend is not None and len(legend) > 0:
                ax.legend()

        """Create baselines, initially hidden"""
        self.baselines = [axis.plot(self.xaxis, yaxix, 'k', animated=True)[0] for axis in self.axes]
        self.baseflags = [False] * nrows

        """Add properties as specified"""
        for axis, ylabel, ylim, ytick in zip(self.axes, ylabels, ylims, yticks):
            # Set axis limits, ticks, gridlines, hide x axis tics and lables
            axis.set_xlim((0, len_xaxis))
            axis.set_ylim(ylim)
            axis.yaxis.set_ticks(ytick)
            axis.yaxis.grid(True if yticks else False)
            axis.xaxis.set_visible(False)

        # Allow interval specification
        self.interval = interval

        # Add axis text if indicated
        self.axis_texts = [axis.text(0.8, ylim[1] - .1 * (ylim[1] - ylim[0]), '') for axis, ylim in
                           zip(self.axes, ylims)] \
            if show_yvals else []

        """Implement the plot_frame to parent"""
        from tkinter import ttk
        plot_frame = ttk.Frame(self.parent)
        plot_frame.grid(row=10, column=0, columnspan=10, sticky='WE',
                        padx=5, pady=5, ipadx=5, ipady=5)

        # Set the size of plot figure
        self.fig.set_size_inches(16, 5)

        # Combine Figure to Canvas
        self.canvas = FigureCanvasTkAgg(self.fig, plot_frame)

        # Implement
        toolbar = nav_tool(self.canvas, plot_frame)
        toolbar.update()
        self.canvas.tkcanvas.pack(fill=tk.BOTH, expand=1)

    def quit(self):
        """
        Terminate the Entire Program
        """
        if self.thread_UpdatePlotFrame is not None:
            if threading.active_count() != 0:
                self.thread_UpdatePlotFrame.stop()
        self.after_cancel(self.id_after_tk)
        self.id_after_tk = None

    def launch_thread(self):
        """
        Starts the realtime plotter.
        """
        self.on_realtime_plot()

    def reset_plot(self):
        """
        Initialize the plot data
        """
        self.queue_plot.__init__()
        self.queue_shared.__init__()

    def update_(self, frame):
        """
        Update from other object
        """
        self.queue_shared.put(frame)

    def on_realtime_plot(self, evt=None):
        if self.thread_UpdatePlotFrame is not None:
            self.thread_UpdatePlotFrame.stop()

        from realtime_plot import update_plot_thread
        self.thread_UpdatePlotFrame = update_plot_thread.UpdatePlotThread(var=self.var,
                                                                          operation_mode=self.operation_mode,
                                                                          interval=self.interval,
                                                                          queue_plot=self.queue_plot,
                                                                          queue_shared=self.queue_shared)
        self.thread_UpdatePlotFrame.start()
        self.periodic_call()

    def periodic_call(self):
        """
        Periodically check the plot data
        """
        self.checkqueue()
        if self.thread_UpdatePlotFrame.is_alive():
            self.id_after_tk = self.after(1, self.periodic_call)
        else:
            pass

    def checkqueue(self):
        """
        Plot the updated data
        """
        while self.queue_plot.qsize():
            try:
                args = self._update_frame()
                self.canvas.draw()

            except queue.Empty:
                pass
        else:
            pass

    def get_frame(self, frame):
        """
        Override this method to return actual frame at current time.
        """
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

    @classmethod
    def rollx(cls, line, newval):
        # Update x value
        RealtimePlotter.roll(line.get_xdata, line.set_xdata, line, newval)

    @classmethod
    def rolly(cls, line, newval):
        # Update y value
        RealtimePlotter.roll(line.get_ydata, line.set_ydata, line, newval)

    @classmethod
    def rollframe(cls, line, new_frame):
        # Update frame value
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

        frame = self.queue_plot.get()

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

        # parameter based on animation options
        return (self.sideline if self.sideline is not None else []) + \
               self.lines + [baseline for baseline, flag in zip(self.baselines, self.baseflags) if flag] + \
               self.axis_texts