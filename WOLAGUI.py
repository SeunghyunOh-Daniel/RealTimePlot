import sys, os

# pyaudio address
sys.path.append("/EQInterpolation/env_OliveGUI/Lib/site-packages")
sys.path.append("./src/")
sys.path.append("./lib/")

import tkinter as tk
from tkinter import ttk
import ctypes
import matplotlib

matplotlib.use('TkAgg')

import threading
import queue
import time
from tkinter import messagebox
from realtime_dsp.real_time_dsp_v2 import wave_file_process

import config
from tk_api import *

try:
    from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk as nav_tool
except:
    from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg as nav_tool

from realtime_plot import real_time_plot
from realtime_dsp import process_thread

audiogram_table = (100, 250, 500, 1000, 2000, 3000, 4000, 6000, 8000)

user32 = ctypes.windll.user32
screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
percentOfWidth = 1
# 0.86
percentOfHeight = 1
# 0.85

START, STOP = "start", "stop"

olive_features_ref = {'overlap_percent': 75,
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


class statement(object):
    def __init__(self):
        self.attack_release = True
        self.noise_reduction = False
        self.feedback_cancellation = False
        self.compression = True
        self.equalizer = True


def get_attack_coeff(value):
    olive_features_ref['Attack_coeff'] = value


def get_release_coeff(value):
    olive_features_ref['Release_coeff'] = value


def get_eq_coeff(channel, gain):
    for index, val in enumerate(olive_features_ref['frequency']):
        if channel == val:
            olive_features_ref['EQ'][index] = gain
            break


queue_process = queue.Queue()


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


class olivesimulator(tk.Tk):
    def __init__(self, sampling_rate):
        # self.master = tk.Tk()
        super().__init__()

        self.title("Hearing Aid Simulator")
        self.geometry("%dx%d" % (screensize[0] * percentOfWidth, screensize[1] * percentOfHeight))

        # Overall flow row 1-2
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
        self.olive_frame = ttk.LabelFrame(self, text=" Olive Flowchart ", width=screensize[0] * 0.99)
        self.olive_frame.grid(row=0, columnspan=10, sticky='WE',
                              padx=5, pady=5, ipadx=5, ipady=5)

        # Top
        self.top_attack_release = tk.Toplevel
        self.top_compression = tk.Toplevel
        self.top_equalizer = tk.Toplevel
        self.top_setting_calibration = tk.Toplevel

        # Plot option row 3
        self.plot_option_frame = ttk.LabelFrame(self, text=" Plot Option", width=screensize[0] * 0.99,
                                                height=screensize[1] * 0.01)
        self.plot_option_frame.grid(row=3, columnspan=10, sticky='WE',
                                    padx=5, pady=5, ipadx=5, ipady=5)

        # Plot row 4-5
        self.plot_frame = ttk.LabelFrame(self, text="Plot", width=screensize[0] * 0.99,
                                         height=screensize[1] * 0.01)
        self.plot_frame.grid(row=4, columnspan=10, sticky='WE',
                             padx=5, pady=5, ipadx=5, ipady=5)

        self.sampling_rate = sampling_rate
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
        self.plot.launch_thread()

        self.dsp_thread = process_thread.ProcessThread(queue_process)
        self.dsp_thread.start()

        self.test_coff = 1

        # self.window.attributes('-fullscreen', True)
        # print("This is a test 2")
        self.create_widgets()

        self.state__ = statement()
        # Olive feature
        self.olive_features = {'overlap_percent': 75,
                               'NFFT': 256,
                               'Attack_coeff': 0.00125,
                               'Release_coeff': 0.00125,
                               'AttackRelease': "OFF",
                               'NR': "OFF",
                               'FB': "OFF",
                               'COMPRESSION': "OFF",
                               'EQ': [0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.1]}

        self.olive_flags = {'EQ': 0,
                            'COMPRESSION': 0,
                            'ATTACK&RELEASE': 0,
                            'SET_CALIBRATION': 0}

        self.olive_compression_tables = {
            'GENDER': {'option': {'Male': 1,
                                  'Female': 2,
                                  'Unknown': 0},
                       'value': tk.StringVar()},

            'TONAL': {'option': {'Tonal': 1,
                                 'Non-Tonal': 0},
                      'value': tk.StringVar()},

            'EXPERIENCE': {'option': {'Experienced': 0,
                                      'New User': 1},
                           'value': tk.StringVar()},

            'FREQUENCY': {'option': audiogram_table,
                          'value': audiogram_table},

            'AUDIOGRAM_LEFT': {'option': 0,
                               'value': (0,) * 9},

            'AUDIOGRAM_RIGHT': {'option': 0,
                                'value': (0,) * 9},

            'SPEAKER_CALIBRATION': {'option': 0,
                                    'value': default_speaker_calibration}
        }

        self.olive_compression_tables['GENDER']['value'].set('Male')
        self.olive_compression_tables['TONAL']['value'].set('Tonal')
        self.olive_compression_tables['EXPERIENCE']['value'].set('Experienced')

        self.textbox_audiogram_left = [tk.IntVar()] * 9
        self.textbox_audiogram_right = [tk.IntVar()] * 9
        self.textbox_speakerCalibration = [tk.Entry(None)] * 2

        self.create_plot()

        self.protocol("WM_DELETE_WINDOW", self.on_exit)

    def exit_plot(self):
        if self.dsp_thread.active_id_thread is not None:
            self.dsp_thread.active_id_thread.terminate()
            queue_process.__init__()
            self.plot.reset_plot()
        else:
            queue_process.__init__()
            self.plot.reset_plot()
            pass

    def on_exit(self, value=None):
        if value is None:
            if messagebox.askokcancel("Close", "Do you want to quit?", parent=self):
                self.plot.quit()

                self.olive_frame.destroy()
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
                    self.olive_flags[flag_name] = 0
                    self.top_equalizer.destroy()
                else:
                    pass
            elif flag_name == 'ATTACK&RELEASE':
                if messagebox.askokcancel("Close", "Do you want to quit the set?", parent=self.top_attack_release):
                    self.olive_flags[flag_name] = 0
                    self.top_attack_release.destroy()
                else:
                    pass
            elif flag_name == 'COMPRESSION':
                if messagebox.askokcancel("Close", "Do you want to quit the set?", parent=self.top_compression):
                    self.olive_flags[flag_name] = 0
                    self.top_compression.destroy()
                else:
                    pass
            elif flag_name == 'SET_CALIBRATION':
                if messagebox.askokcancel("Close", "Do you want to quit the set?", parent=self.top_setting_calibration):
                    self.olive_flags[flag_name] = 0
                    self.top_setting_calibration.destroy()
                else:
                    pass
            else:
                pass

    def on_exit_eq(self):
        self.on_exit(("EQ",))

    def on_exit_ar(self):
        self.on_exit(("ATTACK&RELEASE",))

    def on_exit_cp(self):
        self.on_exit(("COMPRESSION",))

    def on_exit_sc(self):
        self.on_exit(("SET_CALIBRATION",))

    def fft_bins(self, value):
        self.olive_features['NFFT'] = value

    def overlap_percent(self, value):
        self.olive_features['overlap_percent'] = value

    def nr_onoff(self):
        state = self.state__.noise_reduction
        if state:
            state = ~state
            self.state__.noise_reduction = state
            create_buttons(self.olive_frame, 11, 1, "tomato", "Noise Reduction", self.nr_onoff)
            print(f"NoiseReduction OFF")
        else:
            state = ~state
            self.state__.noise_reduction = state
            create_buttons(self.olive_frame, 11, 1, "light green", "Noise Reduction", self.nr_onoff)
            print(f"NoiseReduction ON")

    def fb_onoff(self):
        state = self.state__.feedback_cancellation
        if state:
            state = ~state
            self.state__.feedback_cancellation = state
            create_buttons(self.olive_frame, 13, 1, "tomato", "Feedback Cancellation", self.fb_onoff)
            print(f"FeedbackCancellation OFF")
        else:
            state = ~state
            self.state__.feedback_cancellation = state
            create_buttons(self.olive_frame, 13, 1, "light green", "Feedback Cancellation", self.fb_onoff)
            print(f"FeedbackCancellation ON")

    def compression(self):
        if self.olive_flags["COMPRESSION"] == 1:
            pass
        else:
            self.open_window("COMPRESSION")

    def setEq(self):
        if self.olive_flags["EQ"] == 1:
            pass
        else:
            self.open_window("EQ")

    def attack_release(self):
        if self.olive_flags["ATTACK&RELEASE"] == 1:
            pass
        else:
            self.open_window("ATTACK&RELEASE")

    def setSpeakerCalibration(self):
        if self.olive_flags["SET_CALIBRATION"] == 1:
            pass
        else:
            self.open_window("SET_CALIBRATION")

    def set_eq_coefficent(self):
        for index in range(len(self.olive_features['EQ'])):
            self.olive_features['EQ'][index] = olive_features_ref['EQ'][index]

        self.olive_flags['EQ'] = 0
        self.top_equalizer.destroy()

    def set_ar_coefficent(self):
        self.olive_features['Attack_coeff'] = olive_features_ref['Attack_coeff']
        self.olive_features['Release_coeff'] = olive_features_ref['Release_coeff']

        self.olive_flags['ATTACK&RELEASE'] = 0
        self.top_attack_release.destroy()

    def set_comp(self):
        audiogram_left = [0] * len(self.textbox_audiogram_left)
        audiogram_right = [0] * len(audiogram_left)

        try:
            for index, left_value in enumerate(self.textbox_audiogram_left):
                if left_value.get() == '':
                    left = 0
                else:
                    left = int(left_value.get())

                if self.textbox_audiogram_right[index].get() == '':
                    right = 0
                else:
                    right = int(self.textbox_audiogram_right[index].get())
                audiogram_left[index] = left
                audiogram_right[index] = right

            self.olive_compression_tables['AUDIOGRAM_LEFT']['value'] = tuple(audiogram_left)
            self.olive_compression_tables['AUDIOGRAM_RIGHT']['value'] = tuple(audiogram_right)

            self.olive_flags['COMPRESSION'] = 0
            self.top_compression.destroy()

        except ValueError:
            messagebox.showerror("error", 'ValueError: invalid literal for integer with base 10:',
                                 parent=self.top_compression)

    def set_sc(self):
        num_channel = self.textbox_speakerCalibration[0].get()
        text = self.textbox_speakerCalibration[1].get().split(',')
        if text[-1] == '':
            text = text[:-1]
        else:
            if len(text) != int(num_channel):
                messagebox.showerror("error", "value wrong: the number of channel is mismatched",
                                     parent=self.top_setting_calibration)
            else:
                try:
                    for index, val in enumerate(text):
                        text[index] = float(val)

                    self.olive_compression_tables['SPEAKER_CALIBRATION']['value'] = tuple(text)

                    # Close the tk
                    self.olive_flags['SET_CALIBRATION'] = 0
                    self.top_setting_calibration.destroy()
                except ValueError:
                    messagebox.showerror("error", 'ValueError: invalid literal for float() with base 10:',
                                         parent=self.top_setting_calibration)

    def open_window(self, value):
        if self:
            if value == "EQ":
                self.olive_flags[value] = 1
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
                                    "vertical", self.olive_features['EQ'][index], 100,
                                    'Red', value, get_eq_coeff)
                    x = x + 1
                    y = 1

                self.top_equalizer.protocol("WM_DELETE_WINDOW", self.on_exit_eq)
                create_buttons(eq_frame, int(x / 2) - 1, 3, None, "SET VALUE", self.set_eq_coefficent)

            elif value == "COMPRESSION":
                self.olive_flags[value] = 1
                self.top_compression = tk.Toplevel()
                cp_frame = ttk.LabelFrame(self.top_compression, text="Compressor", height=270, width=100)
                cp_frame.grid(row=6, columnspan=10, sticky='WE',
                              padx=5, pady=5, ipadx=5, ipady=5)

                # Title
                create_label(cp_frame, 1, 0, 'NALNL2 TEST')

                number_compression_features = len(self.olive_compression_tables.keys())
                for index, name_data in enumerate(self.olive_compression_tables.keys()):
                    create_label(cp_frame, 0, index + 1, name_data)

                create_drop(cp_frame, 1, 1,
                            self.olive_compression_tables['GENDER']['value'],
                            self.olive_compression_tables['GENDER']['option'].keys())

                create_drop(cp_frame, 1, 2,
                            self.olive_compression_tables['TONAL']['value'],
                            self.olive_compression_tables['TONAL']['option'].keys())

                create_drop(cp_frame, 1, 3,
                            self.olive_compression_tables['EXPERIENCE']['value'],
                            self.olive_compression_tables['EXPERIENCE']['option'].keys())

                x_index = 1
                for index, frequency in enumerate(self.olive_compression_tables['FREQUENCY']['option']):
                    create_label(cp_frame, x_index, 4, frequency)
                    self.textbox_audiogram_left[index] = create_textbox(parent=cp_frame,
                                                                        location_x=x_index,
                                                                        location_y=5,
                                                                        value=
                                                                        self.olive_compression_tables['AUDIOGRAM_LEFT']
                                                                        ['value'][index])
                    self.textbox_audiogram_right[index] = create_textbox(parent=cp_frame,
                                                                         location_x=x_index,
                                                                         location_y=6,
                                                                         value=self.olive_compression_tables[
                                                                             'AUDIOGRAM_RIGHT']
                                                                         ['value'][index])
                    x_index += 1

                create_buttons(cp_frame, 1, 7, None, "OPEN CALIBRATION SETTING",
                               self.setSpeakerCalibration)

                create_buttons(cp_frame, 5, number_compression_features + 2, None, "SET VALUE", self.set_comp)
                self.top_compression.protocol("WM_DELETE_WINDOW", self.on_exit_cp)

            elif value == "ATTACK&RELEASE":
                self.olive_flags[value] = 1
                self.top_attack_release = tk.Toplevel()
                # Attack & Release
                ar_frame = ttk.LabelFrame(self.top_attack_release, text=" Attack & Release ", height=150, width=500)
                ar_frame.grid(row=4, columnspan=10, sticky='WE',
                              padx=5, pady=5, ipadx=5, ipady=5)

                # Attack Coefficients
                create_label(ar_frame, 1, 1, "Attack Coefficients")
                create_scale(ar_frame, 2, 1, 0.005, .2, 0.005, "horizontal", self.olive_features["Attack_coeff"],
                             700, 'Red', get_attack_coeff)

                # Release Coefficients
                create_label(ar_frame, 1, 10, "Release Coefficients")
                create_scale(ar_frame, 2, 10, 0.1, 2, 0.1, "horizontal", self.olive_features["Release_coeff"], 700,
                             'Red', get_release_coeff)

                self.top_attack_release.protocol("WM_DELETE_WINDOW", self.on_exit_ar)
                create_buttons(ar_frame, 1, 3 + 11, None, "SET VALUE", self.set_ar_coefficent)

            elif value == "SET_CALIBRATION":
                self.olive_flags[value] = 1
                self.top_setting_calibration = tk.Toplevel()
                setting_calibration_frame = ttk.LabelFrame(self.top_setting_calibration,
                                                           text="Setting for Speaker Calibration",
                                                           height=270, width=100)
                setting_calibration_frame.grid(row=6, columnspan=10, sticky='WE',
                                               padx=5, pady=5, ipadx=5, ipady=5)

                create_label(setting_calibration_frame, 0, 0, 'The number of Channel')
                self.textbox_speakerCalibration[0] = create_textbox_custom(setting_calibration_frame, 0, 1, 100,
                                                                           len(self.olive_compression_tables[
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
        if value == "EQ":
            for index in range(len(self.olive_features['EQ'])):
                self.olive_features['EQ'][index] = 0
                olive_features_ref['EQ'][index] = 0

        elif value == "COMPRESSION":
            print()

        elif value == "ATTACK&RELEASE":
            self.olive_features['Attack_coeff'] = 0.005
            self.olive_features['Release_coeff'] = 0.1
            olive_features_ref['Attack_coeff'] = 0.005
            olive_features_ref['Release_coeff'] = 0.1

    def debug_compression_table(self):

        print(f"----COMPRESSION TABLE----\n"
              f" GENDER: {self.olive_compression_tables['GENDER']['value'].get()}\n"
              f" TONAL: {self.olive_compression_tables['TONAL']['value'].get()}\n"
              f" EXPERIENCE: {self.olive_compression_tables['EXPERIENCE']['value'].get()}\n"
              f" AUDIOGRAM\n"
              f" LEFT: {self.olive_compression_tables['AUDIOGRAM_LEFT']['value']}\n"
              f" RIGHT: {self.olive_compression_tables['AUDIOGRAM_RIGHT']['value']}\n"
              f" SPEAKER CALIBRATION: {self.olive_compression_tables['SPEAKER_CALIBRATION']['value']}")

    def debug(self):
        print(f"-----------------------------DEBUG--------------------------------")
        print(f"Olive Value: ")

        print(f" Number of FFT: {self.olive_features['NFFT']}")
        print(f" Overlap(%): {self.olive_features['overlap_percent']}")

        print(f"Attack & Release: ")
        print(f" Attack: {self.olive_features['Attack_coeff']} ", end='')
        print(f" Release: {self.olive_features['Release_coeff']}")
        if self.state__.attack_release:
            print(f" State: ON")
        else:
            print(f" State: OFF")

        print(f"Noise Reduction: ")
        if self.state__.noise_reduction:
            print(f" State: ON")
        else:
            print(f" State: OFF")

        print(f"Feedback Cancellation: ")
        if self.state__.feedback_cancellation:
            print(f" State: ON")
        else:
            print(f" State: OFF")

        print(f"Compression: ")
        if self.state__.compression:
            print(f" State: ON")
        else:
            print(f" State: OFF")

        print(f"Equalizer: ")
        print(" ", end='')
        for value in self.olive_features['EQ']:
            print(f"{value} ", end='')
        print()
        if self.state__.equalizer:
            print(f" State: ON")
        else:
            print(f" State: OFF")

        print()
        print(f"Test Value {self.test_coff}")
        print(f"---------------------------------------------------------------------")
        self.debug_compression_table()

    def set_effect(self):
        """
        Apply effect to plot
        """
        self.test_coff = self.test_coff + 1

        # Complete message
        messagebox.showinfo("", "Complete!")

    def create_widgets(self):
        # Microphone
        create_label(self.olive_frame, 1, 1, "MIC")
        create_arrow(self.olive_frame, 2, 1)

        # Overlap %
        create_label(self.olive_frame, 3, 1, "Overlap %")
        create_scale(self.olive_frame, 3, 2, 25, 75, 25, "horizontal", 75, 90, 'Black', self.overlap_percent)
        create_arrow(self.olive_frame, 4, 1)

        # Number of FFT bins
        create_label(self.olive_frame, 5, 1, "Number of FFT bins")
        create_scale(self.olive_frame, 5, 2, 64, 512, 64, "horizontal", 128, 90, 'Black', self.fft_bins)
        create_arrow(self.olive_frame, 6, 1)

        # Energy
        create_label(self.olive_frame, 7, 1, "Energy")
        create_arrow(self.olive_frame, 8, 1)

        # Attack & Release
        create_buttons(self.olive_frame, 9, 1, "light green", "Attack/Release", self.attack_release)
        create_arrow(self.olive_frame, 10, 1)

        # Noise Reduction
        create_buttons(self.olive_frame, 11, 1, "tomato", "Noise Reduction", self.nr_onoff)
        create_arrow(self.olive_frame, 12, 1)

        # Feedback Cancellation
        create_buttons(self.olive_frame, 13, 1, "tomato", "Feedback Cancellation", self.fb_onoff)
        create_arrow(self.olive_frame, 14, 1)

        # Compression
        create_buttons(self.olive_frame, 15, 1, "light green", "Compression", self.compression)
        create_arrow(self.olive_frame, 16, 1)

        # Equalizer
        create_buttons(self.olive_frame, 17, 1, "light green", "Equalizer", self.setEq)
        create_arrow(self.olive_frame, 18, 1)

        # iFFT
        create_label(self.olive_frame, 19, 1, "iFFT")
        create_arrow(self.olive_frame, 20, 1)

        # Speaker
        create_label(self.olive_frame, 21, 1, "Speaker")

        # Debug
        create_buttons(self.olive_frame, 11, 2, "light green", "Debug Value", self.debug)

        # Set Effect
        create_buttons(self.olive_frame, 12, 2, "light green", "    Set    ", self.set_effect)

        create_buttons(self.plot_option_frame, 10, 1, "light green", "queue", get_queue)
        create_buttons(self.plot_option_frame, 11, 1, "light green", "delete the plot", self.exit_plot)

    def launch_dsp(self, evt=None):
        # if self.dsp_thread is None:
        #     self.dsp_thread.stop()
        self.dsp_thread.set_onoff(('test', self.test_coff))

    def create_plot(self):
        interface_frame = ttk.Frame(self.plot_option_frame)
        interface_frame.grid(row=1, column=9, sticky='WE',
                             padx=5, pady=5, ipadx=5, ipady=5)

        create_buttons(interface_frame, 9, 1, "light green", "DSP ON", self.launch_dsp)
        # divide time and amplitude domain

        # convert to data using fft to frequency domain

        # divide frequency and gain domain


def update_queue(data_queue, simulator):
    while True:
        if data_queue.empty():
            pass
        else:
            frame = data_queue.get_nowait()
            # simulator to plot
            simulator.plot.update_(frame)

        time.sleep(0.001)


def main():
    # Create the entire GUI program
    root = olivesimulator(sampling_rate=44100)

    from sthread import sthreading
    thread_UpdateMainQueue = sthreading.sThread(name="UpdateMainQueueThread", target=update_queue, args=(queue_process, root))
    thread_UpdateMainQueue.start()

    # Start the GUI event loop
    root.mainloop()


if __name__ == "__main__":
    main()
