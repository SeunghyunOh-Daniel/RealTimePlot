import queue
import scipy.io.wavfile as wav
import numpy as np
from plot import Plotter
import threading
import time

def import_wav(path):
    import os
    file_list = []
    for file in os.listdir(path):
        if file.split(".")[-1] == "wav":
            file_list.append(path + "/" + file)
    return file_list


# import wav file or mic data
shared_frames = queue.Queue()

wav_list = import_wav("/")

# Processing Time: 0.00012460000000014126 sec
def get_input_frame(input_frame):
    input_frame_local = input_frame
    shared_frames.put(input_frame_local)
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
    filename_down_sampling = 'down_sampling.wav'
    filepath = "./" + filename_down_sampling
    if sampling_frequency % down_sample_rate != 0:
        raise ValueError

    data_down_sampling = np.array([data_wav[down_sample_rate * i]
                                   for i in range(math.trunc(len(data_wav) / down_sample_rate))])
    if np.dtype(data_down_sampling[0]) == "float64":
        data_down_sampling = np.float32(data_down_sampling)
    else:
        pass

    wav.write(filepath, int(sampling_frequency / down_sample_rate), data_down_sampling)
    sampling_frequency, data_wav = wav.read('./' + filename_down_sampling)

    return sampling_frequency, filepath

def main():
    print("Threading plot and real time dsp")
    global sampling_frequency
    file_wav = wav_list[0]
    sampling_frequency, data_wav = wav.read(file_wav)
    print(f"File: {file_wav}")

    sampling_frequency, path_data = down_sampling(sampling_frequency, data_wav, 1)
    # sampling_frequency = 44100
    plotter = Plotter(sampling_frequency)

    th_update = threading.Thread(target=_update, name="update",
                                 args=(plotter,), daemon=True)

    from real_time_dsp_v2 import wave_file_process
    th_extract_data = threading.Thread(target=wave_file_process, name='extract',
                                       args=(
                                           path_data, False, "", False, False, 50, 512, True, get_input_frame, None, None),
                                       daemon=True)

    th_extract_data.start()
    th_update.start()

    plotter.start()

if __name__=="__main__":
    main()