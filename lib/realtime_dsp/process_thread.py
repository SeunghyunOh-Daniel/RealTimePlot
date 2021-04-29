import os
import queue
import threading
import time

import config
import numpy as np
import scipy.io.wavfile as wav
from sthread import sthreading


def import_wav(path):
    file_list = []
    for file in os.listdir(path):
        if file.split(".")[-1] == "wav":
            file_list.append(path + "/" + file)
    return file_list


# Processing Time: 0.00012460000000014126 sec
def get_input_frame(input_frame, data_queue, effect):
    input_frame_local = input_frame
    if effect is None:
        val_coff = 1
    else:
        val_coff = effect
    # Process
    input_frame_local = input_frame / val_coff

    # update dsp frame to main
    data_queue.put((len(input_frame_local), input_frame_local))
    return input_frame_local


def get_input_frame_fft(input_frame):
    input_frame_local = input_frame
    return input_frame_local


def get_input_frame_ifft(input_frame):
    input_frame_local = input_frame
    return input_frame_local


# down sampling, 0.3690628 sec/each trial
def down_sampling(sampling_frequency, data_wav, sample_rate):
    import math
    down_sample_rate = sample_rate
    filename_down_sampling = 'src/down_sampling.wav'
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


# import wav file or mic data
print(f"file export: {config.local_data_path}")
wav_list = import_wav(config.local_data_path)
file_wav = wav_list[0]

print(f"File: {file_wav}")
sampling_frequency, data_wav = wav.read(file_wav)
rate_down_sampling = 1

sampling_frequency, path_data = down_sampling(sampling_frequency, data_wav, rate_down_sampling)
print(f"Sampling frequency {sampling_frequency}")


class ProcessThread(sthreading.sThread):
    def __init__(self, shared_frame):
        super().__init__(name="ProcessThread")
        self.active_thread_list = []
        self.shared_frame = shared_frame
        self.shared_coff = queue.Queue()
        self.switch = 0
        self.active_id_thread = None

        self.d_thread = None

        self.dsp_features = {'overlap_percent': 75,
                             'NFFT': 256,
                             'Attack_coeff': 0.00125,
                             'Release_coeff': 0.00125,
                             'AttackRelease': "OFF",
                             'NR': "OFF",
                             'FB': "OFF",
                             'COMPRESSION': "OFF",
                             'EQ': [0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.1],
                             'frequency': [100, 250, 500, 1000, 2000, 3000, 4000, 6000, 8000],
                             'test': 1}

        # mic stream version(NOT YET)
        # th_extract_data = threading.Thread(target=real_time_stream, name='extract',
        #                                    args=((1, 3), sampling_frequency, False, 50, 200, True, get_input_frame, None, None),
        #                                    daemon=True)

        # th_extract_data.start()

    def set_onoff(self, coff):
        if self.active_id_thread in threading.enumerate():
            pass
        else:
            self.switch = not self.switch
            self.set_coff(coff)

    def run(self):
        while self._flag:
            time.sleep(0.001)
            if self.switch:
                from realtime_dsp.real_time_dsp_v2 import wave_file_process

                if self.shared_coff.qsize() > 0:
                    effect = self.shared_coff.get_nowait()
                else:
                    effect = None

                d_thread = sthreading.sThread(name="WaveFileProcessThread")
                d_thread.target = wave_file_process
                d_thread.args = (path_data,  # in_file_name
                                 False,  # get_file_details
                                 "",  # out_file_name
                                 False,  # progress_bar
                                 False,  # stereo
                                 50,  # overlap
                                 512,  # block_size
                                 True,  # zero_pad
                                 get_input_frame,  # pre_proc_func
                                 get_input_frame_fft,  # freq_proc_func
                                 get_input_frame_ifft,  # post_proc_func
                                 self.shared_frame,
                                 effect)
                d_thread.start()
                self.active_id_thread = d_thread
                self.switch = not self.switch
            else:
                pass
        else:
            pass
            time.sleep(0.001)

    def set_coff(self, coff):
        """

        """
        print(f"Value change {self.dsp_features[coff[0]]} ", end="")
        self.dsp_features[coff[0]] = coff[1]
        self.shared_coff.put(self.dsp_features[coff[0]])
        print(f"-> {self.dsp_features[coff[0]]}")
