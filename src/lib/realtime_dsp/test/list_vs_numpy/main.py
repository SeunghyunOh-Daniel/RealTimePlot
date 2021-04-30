def main():
    print("Compare list vs numpy")
    from real_time_dsp import wave_file_process
    data = "./sine_440hz_float64.wav"

    # list
    wave_file_process(in_file_name=data,
                      get_file_details=False,
                      out_file_name="",
                      progress_bar=False,
                      stereo=False,
                      overlap=50,
                      block_size=512,
                      zero_pad=True,
                      pre_proc_func=None,
                      freq_proc_func=None,
                      post_proc_func=None,
                      mode=0)

    # numpy
    wave_file_process(in_file_name=data,
                      get_file_details=False,
                      out_file_name="",
                      progress_bar=False,
                      stereo=False,
                      overlap=50,
                      block_size=512,
                      zero_pad=True,
                      pre_proc_func=None,
                      freq_proc_func=None,
                      post_proc_func=None,
                      mode=1)
if __name__ == "__main__":
    main()