#!/usr/bin/env python3

import numpy as np
from scipy.io import wavfile

sampleRate = 44100
frequency = 440
length = 1

#  Produces a 5 second Audio-File
t = np.linspace(0, length, sampleRate * length)
#  Has frequency of 440Hz, float64
y = np.sin(frequency * 2 * np.pi * t)
# Change to float32
y = np.float32(y)
wavfile.write('Sine.wav', sampleRate, y)
