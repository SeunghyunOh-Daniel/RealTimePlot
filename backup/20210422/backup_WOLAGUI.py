import sys
import os

from scipy.io import wavfile

print(os.getcwd())
# pyaudio address
sys.path.append("/EQInterpolation/env_OliveGUI/Lib/site-packages")
sys.path.append("../../src/")
sys.path.append("../../lib/")

import tkinter as tk
from tkinter import ttk
import pyaudio

# from Audio_mic_stream_GUI import *

import ctypes
import matplotlib

matplotlib.use('TkAgg')

try:
    from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk as nav_tool
except:
    from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg as nav_tool

import time

user32 = ctypes.windll.user32
screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
percentOfWidth = 0.86
percentOfHeight = 0.85

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

# # just some arbitrary command for demonstration
# cmd = [sys.executable, '-c', """import sys, time
# print("!")
# sys.stdout.flush()
# for i in range(30):
#     sys.stdout.write("%d " % i)
#     sys.stdout.flush()
#     time.sleep(.05)
# """]

# sys.stdout.flush()
# time.sleep(.05)

# class data_table(object):
#     def __init__(self):


import config
from realtime_dsp.real_time_dsp_v2 import *
import threading
import queue
import scipy.io.wavfile as wav


def import_wav(path):
    import os
    file_list = []
    for file in os.listdir(path):
        if file.split(".")[-1] == "wav":
            file_list.append(path + "/" + file)
    return file_list


# import wav file or mic data
shared_frames = queue.Queue()

print(f"file export: {config.local_data_path}")
wav_list = import_wav(config.local_data_path)
file_wav = wav_list[0]
print(f"File: {file_wav}")
sampling_frequency, data_wav = wav.read(file_wav)
rate_down_sampling = 1


# sampling_frequency = 0

# Processing Time: 0.00012460000000014126 sec
def get_input_frame(input_frame):
    input_frame_local = input_frame
    shared_frames.put((len(input_frame_local), input_frame_local))
    global data

    return input_frame_local


# Processing Time: 0.04665140000000001 sec
def _update(plotter):
    while True:
        frame = None
        if shared_frames.empty():
            pass
        else:
            frame = shared_frames.get_nowait()
        plotter.get_frame_(frame)
        time.sleep(1e-3)


# down sampling, 0.3690628 sec/each trial
def down_sampling(sampling_frequency, data_wav, sample_rate):
    import math
    down_sample_rate = sample_rate
    filename_down_sampling = '../../src/down_sampling.wav'
    filepath = "./" + filename_down_sampling
    if sampling_frequency % down_sample_rate != 0:
        raise ValueError

    data_down_sampling = np.array([data_wav[down_sample_rate * i]
                                   for i in range(math.trunc(len(data_wav) / down_sample_rate))])
    if np.dtype(data_down_sampling[0]) == "float64":
        data_down_sampling = np.float32(data_down_sampling)
    else:
        pass

    wav.write(filename_down_sampling, int(sampling_frequency / down_sample_rate), data_down_sampling)
    sampling_frequency, data_wav = wav.read('./' + filename_down_sampling)

    return sampling_frequency, filepath


class statement(object):
    def __init__(self):
        self.attack_release = True
        self.noise_reduction = False
        self.feedback_cancellation = False
        self.compression = True
        self.equalizer = True


# Create buttons
def create_buttons(parent, location_x, location_y, backgroundcolor, name, cmdtrig):
    button = tk.Button(parent, bg=backgroundcolor, text=name, relief=tk.RAISED, borderwidth=2, command=cmdtrig)
    button.grid(row=location_y, column=location_x, sticky=tk.E + tk.W + tk.N + tk.S, pady=30, padx=20)


# Create labels
def create_label(parent, location_x, location_y, name="NO-NAME-SET"):
    label = tk.Label(parent, text=name)
    label.grid(row=location_y, column=location_x, sticky=tk.E + tk.W + tk.N + tk.S, pady=30, padx=20)


# Create buttons
def create_scale(parent, location_x, location_y, start, end, resolution, typeorient, default, barlen, color,
                 cmdtrig):
    scale = tk.Scale(parent, resolution=resolution, from_=start, to=end, orient=typeorient, length=barlen, fg=color,
                     command=cmdtrig)
    scale.grid(row=location_y, column=location_x, sticky=tk.E + tk.W + tk.N + tk.S, padx=20, pady=20)
    scale.set(default)


# create EQ scale
def create_EQ_scale(parent, location_x, location_y, start, end, resolution, orient, default, barlen, color,
                    channel_number, cmdtrig):
    scale = tk.Scale(parent, resolution=resolution, from_=start, to=end, orient=orient, length=barlen, fg=color,
                     command=lambda func: cmdtrig(channel_number, func))
    scale.grid(row=location_y, column=location_x, sticky=tk.E + tk.W + tk.N + tk.S, padx=20, pady=4)
    scale.set(default)


def create_arrow(parent, location_x, location_y):
    arr = tk.Label(parent, text="\N{RIGHTWARDS BLACK ARROW}")
    arr.grid(row=location_y, column=location_x, sticky=tk.E + tk.W + tk.N + tk.S, pady=20, padx=10)


def get_attack_coeff(value):
    olive_features_ref['Attack_coeff'] = value


def get_release_coeff(value):
    olive_features_ref['Release_coeff'] = value


def get_eq_coefficent(channel, gain):
    for index, val in enumerate(olive_features_ref['frequency']):
        if channel == val:
            olive_features_ref['EQ'][index] = gain
            break


class olivesimulator(object):
    def __init__(self):
        self.master = tk.Tk()
        self.master.title("Hearing Aid Simulator")
        self.master.geometry("%dx%d" % (screensize[0] * percentOfWidth, screensize[1] * percentOfHeight))

        # Overall flow
        self.olive_frame = ttk.LabelFrame(self.master, text=" Olive Flowchart ")
        self.olive_frame.grid(row=0, columnspan=10, sticky='WE',
                              padx=5, pady=5, ipadx=5, ipady=5)

        # Top
        self.top_attack_release = tk.Toplevel
        self.top_compression = tk.Toplevel
        self.top_equalizer = tk.Tk

        # Plot
        self.plot_frame = ttk.LabelFrame(self.master, text=" Plot ", width=screensize[0] * 0.4,
                                         height=screensize[1] * 0.6)
        self.plot_frame.grid(row=4, columnspan=10, sticky='WE',
                             padx=5, pady=5, ipadx=5, ipady=5)

        import v2
        self.plot = v2.RealtimePlotter(self.plot_frame,
                                       [(-1, +1)],
                                       size=100,
                                       time=1,
                                       sampling_frequency=sampling_frequency,
                                       show_yvals=True,
                                       window_name='Graph demo',
                                       yticks=[(-1, 0, +1)],
                                       styles=[''],
                                       ylabels=['Plot'],
                                       interval_msec=20,
                                       shared_queue=shared_frames)

        self.process = None
        self.after = self.master.after
        self.command = START
        self.button_text = None
        self.CHUNK = 1024
        self.WIDTH = 2
        self.CHANNELS = 2
        self.RATE = 44100
        self.RECORD_SECONDS = 10
        # self.window.attributes('-fullscreen', True)
        # print("This is a test 2")
        self.create_widgets()
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=self.p.get_format_from_width(self.WIDTH),
                                  channels=self.CHANNELS,
                                  rate=self.RATE,
                                  input=True,
                                  output=True,
                                  frames_per_buffer=self.CHUNK)

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
                            'ATTACK&RELEASE': 0}
        self.create_plot()

        self.master.protocol("WM_DELETE_WINDOW", self.on_exit)

    def on_exit(self, value=None):
        from tkinter import messagebox
        if value is None:
            if messagebox.askokcancel("Close", "Do you want to quit?", parent=self.master):
                self.plot.quit()

                self.olive_frame.destroy()
                self.plot_frame.destroy()
                self.master.destroy()
        else:
            flag_name = value[0]
            if flag_name == 'EQ':
                if messagebox.askokcancel("Close", "Do you want to quit?", parent=self.top_equalizer):
                    self.olive_flags[flag_name] = 0
                    self.top_equalizer.destroy()
                else:
                    pass
            elif flag_name == 'ATTACK&RELEASE':
                if messagebox.askokcancel("Close", "Do you want to quit?", parent=self.top_attack_release):
                    self.olive_flags[flag_name] = 0
                    self.top_attack_release.destroy()
                else:
                    pass
            elif flag_name == 'COMPRESSION':
                if messagebox.askokcancel("Close", "Do you want to quit?", parent=self.top_compression):
                    self.olive_flags[flag_name] = 0
                    self.top_compression.destroy()
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
        self.olive_flags['COMPRESSION'] = 0
        self.top_compression.destroy()

    def open_window(self, value):
        if self.master:
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
                                    'Red', value, get_eq_coefficent)
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

                create_buttons(cp_frame, 1, 1, None, "SET VALUE", self.set_comp)
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

        print(f"---------------------------------------------------------------------")

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

        # Print value
        create_buttons(self.olive_frame, 11, 2, "light green", "Debug Value", self.debug)

    def create_plot(self):

        # divide time and amplitude domain

        # convert to data using fft to frequency domain

        # divide frequency and gain domain

        # Add the real-time plot
        global sampling_frequency
        sampling_frequency, path_data = down_sampling(sampling_frequency, data_wav, rate_down_sampling)
        print(f"Sampling frequency {sampling_frequency}")

        global shared_frames
        self.plot.launch_thread()
        # th_update = threading.Thread(target=_update, name="update",
        #                              args=(plotter,), daemon=True)
        th_extract_data = threading.Thread(target=wave_file_process, name='extract',
                                           args=(path_data,  # in_file_name
                                                 False,  # get_file_details
                                                 "",  # out_file_name
                                                 False,  # progress_bar
                                                 False,  # stereo
                                                 50,  # overlap
                                                 512,  # block_size
                                                 True,  # zero_pad
                                                 get_input_frame,  # pre_proc_func
                                                 None,  # freq_proc_func
                                                 None),  # post_proc_func
                                           daemon=True)
        #
        # th_extract_data = threading.Thread(target=real_time_stream, name='extract',
        #                                    args=((1, 3), sampling_frequency, False, 50, 200, True, get_input_frame, None, None),
        #                                    daemon=True)
        #
        th_extract_data.start()
        # th_update.start()

        # self.create_buttons(self.plot_frame, 4, 10, "light green", "Refresh", None)

    def toggle(self, event_unused=None):
        if self.command is START:
            self.start_process()
            self.command = STOP
            self.button_text.set(self.command)
        else:
            assert self.command is STOP
            self.stop_process()

    def stop(self):
        self.command = START
        self.button_text.set(self.command)

    def start_process(self):
        # data = stream.read(CHUNK)
        # stream.write(data, CHUNK)
        self.stop_process()
        # self.process = Popen(cmd)
        self.process = self.stream_data()

        # for i in range(0, int(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
        #     data = self.stream.read(self.CHUNK)
        #     self.stream.write(data, self.CHUNK)
        def poller():
            if self.process is not None and self.process.poll() is None:
                # process is still running
                self.after(delay, poller)  # continue polling
            else:
                self.stop()

        delay = 100  # milliseconds
        self.after(delay, poller)

    def stream_data(self):
        for i in range(0, int(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
            data = self.stream.read(self.CHUNK)
            # data_mod=wave_file_process(data,False,olive_features['overlap_percent'],olive_features['NFFT'],olive_features['overlap_percent'],olive_features['overlap_percent'])
            self.stream.write(data, self.CHUNK)

    def stop_process(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            # kill process in a couple of seconds if it is not terminated
            self.after(2000, kill_process, self.process)
            self.stream.stop_stream()
            self.stream.close()
            self.p.terminate()
        self.process = None


def kill_process(process):
    if process is not None and process.poll() is None:
        process.kill()
        process.wait()


# Create the entire GUI program
program = olivesimulator()

# Start the GUI event loop
program.master.mainloop()

##############################################################################################################


# import wav file or mic data
print(config.local_data_path)

wav_list = import_wav(config.local_data_path)
sampling_rate, data = wavfile.read(wav_list[0])

# divide time and amplitude domain

# convert to data using fft to frequency domain

# divide frequency and gain domain

# Add the real-time plot


# global sampling_frequency
# file_wav = wav_list[0]
# sampling_frequency, data_wav = wav.read(file_wav)
# print(f"File: {file_wav}")
#
# sampling_frequency, path_data = down_sampling(sampling_frequency, data_wav, 1)
# # sampling_frequency = 44100
# plotter = Plotter(sampling_frequency)
#
#
# tk = tk.Ttk()
# canvas = FigureCanvasTkAgg(plotter.get_fig(), master=self.plot_frame)
#
# # canvas.draw()
# # canvas.get_tk_widget().grid(row=1, column=1, columnspan=10,
# #                             padx=5, pady=5, ipadx=5, ipady=5)
#
# toolbar = nav_tool(canvas, self.plot_frame)
# toolbar.update()
#
# canvas._tkcanvas.pack(fill=tk.BOTH, expand=1)
#
# # th_update = threading.Thread(target=_update, name="update",
# #                              args=(plotter,), daemon=True)
# #
# # th_extract_data = threading.Thread(target=wave_file_process, name='extract',
# #                                    args=(
# #                                        path_data, False, "", False, False, 50, 512, True, get_input_frame, None, None),
# #                                    daemon=True)
# #
# # # th_extract_data = threading.Thread(target=real_time_stream, name='extract',
# # #                                    args=((1, 3), sampling_frequency, False, 50, 200, True, get_input_frame, None, None),
# # #                                    daemon=True)
# #
# # th_extract_data.start()
# # th_update.start()
# #
# #
# # import matplotlib.animation as animation
# #
# # ani = animation.FuncAnimation(plotter.get_fig(), plotter.animate_frame, interval=plotter.interval_msec, blit=True)
# # plt.show()
