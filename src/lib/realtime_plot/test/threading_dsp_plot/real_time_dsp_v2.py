##################################################################################################
#                                                                                                #
#                                 Real time DSP process Lib                                      #
#                                                                                                #
##################################################################################################
'''
    This library provides an easy solution to apply new algorithms with
    no need to stress with the frame overlap for that. 

    There are different functions depending in the data input:

    -----------------------------------------------------------------------------------
    # wave_file_process
    Function reads a wave file and call the processing functions entered by the user
    User can return the process data or save it in an wav file
        * Params:
        - in_file_name: the wave file name (with full directory)
        - get_file_details: returns the wav file details in form of dictionary with keys
                            name, samplerate, channels, length_samples, length_seconds and
                            data_type
        - out_file_name: the output wav file name. If empty will return processed data in 
                        python list format.  
        - stereo: True for stereo, False for mono (left will be used for mono). If the 
                  input file is mono, left data will be copied to right.
        - overlap: 50% (50) or 75% (75) overlap options
        - block_size: The number of input samples per frame
        - zero_pad: Add nff/2 zeros in each frame, reducing by half the input frame
        of the system. For example, if overlap is 50% and NFFT is 256 point, each 
        time domain frame will have 64 new samples per loop if zero pad is True 
        and 128 if zero pad is False.
        - pre_proc_func: The time domain preprocess function
            * Inputs: The current time domain frames 
            * Output: Should return the same object as the input with processed data
            * Format: Python list of float objects
                      ([1,2,3...] for mono [[1,2,3..][1,2,3..]] for stereo)
        - freq_proc_func: The frequency domain process function
            * Inputs: The current frequency domain frames with real and imaginary
                    components of size (nfft/2)+1 (non normalized) 
            * Output: Should return the same object as the input with processed data
            * Format: Python list of numpy.complex128 objects 
                      ([1,2,3...] for mono [[1,2,3..][1,2,3..]] for stereo)
        - post_proc_func: The time domain postprocess function
            * Inputs: The current time domain frames 
            * Output: Should return the same object as the input with processed data
            * Format: Python list of float objects 
                      ([1,2,3...] for mono [[1,2,3..][1,2,3..]] for stereo)
    -----------------------------------------------------------------------------------
    # real_time_stream
    Function captures and stream data in real time from the device mic and speaker.
        * Params:
        - device: a tuple with the input and output devices number. Use the command:
                 "python3 -m sounddevice" to check the devices available
        - samplerate: the sampling frequency for the audio stream
        - stereo: True for stereo, False for mono (left will be used for mono)
        - overlap: 50% (50) or 75% (75) overlap options
        - block_size: The number of input samples per frame
        - zero_pad: Add nff/2 zeros in each frame, reducing by half the input frame
        of the system. For example, if overlap is 50% and NFFT is 256 point, each 
        time domain frame will have 64 new samples per loop if zero pad is True 
        and 128 if zero pad is False.
        - pre_proc_func: The time domain preprocess function
            * Inputs: The current time domain frames 
            * Output: Should return the same object as the input with processed data
            * Format: Python list of float objects
                      ([1,2,3...] for mono [[1,2,3..][1,2,3..]] for stereo)
        - freq_proc_func: The frequency domain process function
            * Inputs: The current frequency domain frames with real and imaginary
                    components of size (nfft/2)+1 (non normalized) 
            * Output: Should return the same object as the input with processed data
            * Format: Python list of numpy.complex128 objects 
                      ([1,2,3...] for mono [[1,2,3..][1,2,3..]] for stereo)
        - post_proc_func: The time domain postprocess function
            * Inputs: The current time domain frames 
            * Output: Should return the same object as the input with processed data
            * Format: Python list of float objects 
                      ([1,2,3...] for mono [[1,2,3..][1,2,3..]] for stereo)

    NOTES: Current the limitation is only samplerate 16kHz or below
    -----------------------------------------------------------------------------------

'''
########################################## Imports #############################################
import math
import numpy as np
import scipy.io.wavfile as wav
import sounddevice as sd
import soundfile as sf
import sys
import time as tm
from config import *

######################################### WAV File Process #############################################

def _print_progress (iteration, total, prefix = '', suffix = '', decimals = 1, barLength = 50):
    formatStr = "{0:." + str(decimals) + "f}"
    percent = formatStr.format(100 * (iteration / float(total)))
    filledLength = int(round(barLength * iteration / float(total)))
    bar = '#' * filledLength + '-' * (barLength - filledLength)
    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percent, '%', suffix)),
    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()

def _get_file_details(in_file_name):

    wav_freq, wav_data = wav.read(in_file_name)
    outdata={}
    outdata["name"]=in_file_name
    outdata["samplerate"]=wav_freq
    try:
        outdata["channels"]=wav_data.shape[1]
        outdata["length_samples"]=wav_data.shape[0]
        outdata["length_seconds"]=wav_data.shape[0] / wav_freq
    except:
        outdata["channels"]=1
        outdata["length_samples"]=len(wav_data)
        outdata["length_seconds"]=len(wav_data) / wav_freq
    if(wav_data.dtype=='int16'): outdata["data_type"]='int16'
    elif(wav_data.dtype=='int32'): outdata["data_type"]='int32'
    elif(wav_data.dtype=='float32'): outdata["data_type"]='float32'

    return outdata

def wave_file_process(in_file_name="",
                      get_file_details=False,
                      out_file_name="",
                      progress_bar=True,
                      stereo=True,
                      overlap=75,
                      block_size=128,
                      zero_pad=True,
                      pre_proc_func=None,
                      freq_proc_func=None,
                      post_proc_func=None):

    if not get_file_details:
        print("\n#################  Wave File Process #################")

    # Errors check before do any process
    if in_file_name=="":
        if flag_debug:
            import debug
            debug.print_debug()
        print("ERROR: No wav file name entered") 
        return None

    # Returns the details from file name entered
    if get_file_details:
        return _get_file_details(in_file_name)

    if (pre_proc_func==None) and (freq_proc_func==None) and (post_proc_func==None):
        print("WARNING: No process function entered, no process will be applied to the file")
        func_bool=input("Do you want to continue (Y/n) ? ")
        if(func_bool!="Y" and func_bool!="y"):
            return None

    if(overlap!=50 and overlap!=75):
        if flag_debug:
            import debug
            debug.print_debug()
        print("ERROR: Wrong overlap value (50 or 75 only)")
        return None

    if (block_size % 2)!=0:
        if flag_debug:
            import debug
            debug.print_debug()
        print("ERROR: Blocksize value should be even number")
        return None

    print("Processing the "+(in_file_name.split("/")[-1])+" file...")

    #Reading the wave file
    wav_freq, wav_data = wav.read(in_file_name)

    #Checking the input bit depth (no support for 8 and 24 bit PCM) 
    if(wav_data.dtype=='int16'): bit_depth=15
    elif(wav_data.dtype=='int32'): bit_depth=31
    elif(wav_data.dtype=='float32'): bit_depth=0
    elif(wav_data.dtype=='float64'): bit_depth=0
    
    #Checking if input file is stereo and normalizing buffers
    if len(wav_data.shape)==1:
        wav_data_left=wav_data/(2**bit_depth)
        if stereo:
            wav_data_right=wav_data/(2**bit_depth)

    elif len(wav_data.shape)==2:
        if stereo:
            wav_data_left=wav_data[:,0]/(2**bit_depth)
            wav_data_right=wav_data[:,1]/(2**bit_depth)
        else:
            wav_data_left=((wav_data[:,0]/(2**bit_depth))+(wav_data[:,1]/(2**bit_depth)))/2

    #Checking the NFFT value
    nfft=0
    if zero_pad:
        if overlap==75:
            nfft=int(block_size*8)
        else:
            nfft=int(block_size*4)
    else: 
        if overlap==75:
            nfft=int(block_size*4)
        else:
            nfft=int(block_size*2)

    #Checking the FFT frame size
    if zero_pad:
        fft_frame_size=int(nfft/2)
    else:
        fft_frame_size=nfft

    #Checking if the overlap is 50% or 75%
    if overlap==50:
        new_frame_size=int(fft_frame_size/2)
    elif overlap==75:
        new_frame_size=int(fft_frame_size/4)

    #Getting the different frames for left and right
    frames_data_left=[wav_data_left[(i*new_frame_size):(i*new_frame_size+new_frame_size)]  for i in range(int(len(wav_data_left)/new_frame_size))]
    if(stereo): frames_data_right=[wav_data_right[(i*new_frame_size):(i*new_frame_size+new_frame_size)]  for i in range(int(len(wav_data_left)/new_frame_size))]

    #Getting the window function
    hanning= np.array([(0.5-(0.5*math.cos((2*math.pi*i)/(fft_frame_size-1)))) for i in range(fft_frame_size)], dtype='float64')
    #Initializing the static variables used in WOLA operation
    #The final output list with the entire data processed
    output_left = np.zeros(len(wav_data))
    output_right = np.zeros(len(wav_data))

    output_index_start = 0
    output_index_end = new_frame_size

    #Previous loop windowed frame used for WOLA operation
    windowed_frame_left = np.zeros(fft_frame_size-new_frame_size)
    windowed_frame_right = np.zeros(fft_frame_size-new_frame_size)

    #Input buffer for WOLA operation
    input_frames_left = np.zeros(fft_frame_size)
    input_frames_right = np.zeros(fft_frame_size)

    #FFT input buffer
    fft_in_left = np.zeros(nfft)
    fft_in_right = np.zeros(nfft)

    #First half of the FFT frequency data
    fft_channels_left=np.zeros(int(nfft/2)+1)
    fft_channels_right=np.zeros(int(nfft/2)+1)


    #IFFT output with only real data format
    ifft_out_left = np.zeros(fft_frame_size)
    ifft_out_right = np.zeros(fft_frame_size)

    # The output time domain frame before post process applied
    out_frame_left = np.zeros(new_frame_size)
    out_frame_right = np.zeros(new_frame_size)

    # The data frames loop
    for index, frame in enumerate(frames_data_left):
        # tic = tm.perf_counter()

        # Loading the current unprocessed time domain frame
        new_frame_left = frame
        if stereo:
            new_frame_right = frames_data_right[index]

        # Checking if there is a preprocess function set
        # No preprocess function just copies the input
        if not pre_proc_func:
            pre_processed_frame_left = new_frame_left
            if stereo:
                pre_processed_frame_right = new_frame_right

        # Calling the preprocess function with the new frame input
        else:
            if stereo:
                # Adding the 2 streams in one list
                indata = np.empty((0,len(new_frame_left)))
                indata = np.append(indata, [new_frame_left], axis=0)
                indata = np.append(indata, [new_frame_right], axis=0)
                outdata=pre_proc_func(indata)

                pre_processed_frame_left=outdata[0]
                pre_processed_frame_right=outdata[1]
            else:
                pre_processed_frame_left=pre_proc_func(new_frame_left)

        #Checking if 50% overlap to set the FFT input buffer
        if overlap==50:
            if stereo:
                input_frames_left[:block_size] = input_frames_left[block_size:]
                input_frames_left[block_size:] = pre_processed_frame_left

                input_frames_right[:block_size] = input_frames_right[block_size:]
                input_frames_right[block_size:] = pre_processed_frame_right

            else:
                input_frames_left[:block_size] = input_frames_left[block_size:]
                input_frames_left[block_size:] = pre_processed_frame_left
        
        #Checking if 75% overlap to set the FFT input buffer
        elif overlap==75:
                if stereo:
                    input_frames_left[:block_size] = input_frames_left[block_size:2 * block_size]
                    input_frames_left[block_size:2 * block_size] = input_frames_left[2 * block_size:3 * block_size]
                    input_frames_left[2 * block_size:3 * block_size] = input_frames_left[3 * block_size:4 * block_size]
                    input_frames_left[3 * block_size:4 * block_size] = pre_processed_frame_left

                    input_frames_right[:block_size] = input_frames_right[block_size:2 * block_size]
                    input_frames_right[block_size:2 * block_size] = input_frames_right[2 * block_size:3 * block_size]
                    input_frames_right[2 * block_size:3 * block_size] = input_frames_right[3 * block_size:4 * block_size]
                    input_frames_right[3 * block_size:4 * block_size] = pre_processed_frame_right
                else:
                    input_frames_left[:block_size] = input_frames_left[block_size:2 * block_size]
                    input_frames_left[block_size:2 * block_size] = input_frames_left[2 * block_size:3 * block_size]
                    input_frames_left[2 * block_size:3 * block_size] = input_frames_left[3 * block_size:4 * block_size]
                    input_frames_left[3 * block_size:4 * block_size] = pre_processed_frame_left

        #Applying the window function (Hanning)
        if stereo:
            fft_in_left[:int(nfft / 2)] = input_frames_left * hanning
            fft_in_right[:int(nfft / 2)] = input_frames_right * hanning
        else:
            fft_in_left[:int(nfft/2)] = input_frames_left * hanning

        #Doing the FFT operation, In this case half of data is zero ;int(nfft/2)~
        fft_out_left=np.fft.fft(fft_in_left)
        if stereo:
            fft_out_right=np.fft.fft(fft_in_right)

        #Removing reflection
        fft_channels_left=fft_out_left[:(int(nfft/2)+1)]
        if stereo:
            fft_channels_right=fft_out_right[:(int(nfft/2)+1)]

        #Checking if there is a frequency domain process function
        # No frequency domain process function just copies the input
        if not freq_proc_func:
            freq_processed_frame_left=fft_channels_left
            if stereo:
                freq_processed_frame_right=fft_channels_right

        # Calling the frequency domain process function
        else:
            if stereo:
                # Adding the 2 streams in one list
                indata = np.empty((0, int(nfft / 2) + 1))
                indata = np.append(indata, [fft_channels_left], axis=0)
                indata = np.append(indata, [fft_channels_right], axis=0)

                outdata=freq_proc_func(indata)

                freq_processed_frame_left=outdata[0]
                freq_processed_frame_right=outdata[1]
            else:
                freq_processed_frame_left = freq_proc_func(fft_channels_left)

        #Mirror the spectrum
        if stereo:
            # Left
            fft_out_left[:int(nfft / 2)] = freq_processed_frame_left[:int(nfft / 2)]

            # Mirror copy except bias
            temp_mirror = freq_processed_frame_left[1:int(nfft / 2)]
            temp_mirror = temp_mirror[::-1]
            fft_out_left[int(nfft / 2) + 1:] = np.conj(temp_mirror)

            # Nyquist
            fft_out_left[int(nfft / 2)] = freq_processed_frame_left[int(nfft / 2)]

            # Right
            fft_out_right[:int(nfft / 2)] = freq_processed_frame_right[:int(nfft / 2)]

            # Mirror copy except bias
            temp_mirror = freq_processed_frame_right[1:int(nfft / 2)]
            temp_mirror = temp_mirror[::-1]
            fft_out_right[int(nfft / 2) + 1:] = np.conj(temp_mirror)

            # Nyquist
            fft_out_right[int(nfft / 2)] = freq_processed_frame_right[int(nfft / 2)]

        else:
            # Left
            fft_out_left[:int(nfft / 2)] = freq_processed_frame_left[:int(nfft / 2)]

            # Mirror copy except bias
            temp_mirror = freq_processed_frame_left[1:int(nfft / 2)]
            temp_mirror = temp_mirror[::-1]
            fft_out_left[int(nfft / 2) + 1:] = np.conj(temp_mirror)

            # Nyquist
            fft_out_left[int(nfft / 2)] = freq_processed_frame_left[int(nfft / 2)]


        #Doing the IFFT operation
        ifft_in_left=np.fft.ifft(fft_out_left)
        if stereo:
            ifft_in_right=np.fft.ifft(fft_out_right)

        #Separating the desired part of the IFFT output
        #For 50% overlap no second window needed
        if overlap==50:
            if stereo:
                ifft_out_left = ifft_in_left[:fft_frame_size].real
                out_frame_left = ifft_out_left[:new_frame_size] + windowed_frame_left[:new_frame_size]
                windowed_frame_left = ifft_out_left[new_frame_size:]

                ifft_out_right = ifft_in_right[:fft_frame_size].real
                out_frame_right = ifft_out_right[:new_frame_size] + windowed_frame_right[:new_frame_size]
                windowed_frame_right = ifft_out_right[new_frame_size:]
            else:
                ifft_out_left = ifft_in_left[:fft_frame_size].real
                out_frame_left = ifft_out_left[:new_frame_size] + windowed_frame_left[:new_frame_size]
                windowed_frame_left = ifft_out_left[new_frame_size:]

        #For 75% applying second window with gain adjustment to normalize output (-1< out <1)
        elif overlap==75:
            if stereo:
                ifft_out_left = np.float64(ifft_in_left[:fft_frame_size].real) * hanning * 2 / 3

                out_frame_left = ifft_out_left[:new_frame_size] + windowed_frame_left[:new_frame_size]
                windowed_frame_left[:new_frame_size] = windowed_frame_left[:new_frame_size] + ifft_out_left[:new_frame_size]
                windowed_frame_left[new_frame_size:2 * new_frame_size] = windowed_frame_left[new_frame_size:2 * new_frame_size] + ifft_out_left[new_frame_size:2 * new_frame_size]
                windowed_frame_left[2 * new_frame_size:] = ifft_out_left[3 * new_frame_size:]

                ifft_out_right = np.float64(ifft_in_right[:fft_frame_size].real) * hanning * 2 / 3

                out_frame_right = ifft_out_right[:new_frame_size] + windowed_frame_right[:new_frame_size]
                windowed_frame_right[:new_frame_size] = windowed_frame_right[:new_frame_size] + ifft_out_right[:new_frame_size]
                windowed_frame_right[new_frame_size:2 * new_frame_size] = windowed_frame_right[new_frame_size:2 * new_frame_size] + ifft_out_right[new_frame_size:2 * new_frame_size]
                windowed_frame_right[2 * new_frame_size:] = ifft_out_right[3 * new_frame_size:]

            else:
                ifft_out_left = np.float64(ifft_in_left[:fft_frame_size].real) * hanning * 2 / 3

                out_frame_left = ifft_out_left[:new_frame_size] + windowed_frame_left[:new_frame_size]
                windowed_frame_left[:new_frame_size] = windowed_frame_left[new_frame_size:2 * new_frame_size] + ifft_out_left[new_frame_size:2 * new_frame_size]
                windowed_frame_left[new_frame_size:2 * new_frame_size] = windowed_frame_left[2 * new_frame_size: 3 * new_frame_size] + ifft_out_left[2 * new_frame_size:3 * new_frame_size]
                windowed_frame_left[2 * new_frame_size:] = ifft_out_left[3 * new_frame_size:]
    
        #Checking if there is a post process function
        # No post process function just copies the input
        if not post_proc_func:
            post_processed_frame_left=out_frame_left
            if stereo:
                post_processed_frame_right=out_frame_right

        # Calling the post process function
        else: 
            # Adding the 2 streams in one list
            if stereo:
                indata = np.empty((0, new_frame_size))
                indata = np.append(indata, [out_frame_left], axis=0)
                indata = np.append(indata, [out_frame_right], axis=0)
                outdata = post_proc_func(indata)
                post_processed_frame_left = outdata[0]
                post_processed_frame_right = outdata[1]

            else:
                post_processed_frame_left = post_proc_func(out_frame_left)

        # Adding the current frame to the output buffer
        output_left[output_index_start:output_index_end] = post_processed_frame_left[:new_frame_size]

        if stereo:
            output_right[output_index_start:output_index_end] = post_processed_frame_right[:new_frame_size]

        output_index_start += new_frame_size
        output_index_end += new_frame_size
        #Updating the progress bar
        if progress_bar:
            _print_progress (len(frame), len(frames_data_left))

        # print(f"Period {tm.perf_counter()-tic}")



    print("\nProcess COMPLETE!")
    #Return the output buffers Left and Right if out_file_name=""
    if (out_file_name=="") or (out_file_name==None):
        if stereo:
            outdata = []
            outdata.append(output_left)
            outdata.append(output_right)
            return outdata
        else:
            return output_left

    #Else save the output wav file
    else:
        left = np.float32(output_left)
        data = left
        if stereo:
            right = np.float32(output_right)
            data = np.vstack((left, right)).T
        wav.write(out_file_name,wav_freq,data)


######################################### Real time Stream #############################################

#Class to hold static data for the callback
class _RealTimeStreamParams:
    #User input data
    stereo=True
    overlap=75
    block_size=128
    nfft=1024
    fft_frame_size=512
    hanning=[0]
    pre_proc_func=None
    freq_proc_func=None
    post_proc_func=None
    #Wola static data
    windowed_frame_left=[0]
    windowed_frame_right=[0]
    input_frames_left=[0]
    input_frames_right=[0]

#Creating the real time stream class instance
RTSteamInstance=_RealTimeStreamParams()

def real_time_stream(device=(1,3),
                     samplerate=16000,
                     stereo=False,
                     overlap=75,
                     block_size=128,
                     zero_pad=True,
                     pre_proc_func=None,
                     freq_proc_func=None,
                     post_proc_func=None): 
    #Printing function header
    print("\n#################  Real Time Stream  #################")
    #Errors check before do any process
    if(pre_proc_func==None and freq_proc_func==None and post_proc_func==None): 
        print("WARNING: No process function entered, no process will be applied to the stream")
        func_bool=input("Do you want to continue (Y/n) ? ")
        if(func_bool!="Y" and func_bool!="y"):
            return None 
    if(overlap!=50 and overlap!=75): 
        print("ERROR: Wrong overlap value (50 or 75 only)")
        return None
    if((block_size % 2)!=0): 
        print("ERROR: Blocksize value should be even number")
        return None
    if(samplerate not in [4000,8000,16000,22050,24000,44100,48000,96000]):
        print("ERROR: Samplerate not standard")
        return None        
    #Checking the NFFT value
    nfft=0
    if(zero_pad): 
        if(overlap==75):nfft=int(block_size*8)
        else: nfft=int(block_size*4)
    else: 
        if(overlap==75):nfft=int(block_size*4)
        else: nfft=int(block_size*2)    
    #Checking the FFT frame size
    fft_frame_size=0
    if(zero_pad): fft_frame_size=int(nfft/2)
    else: fft_frame_size=nfft
    #Hanning window
    hanning=[(0.5-(0.5*math.cos((2*math.pi*i)/(fft_frame_size-1)))) for i in range(fft_frame_size)]
    #Loading the global instance
    global RTSteamInstance
    #Updating the global instance with user inputs
    RTSteamInstance.stereo=stereo
    RTSteamInstance.overlap=overlap
    RTSteamInstance.block_size=block_size
    RTSteamInstance.nfft=nfft
    RTSteamInstance.fft_frame_size=fft_frame_size
    RTSteamInstance.hanning=hanning
    RTSteamInstance.pre_proc_func=pre_proc_func
    RTSteamInstance.freq_proc_func=freq_proc_func
    RTSteamInstance.post_proc_func=post_proc_func
    RTSteamInstance.windowed_frame_left=[0]*(fft_frame_size-block_size)
    RTSteamInstance.windowed_frame_right=[0]*(fft_frame_size-block_size)
    RTSteamInstance.input_frames_left=[0]*fft_frame_size
    RTSteamInstance.input_frames_right=[0]*fft_frame_size
    #Setting channels based on stereo user input
    channels=0
    if(stereo): channels=2
    else: channels=1
    #Calling the sounddevice stream function
    with sd.Stream(device=device,
                   samplerate=samplerate, blocksize= block_size,
                   dtype=None, latency="low",
                   channels=channels, callback=_callback):
        #Message print to user
        print('\nPress RETURN to exit...')
        input()

# Callback for sounddevice stream (fixed format)
def _callback(indata, outdata, frames, time, status):
    #Loading the global instance values
    global RTSteamInstance
    stereo=RTSteamInstance.stereo
    overlap=RTSteamInstance.overlap
    block_size=RTSteamInstance.block_size
    nfft=RTSteamInstance.nfft
    fft_frame_size=RTSteamInstance.fft_frame_size
    hanning=RTSteamInstance.hanning
    pre_proc_func=RTSteamInstance.pre_proc_func
    freq_proc_func=RTSteamInstance.freq_proc_func
    post_proc_func=RTSteamInstance.post_proc_func
    windowed_frame_left=RTSteamInstance.windowed_frame_left
    windowed_frame_right=RTSteamInstance.windowed_frame_right
    input_frames_left=RTSteamInstance.input_frames_left
    input_frames_right=RTSteamInstance.input_frames_right

    # Wola variables
    output_left=[]
    output_right=[]
    #FFT input buffer
    fft_in_left=[0]*nfft
    fft_in_right=[0]*nfft
    #First half of the FFT frequency data
    fft_channels_left=[0]*(int(nfft/2)+1)
    fft_channels_right=[0]*(int(nfft/2)+1)
    #IFFT output with only real data format
    ifft_out_left=[0]*fft_frame_size
    ifft_out_right=[0]*fft_frame_size
    #The output time domain frame before post process applied
    out_frame_left=[0]*block_size
    out_frame_right=[0]*block_size    
    # Converting input data in standard format
    new_frame_left=[indata[i][0] for i in range(indata.shape[0])]
    if(stereo): new_frame_right=[indata[i][1] for i in range(indata.shape[0])]

    #Checking if there is a preprocess function set
    # No preprocess function just copies the input
    if not(pre_proc_func): 
        pre_processed_frame_left=new_frame_left
        if(stereo): pre_processed_frame_right=new_frame_right

    # Calling the preprocess function with the new frame input
    else: 
        if(stereo): 
            # Adding the 2 streams in one list
            indata=[]
            indata.append(new_frame_left)
            indata.append(new_frame_right)
            outdata=pre_proc_func(indata)
            pre_processed_frame_left=outdata[0]
            pre_processed_frame_right=outdata[1]
        else: pre_processed_frame_left=pre_proc_func(new_frame_left)

    #Checking if 50% overlap to set the FFT input buffer
    if(overlap==50):
        if(stereo):
            input_frames_left[:block_size]=input_frames_left[block_size:]
            input_frames_left[block_size:]=pre_processed_frame_left

            input_frames_right[:block_size]=input_frames_right[block_size:]
            input_frames_right[block_size:]=pre_processed_frame_right
        else:
            input_frames_left[:block_size]=input_frames_left[block_size:]
            input_frames_left[block_size:]=pre_processed_frame_left
    
    #Checking if 75% overlap to set the FFT input buffer
    elif(overlap==75):
        if(stereo):
            input_frames_left[:block_size]=input_frames_left[block_size:2*block_size]
            input_frames_left[block_size:2*block_size]=input_frames_left[2*block_size:3*block_size]
            input_frames_left[2*block_size:3*block_size]=input_frames_left[3*block_size:4*block_size]
            input_frames_left[3*block_size:4*block_size]=pre_processed_frame_left

            input_frames_right[:block_size]=input_frames_right[block_size:2*block_size]
            input_frames_right[block_size:2*block_size]=input_frames_right[2*block_size:3*block_size]
            input_frames_right[2*block_size:3*block_size]=input_frames_right[3*block_size:4*block_size]
            input_frames_right[3*block_size:4*block_size]=pre_processed_frame_right

        else:
            input_frames_left[:block_size]=input_frames_left[block_size:2*block_size]
            input_frames_left[block_size:2*block_size]=input_frames_left[2*block_size:3*block_size]
            input_frames_left[2*block_size:3*block_size]=input_frames_left[3*block_size:4*block_size]
            input_frames_left[3*block_size:4*block_size]=pre_processed_frame_left

    #Applying the window function (Hanning)
    if(stereo):
        for i in range(fft_frame_size):
            fft_in_left[i]=input_frames_left[i]*hanning[i]
            fft_in_right[i]=input_frames_right[i]*hanning[i]
    else:
        for i in range(fft_frame_size):
            fft_in_left[i]=input_frames_left[i]*hanning[i]

    #Doing the FFT operation
    fft_out_left=np.fft.fft(fft_in_left)
    if(stereo): fft_out_right=np.fft.fft(fft_in_right)

    #Revoming reflaction
    fft_channels_left=fft_out_left[:(int(nfft/2)+1)]
    if(stereo): fft_channels_right=fft_out_right[:(int(nfft/2)+1)]

    #Checking if there is a frequency domain process function
    # No frequency domain process function just copies the input
    if not(freq_proc_func): 
        freq_processed_frame_left=fft_channels_left
        if(stereo): freq_processed_frame_right=fft_channels_right
    # Calling the frequency domain process function
    else: 
        if(stereo): 
            # Adding the 2 streams in one list
            indata=[]
            indata.append(fft_channels_left)
            indata.append(fft_channels_right)
            outdata=freq_proc_func(indata)
            freq_processed_frame_left=outdata[0]
            freq_processed_frame_right=outdata[1]
        else: freq_processed_frame_left=freq_proc_func(fft_channels_left)

    #Mirror the spectrum
    if(stereo):
        for i in range(int(nfft/2)):
            fft_out_left[i]=freq_processed_frame_left[i]
            fft_out_left[nfft-1-i]=np.conj(freq_processed_frame_left[i+1])
            fft_out_right[i]=freq_processed_frame_right[i]
            fft_out_right[nfft-1-i]=np.conj(freq_processed_frame_right[i+1])
        fft_out_left[int(nfft/2)]=freq_processed_frame_left[int(nfft/2)]
        fft_out_right[int(nfft/2)]=freq_processed_frame_right[int(nfft/2)]
    else:
        for i in range(int(nfft/2)):
            fft_out_left[i]=freq_processed_frame_left[i]
            fft_out_left[nfft-1-i]=np.conj(freq_processed_frame_left[i+1])
        fft_out_left[int(nfft/2)]=freq_processed_frame_left[int(nfft/2)]

    #Doing the IFFT operation
    ifft_in_left=np.fft.ifft(fft_out_left)
    if(stereo): ifft_in_right=np.fft.ifft(fft_out_right)

    #Separating the desired part of the IFFT output
    #For 50% overlap no second window needed
    if(overlap==50):
        if(stereo):
            ifft_out_left=[ifft_in_left[i].real for i in range(fft_frame_size)]
            ifft_out_right=[ifft_in_right[i].real for i in range(fft_frame_size)]
            out_frame_left=[ifft_out_left[i]+windowed_frame_left[i] for i in range(block_size)]
            windowed_frame_left=ifft_out_left[block_size:]
            out_frame_right=[ifft_out_right[i]+windowed_frame_right[i] for i in range(block_size)]
            windowed_frame_right=ifft_out_right[block_size:]

        else:
            ifft_out_left=[ifft_in_left[i].real for i in range(fft_frame_size)]
            out_frame_left=[ifft_out_left[i]+windowed_frame_left[i] for i in range(block_size)]
            windowed_frame_left=ifft_out_left[block_size:]

    #For 75% applying second window with gain adjustment to normalize output (-1< out <1)
    elif(overlap==75):
        if(stereo):
            ifft_out_left=[float(ifft_in_left[i].real)*hanning[i]*(2/3) for i in range(fft_frame_size)]
            ifft_out_right=[float(ifft_in_right[i].real)*hanning[i]*(2/3) for i in range(fft_frame_size)]
            out_frame_left=[ifft_out_left[i]+windowed_frame_left[i] for i in range(block_size)]
            windowed_frame_left[:block_size]=[windowed_frame_left[i+block_size]+ifft_out_left[i+block_size] for i in range(block_size)]
            windowed_frame_left[block_size:2*block_size]=[windowed_frame_left[i+2*block_size]+ifft_out_left[i+2*block_size] for i in range(block_size)]
            windowed_frame_left[2*block_size:]=ifft_out_left[3*block_size:]
            
            out_frame_right=[ifft_out_right[i]+windowed_frame_right[i] for i in range(block_size)]
            windowed_frame_right[:block_size]=[windowed_frame_right[i+block_size]+ifft_out_right[i+block_size] for i in range(block_size)]
            windowed_frame_right[block_size:2*block_size]=[windowed_frame_right[i+2*block_size]+ifft_out_right[i+2*block_size] for i in range(block_size)]
            windowed_frame_right[2*block_size:]=ifft_out_right[3*block_size:]
        else:
            ifft_out_left=[float(ifft_in_left[i].real)*hanning[i]*(2/3) for i in range(fft_frame_size)]
            out_frame_left=[ifft_out_left[i]+windowed_frame_left[i] for i in range(block_size)]
            windowed_frame_left[:block_size]=[windowed_frame_left[i+block_size]+ifft_out_left[i+block_size] for i in range(block_size)]
            windowed_frame_left[block_size:2*block_size]=[windowed_frame_left[i+2*block_size]+ifft_out_left[i+2*block_size] for i in range(block_size)]
            windowed_frame_left[2*block_size:]=ifft_out_left[3*block_size:] 

    #Checking if there is a post process function
    # No post process function just copies the input
    if not(post_proc_func): 
        post_processed_frame_left=out_frame_left
        if(stereo): post_processed_frame_right=out_frame_right
    # Calling the post process function
    else: 
        # Adding the 2 streams in one list
        if(stereo):
            indata=[]
            indata.append(out_frame_left)
            indata.append(out_frame_right)
            outdata=post_proc_func(indata)
            post_processed_frame_left=outdata[0]
            post_processed_frame_right=outdata[1]
        else: post_processed_frame_left=post_proc_func(out_frame_left)

    # Getting the output buffer
    output_left[:]=post_processed_frame_left
    if(stereo): output_right[:]=post_processed_frame_right

    # Saving back to the instance the updated buffers
    RTSteamInstance.windowed_frame_left=windowed_frame_left
    RTSteamInstance.windowed_frame_right=windowed_frame_right
    RTSteamInstance.input_frames_left=input_frames_left
    RTSteamInstance.input_frames_right=input_frames_right

    # Formating the output with sounddevice standard
    outdata[:]=np.vstack((output_left))
    if(stereo): outdata[:]=np.vstack((output_left,output_right)).T

