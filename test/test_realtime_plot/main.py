import tkinter as tk
from tkinter import ttk
import ctypes
import matplotlib

matplotlib.use('TkAgg')

try:
    from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk as nav_tool
except:
    from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg as nav_tool

user32 = ctypes.windll.user32
screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
percentOfWidth = 0.86
percentOfHeight = 0.85

from realtime_dsp.real_time_dsp_v2 import *
from realtime_plot.real_time_plot import RealtimePlotter
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

wav_list = import_wav("./")
file_wav = wav_list[0]

sampling_frequency, data_wav = wav.read(file_wav)
rate_down_sampling = 1


# Processing Time: 0.00012460000000014126 sec
def get_input_frame(input_frame):
    input_frame_local = input_frame
    shared_frames.put((len(input_frame_local), input_frame_local))
    return input_frame_local


# down sampling, 0.3690628 sec/each trial
def down_sampling(sampling_frequency, data_wav, sample_rate):
    import math
    down_sample_rate = sample_rate
    filename_down_sampling = './down_sampling.wav'
    filepath = filename_down_sampling
    if sampling_frequency % down_sample_rate != 0:
        raise ValueError

    data_down_sampling = np.array([data_wav[down_sample_rate * i]
                                   for i in range(math.trunc(len(data_wav) / down_sample_rate))])

    if np.dtype(data_down_sampling[0]) == "float64":
        data_down_sampling = np.float32(data_down_sampling)
    else:
        pass

    wav.write(filepath, int(sampling_frequency / down_sample_rate), data_down_sampling)
    sampling_frequency, data_wav = wav.read(filepath)

    return sampling_frequency, filepath


class plot_simulator(object):
    def __init__(self):
        self.master = tk.Tk()
        self.master.title("Plot Simulator")

        # Plot
        self.plot_frame = ttk.LabelFrame(self.master,
                                         text=" Plot ",
                                         width=screensize[0] * 0.4,
                                         height=screensize[1] * 0.6)
        self.plot_frame.grid(row=4,
                             columnspan=10,
                             sticky='WE',
                             padx=5,
                             pady=5,
                             ipadx=5,
                             ipady=5)


        self.plot = RealtimePlotter(self.plot_frame,
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

        self.create_plot()

        self.master.protocol("WM_DELETE_WINDOW", self.exit)

    def exit(self):
        from tkinter import messagebox
        if messagebox.askokcancel("Close", "Do you want to quit?", parent=self.master):
            self.plot.quit()
            self.master.destroy()

    def create_plot(self):
        # Add the real-time plot
        global sampling_frequency
        sampling_frequency, path_data = down_sampling(sampling_frequency=sampling_frequency,
                                                      data_wav=data_wav,
                                                      sample_rate=rate_down_sampling)

        global shared_frames
        self.plot.launch_thread()
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
        th_extract_data.start()


if __name__ == "__main__":
    # Create the entire GUI program
    program = plot_simulator()

    # Start the GUI event loop
    program.master.mainloop()
