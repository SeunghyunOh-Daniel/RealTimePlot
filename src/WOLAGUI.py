"""
Main Operation
"""

# --------------------------------------------------------------------------------------------------------------------------------------

# Library
import sys, os
sys.path.append("lib/")

import tkinter as tk
from tkinter import ttk
import ctypes
import matplotlib

matplotlib.use('TkAgg')

import threading
import queue
import time
from tkinter import messagebox

try:
    from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk as nav_tool
except:
    from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg as nav_tool

from tk_api import *
from realtime_plot import real_time_plot
from realtime_dsp import process_thread
from sthread import sthreading

# --------------------------------------------------------------------------------------------------------------------------------------

# Constant
audiogram_table = (100, 250, 500, 1000, 2000, 3000, 4000, 6000, 8000)

# Screen Size
from PIL import ImageGrab
img = ImageGrab.grab()
# user32 = ctypes.windll.user32
# screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
screensize = img.size[0], img.size[1]
percentOfWidth = 1
# 0.86
percentOfHeight = 1
# 0.85

START, STOP = "start", "stop"

features_ref = {'overlap_percent': 75,
                'NFFT': 256,
                'Attack_coeff': 0.00125,
                'Release_coeff': 0.00125,
                'AttackRelease': "OFF",
                'NR': "OFF",
                'FB': "OFF",
                'COMPRESSION': "OFF",
                'EQ': [0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.1],
                'frequency': [100, 250, 500, 1000, 2000, 3000, 4000, 6000, 8000]}

default_speaker_calibration = (
    118.97129592, 118.85342742, 118.1560025, 117.35310275, 116.41419258, 115.62182308, 115.20886492, 114.95345658,
    114.77811592, 114.84784333,
    114.98569725, 115.37972533, 116.2442175, 117.38331708, 118.87947008, 120.68096842, 122.10399808, 122.25416308,
    120.79821658, 118.21325358,
    115.36788542, 112.74273308, 110.61898283, 108.71922217, 107.14874533, 105.73730825, 104.46745983, 103.27669458,
    102.26681263071428, 101.25693068142857,
    100.24704873214286, 99.23716678285714, 98.22728483357143, 97.21740288428572, 96.20752093499999, 95.19763898571428,
    94.18775703642856, 93.17787508714285, 92.16799313785714, 91.15811118857143,
    90.14822923928571, 89.13834729, 88.12846534071429, 87.11858339142857, 86.10870144214286, 85.09881949285713,
    84.08893754357143, 83.0790555942857, 82.06917364499999, 81.05929169571428,
    80.04940974642857, 79.03952779714285, 78.02964584785714, 77.01976389857143, 76.00988194928571, 75.0
)


# --------------------------------------------------------------------------------------------------------------------------------------

class statement(object):
    def __init__(self):
        self.attack_release = True
        self.noise_reduction = False
        self.feedback_cancellation = False
        self.compression = True
        self.equalizer = True


def get_attack_coeff(value):
    features_ref['Attack_coeff'] = value


def get_release_coeff(value):
    features_ref['Release_coeff'] = value


def get_eq_coeff(channel, gain):
    for index, val in enumerate(features_ref['frequency']):
        if channel == val:
            features_ref['EQ'][index] = gain
            break


# Shared for Main Frame
queue_process = queue.Queue()


# Check Main Frame
def get_queue():
    number_thread = threading.active_count()
    main_thread = threading.main_thread()
    try:
        if queue_process.qsize() > 0:
            val = queue_process.get_nowait()
            print(val)
            print(f"main thread:{main_thread}\n"
                  f"Total thread {number_thread}\n"
                  f"Current thread {threading.current_thread()}\n"
                  f"Thread list ")
            for thread in threading.enumerate():
                print(f" {thread.name}")

        else:
            print("NO VALUE")
            print(f"main thread:{main_thread}\n"
                  f"Total thread {number_thread}\n"
                  f"Current thread {threading.current_thread()}\n"
                  f"Thread list ")
            for thread in threading.enumerate():
                print(f" {thread.name}")
    finally:
        pass


# GUI
class simulator(tk.Tk):
    def __init__(self, sampling_rate):
        # self.master = tk.Tk()
        super().__init__()

        self.title("Hearing Aid Simulator")
        self.geometry("%dx%d" % (screensize[0] * percentOfWidth, screensize[1] * percentOfHeight))
        # self.window.attributes('-fullscreen', True)

        """    column 0 column 1 ...
             -------------------------------------------
    row 0    |   <--->                                 |
    row 1    |     * |                                 |
      .      |                                         |
      .      |                                         |              
      .      |                                         |
             |                                         |
             |                                         |
             |                                         |
             -------------------------------------------
        """

        # Overall flow row 1-2
        self.MainFrame = ttk.LabelFrame(self, text=" Flowchart ", width=screensize[0] * 0.99)
        self.MainFrame.grid(row=0, columnspan=10, sticky='WE',
                            padx=5, pady=5, ipadx=5, ipady=5)

        # Create each Top Frame
        self.top_attack_release = tk.Toplevel
        self.top_compression = tk.Toplevel
        self.top_equalizer = tk.Toplevel
        self.top_setting_calibration = tk.Toplevel

        # Each top's open flag
        self.tops_flag = {'EQ': 0,
                          'COMPRESSION': 0,
                          'ATTACK&RELEASE': 0,
                          'SET_CALIBRATION': 0}

        # Plot option Frame, location: row 3
        self.plot_option_frame = ttk.LabelFrame(self, text=" Plot Option", width=screensize[0] * 0.99,
                                                height=screensize[1] * 0.01)
        self.plot_option_frame.grid(row=3, columnspan=10, sticky='WE',
                                    padx=5, pady=5, ipadx=5, ipady=5)

        # Plot Frame, location: row 4-5
        self.plot_frame = ttk.LabelFrame(self, text="Plot", width=screensize[0] * 0.99,
                                         height=screensize[1] * 0.01)
        self.plot_frame.grid(row=4, columnspan=10, sticky='WE',
                             padx=5, pady=5, ipadx=5, ipady=5)

        self.sampling_rate = sampling_rate

        # Create the plot
        self.plot = real_time_plot.RealtimePlotter(self.plot_frame,
                                                   [(-1, +1)],
                                                   size=100,
                                                   total_time=1,
                                                   sampling_rate=self.sampling_rate,
                                                   show_yvals=True,
                                                   window_name='Graph demo',
                                                   yticks=[(-1, 0, +1)],
                                                   styles=[''],
                                                   ylabels=['Plot'],
                                                   interval=0.05)

        # Start the plot
        self.plot.launch_thread()

        # Create processing thread
        self.dsp_thread = process_thread.ProcessThread(queue_process)
        self.dsp_thread.start()

        # Apply coefficient to processing
        self.test_coff = 1

        # Create Main GUI object
        self.create_widgets()

        # Current statement of function
        self.statement = statement()

        # Signal Features
        self.features = {'overlap_percent': 75,
                         'NFFT': 256,
                         'Attack_coeff': 0.00125,
                         'Release_coeff': 0.00125,
                         'AttackRelease': "OFF",
                         'NR': "OFF",
                         'FB': "OFF",
                         'COMPRESSION': "OFF",
                         'EQ': [0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.1]}

        # Make the component on Plot Frame
        self.create_plot()

        # Set the Close button
        self.protocol("WM_DELETE_WINDOW", self.on_exit)

    def stop_plot(self):
        # Stop the plot
        if self.dsp_thread.active_id_thread is not None:
            self.dsp_thread.active_id_thread.terminate()
            queue_process.__init__()
            self.plot.reset_plot()
        else:
            queue_process.__init__()
            self.plot.reset_plot()
            pass

    def on_exit(self, value=None):
        # Set exit button from each Window
        if value is None:
            if messagebox.askokcancel("Close", "Do you want to quit?", parent=self):
                self.plot.quit()
                self.MainFrame.destroy()
                self.plot_option_frame.destroy()
                self.plot_frame.destroy()
                self.destroy()
                self.quit()
            else:
                pass
        else:
            flag_name = value[0]
            if flag_name == 'EQ':
                if messagebox.askokcancel("Close", "Do you want to quit the set?", parent=self.top_equalizer):
                    self.tops_flag[flag_name] = 0
                    self.top_equalizer.destroy()
                else:
                    pass
            elif flag_name == 'ATTACK&RELEASE':
                if messagebox.askokcancel("Close", "Do you want to quit the set?", parent=self.top_attack_release):
                    self.tops_flag[flag_name] = 0
                    self.top_attack_release.destroy()
                else:
                    pass
            elif flag_name == 'COMPRESSION':
                if messagebox.askokcancel("Close", "Do you want to quit the set?", parent=self.top_compression):
                    self.tops_flag[flag_name] = 0
                    self.top_compression.destroy()
                else:
                    pass
            elif flag_name == 'SET_CALIBRATION':
                if messagebox.askokcancel("Close", "Do you want to quit the set?", parent=self.top_setting_calibration):
                    self.tops_flag[flag_name] = 0
                    self.top_setting_calibration.destroy()
                else:
                    pass
            else:
                pass

    def on_exit_eq(self):
        # Set exit button from EQ window
        self.on_exit(("EQ",))

    def on_exit_ar(self):
        # Set exit button from Attack, Release window
        self.on_exit(("ATTACK&RELEASE",))

    def on_exit_cp(self):
        # Set exit button from Compression window
        self.on_exit(("COMPRESSION",))

    def on_exit_sc(self):
        # Set exit button from Set speaker calibration data window
        self.on_exit(("SET_CALIBRATION",))

    """
    Set Signal Features using directly or opening setting window
    """

    def fft_bins(self, value):
        self.features['NFFT'] = value

    def overlap_percent(self, value):
        self.features['overlap_percent'] = value

    def nr_onoff(self):
        state = self.statement.noise_reduction
        if state:
            state = ~state
            self.statement.noise_reduction = state
            create_buttons(self.MainFrame, 11, 1, "tomato", "Noise Reduction", self.nr_onoff)
            print(f"NoiseReduction OFF")
        else:
            state = ~state
            self.statement.noise_reduction = state
            create_buttons(self.MainFrame, 11, 1, "light green", "Noise Reduction", self.nr_onoff)
            print(f"NoiseReduction ON")

    def fb_onoff(self):
        state = self.statement.feedback_cancellation
        if state:
            state = ~state
            self.statement.feedback_cancellation = state
            create_buttons(self.MainFrame, 13, 1, "tomato", "Feedback Cancellation", self.fb_onoff)
            print(f"FeedbackCancellation OFF")
        else:
            state = ~state
            self.statement.feedback_cancellation = state
            create_buttons(self.MainFrame, 13, 1, "light green", "Feedback Cancellation", self.fb_onoff)
            print(f"FeedbackCancellation ON")

    def compression(self):
        if self.tops_flag["COMPRESSION"] == 1:
            pass
        else:
            self.open_window("COMPRESSION")

    def setEq(self):
        if self.tops_flag["EQ"] == 1:
            pass
        else:
            self.open_window("EQ")

    def attack_release(self):
        if self.tops_flag["ATTACK&RELEASE"] == 1:
            pass
        else:
            self.open_window("ATTACK&RELEASE")

    def setSpeakerCalibration(self):
        if self.tops_flag["SET_CALIBRATION"] == 1:
            pass
        else:
            self.open_window("SET_CALIBRATION")

    """
    Set Signal Features on opening setting window
    """

    def set_eq_coefficent(self):
        for index in range(len(self.features['EQ'])):
            self.features['EQ'][index] = features_ref['EQ'][index]

        self.tops_flag['EQ'] = 0
        self.top_equalizer.destroy()

    def set_ar_coefficent(self):
        self.features['Attack_coeff'] = features_ref['Attack_coeff']
        self.features['Release_coeff'] = features_ref['Release_coeff']

        self.tops_flag['ATTACK&RELEASE'] = 0
        self.top_attack_release.destroy()

    def open_window(self, value):
        # Make the windows in each of cases
        if self:
            if value == "EQ":
                self.tops_flag[value] = 1
                self.top_equalizer = tk.Toplevel()
                eq_frame = ttk.LabelFrame(self.top_equalizer, text="Equalizer", height=270, width=100)
                eq_frame.grid(row=6, columnspan=10, sticky='WE',
                              padx=5, pady=5, ipadx=5, ipady=5)
                # Frequencies to equalize
                # freq=['100','250','500','1000','2000','3000','4000','5000','6000','8000']
                freq = [100, 250, 500, 1000, 2000, 3000, 4000, 6000, 8000]
                x, y = 1, 1
                for index, value in enumerate(freq):
                    # Freq (Hz)
                    create_label(eq_frame, x, y, str(value) + ' Hz')
                    y = 2
                    create_EQ_scale(eq_frame, x, y,
                                    0.5, -0.5, 0.1,
                                    "vertical", self.features['EQ'][index], 100,
                                    'Red', value, get_eq_coeff)
                    x = x + 1
                    y = 1

                self.top_equalizer.protocol("WM_DELETE_WINDOW", self.on_exit_eq)
                create_buttons(eq_frame, int(x / 2) - 1, 3, None, "SET VALUE", self.set_eq_coefficent)

            elif value == "COMPRESSION":
                from tkinter import messagebox
                messagebox.showinfo("", "Service Preparing...")

            elif value == "ATTACK&RELEASE":
                self.tops_flag[value] = 1
                self.top_attack_release = tk.Toplevel()
                # Attack & Release
                ar_frame = ttk.LabelFrame(self.top_attack_release, text=" Attack & Release ", height=150, width=500)
                ar_frame.grid(row=4, columnspan=10, sticky='WE',
                              padx=5, pady=5, ipadx=5, ipady=5)

                # Attack Coefficients
                create_label(ar_frame, 1, 1, "Attack Coefficients")
                create_scale(ar_frame, 2, 1, 0.005, .2, 0.005, "horizontal", self.features["Attack_coeff"],
                             700, 'Red', get_attack_coeff)

                # Release Coefficients
                create_label(ar_frame, 1, 10, "Release Coefficients")
                create_scale(ar_frame, 2, 10, 0.1, 2, 0.1, "horizontal", self.features["Release_coeff"], 700,
                             'Red', get_release_coeff)

                self.top_attack_release.protocol("WM_DELETE_WINDOW", self.on_exit_ar)
                create_buttons(ar_frame, 1, 3 + 11, None, "SET VALUE", self.set_ar_coefficent)

            elif value == "SET_CALIBRATION":
                self.tops_flag[value] = 1
                self.top_setting_calibration = tk.Toplevel()
                setting_calibration_frame = ttk.LabelFrame(self.top_setting_calibration,
                                                           text="Setting for Speaker Calibration",
                                                           height=270, width=100)
                setting_calibration_frame.grid(row=6, columnspan=10, sticky='WE',
                                               padx=5, pady=5, ipadx=5, ipady=5)

                create_label(setting_calibration_frame, 0, 0, 'The number of Channel')
                self.textbox_speakerCalibration[0] = create_textbox_custom(setting_calibration_frame, 0, 1, 100,
                                                                           len(self.compression_features[
                                                                                   'SPEAKER_CALIBRATION']['value']))

                create_label(setting_calibration_frame, 0, 2, 'Value')
                create_label(setting_calibration_frame, 0, 3,
                             "Example: 118.971259, 118.827642, 118.156025, 117.353175, 116.419258, 115.621308")
                from functools import reduce
                self.textbox_speakerCalibration[1] = create_textbox_custom(setting_calibration_frame, 0, 4, 100,
                                                                           reduce(lambda x, y: str(x) + ", " + str(y),
                                                                                  default_speaker_calibration))

                create_buttons(setting_calibration_frame, 0, 5, None, "SET DATA", self.set_sc)
                self.top_setting_calibration.protocol("WM_DELETE_WINDOW", self.on_exit_sc)

    def reset_coefficent(self, value):
        # Reset the features to values when started in first time
        if value == "EQ":
            for index in range(len(self.features['EQ'])):
                self.features['EQ'][index] = 0
                features_ref['EQ'][index] = 0

        elif value == "COMPRESSION":
            print()

        elif value == "ATTACK&RELEASE":
            self.features['Attack_coeff'] = 0.005
            self.features['Release_coeff'] = 0.1
            features_ref['Attack_coeff'] = 0.005
            features_ref['Release_coeff'] = 0.1

    def debug_compression_table(self):
        # Print compression features
        print(f"----COMPRESSION TABLE----\n"
              f" GENDER: {self.compression_features['GENDER']['value'].get()}\n"
              f" TONAL: {self.compression_features['TONAL']['value'].get()}\n"
              f" EXPERIENCE: {self.compression_features['EXPERIENCE']['value'].get()}\n"
              f" AUDIOGRAM\n"
              f" LEFT: {self.compression_features['AUDIOGRAM_LEFT']['value']}\n"
              f" RIGHT: {self.compression_features['AUDIOGRAM_RIGHT']['value']}\n"
              f" SPEAKER CALIBRATION: {self.compression_features['SPEAKER_CALIBRATION']['value']}")

    def debug(self):
        # Print whole features
        print(f"-----------------------------DEBUG--------------------------------"
              f"Olive Value: \n"
              f" Number of FFT: {self.features['NFFT']}\n"
              f" Overlap(%): {self.features['overlap_percent']}\n"
              f"Attack & Release: \n"
              f" Attack: {self.features['Attack_coeff']}  "
              f" Release: {self.features['Release_coeff']}")

        if self.statement.attack_release:
            print(f" State: ON")
        else:
            print(f" State: OFF")

        print(f"Noise Reduction ", end="")
        if self.statement.noise_reduction:
            print(f" State: ON")
        else:
            print(f" State: OFF")

        print(f"Feedback Cancellation: ", end="")
        if self.statement.feedback_cancellation:
            print(f" State: ON")
        else:
            print(f" State: OFF")

        print(f"Compression: ", end="")
        if self.statement.compression:
            print(f" State: ON")
        else:
            print(f" State: OFF")

        print(f"Equalizer: ")
        print(" ", end='')
        for value in self.features['EQ']:
            print(f"{value} ", end='')
        print()
        if self.statement.equalizer:
            print(f" State: ON")
        else:
            print(f" State: OFF")

        print(f"\nTest Value {self.test_coff}\n"
              f"---------------------------------------------------------------------")

        self.debug_compression_table()

    def set_effect(self):
        """
        Apply effect to plot
        """
        self.test_coff = self.test_coff + 1

        # Complete message
        messagebox.showinfo("", "Complete!")

    def create_widgets(self):
        # Main Frame for location of each object

        # Microphone
        create_label(self.MainFrame, 1, 1, "MIC")
        create_arrow(self.MainFrame, 2, 1)

        # Overlap %
        create_label(self.MainFrame, 3, 1, "Overlap %")
        create_scale(self.MainFrame, 3, 2, 25, 75, 25, "horizontal", 75, 90, 'Black', self.overlap_percent)
        create_arrow(self.MainFrame, 4, 1)

        # Number of FFT bins
        create_label(self.MainFrame, 5, 1, "Number of FFT bins")
        create_scale(self.MainFrame, 5, 2, 64, 512, 64, "horizontal", 128, 90, 'Black', self.fft_bins)
        create_arrow(self.MainFrame, 6, 1)

        # Energy
        create_label(self.MainFrame, 7, 1, "Energy")
        create_arrow(self.MainFrame, 8, 1)

        # Attack & Release
        create_buttons(self.MainFrame, 9, 1, "light green", "Attack/Release", self.attack_release)
        create_arrow(self.MainFrame, 10, 1)

        # Noise Reduction
        create_buttons(self.MainFrame, 11, 1, "tomato", "Noise Reduction", self.nr_onoff)
        create_arrow(self.MainFrame, 12, 1)

        # Feedback Cancellation
        create_buttons(self.MainFrame, 13, 1, "tomato", "Feedback Cancellation", self.fb_onoff)
        create_arrow(self.MainFrame, 14, 1)

        # Compression
        create_buttons(self.MainFrame, 15, 1, "light green", "Compression", self.compression)
        create_arrow(self.MainFrame, 16, 1)

        # Equalizer
        create_buttons(self.MainFrame, 17, 1, "light green", "Equalizer", self.setEq)
        create_arrow(self.MainFrame, 18, 1)

        # iFFT
        create_label(self.MainFrame, 19, 1, "iFFT")
        create_arrow(self.MainFrame, 20, 1)

        # Speaker
        create_label(self.MainFrame, 21, 1, "Speaker")

        # Debug
        create_buttons(self.MainFrame, 11, 2, "light green", "Debug Value", self.debug)

        # Set Effect
        create_buttons(self.MainFrame, 12, 2, "light green", "    Set    ", self.set_effect)

        create_buttons(self.plot_option_frame, 10, 1, "light green", "queue", get_queue)
        create_buttons(self.plot_option_frame, 11, 1, "light green", "stop the plot", self.stop_plot)

    def launch_dsp(self, evt=None):
        # Pass the feature and Be On the signal processing
        self.dsp_thread.set_onoff(('test', self.test_coff))

    def create_plot(self):
        # Create Plot Frame
        interface_frame = ttk.Frame(self.plot_option_frame)
        interface_frame.grid(row=1, column=9, sticky='WE',
                             padx=5, pady=5, ipadx=5, ipady=5)

        create_buttons(interface_frame, 9, 1, "light green", "DSP ON", self.launch_dsp)


def update_queue(data_queue, simulator):
    # Update data to queue
    while True:
        if data_queue.empty():
            pass
        else:
            frame = data_queue.get_nowait()
            # update the data
            simulator.plot.update_(frame)

        # Period 1ms
        time.sleep(0.001)


def main():
    # GUI
    root = simulator(sampling_rate=44100)

    # Update thread
    thread_UpdateMainQueue = sthreading.sThread(name="UpdateMainQueueThread", target=update_queue,
                                                args=(queue_process, root))
    thread_UpdateMainQueue.start()

    # Start the GUI event loop
    root.mainloop()


if __name__ == "__main__":
    main()
