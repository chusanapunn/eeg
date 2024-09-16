import mne
import pandas as pd
import sys
import matplotlib.pyplot as plt
import datetime
import win32com.client
import numpy as np
import math
from scipy.fft import fft
import re

class QEEGPatient:
    def __init__(self, subject_id, eeg_signal):
        self.subject_id = subject_id  # Unique identifier for the patient
        self.eeg_signal = eeg_signal  # Patient Raw EEG signal
        
        # 19 EEG channels
        self.channels = ["Fp1", "Fp2", "F3", "F4", "C3", "C4", 
                         "P3", "P4", "O1", "O2", "F7", "F8", 
                         "T3", "T4", "T5", "T6", "Fz", "Cz", "Pz"]
        
        # (baseline1, simulation, q1-q4,baseline2(post-intervention))
        self.segments = {}  

    # def add_segment(self, segment_name, segment_data):
    #     self.segments[segment_name] = {
    #         'segment_data': segment_data,                         # raw for that segment
    #         'absolute_power': {ch: {} for ch in self.channels},   # others attribute
    #         'relative_power': {ch: {} for ch in self.channels},
    #         'amplitude_asymmetry': {},
    #         'phase_lag': {},
    #         'coherence': {},
    #         'band_ratios': {ch: {} for ch in self.channels}
    #     }

    # def compute_absolute_power(self, segment_name, channel, band):

    #     self.segments[segment_name]['absolute_power'][channel][band] = #

    # def compute_relative_power(self, segment_name, channel, band, value):
    #     self.segments[segment_name]['relative_power'][channel][band] = value

    # def compute_amplitude_asymmetry(self, segment_name, channel1, channel2, band, value):
    #     self.segments[segment_name]['amplitude_asymmetry'][(channel1, channel2)] = {band: value}

    # def compute_phase_lag(self, segment_name, channel1, channel2, band, value):
    #     self.segments[segment_name]['phase_lag'][(channel1, channel2)] = {band: value}

    # def compute_coherence(self, segment_name, channel1, channel2, band, value):
    #     self.segments[segment_name]['coherence'][(channel1, channel2)] = {band: value}

    # def compute_band_ratio(self, segment_name, channel, ratio_name, value):
    #     self.segments[segment_name]['band_ratios'][channel][ratio_name] = value

    def get_absolute_power(self, segment_name, channel, band):
        return self.segments[segment_name]['absolute_power'][channel].get(band)

    # def get_coherence(self, segment_name, channel1, channel2, band):
    #     return self.segments[segment_name]['coherence'][(channel1, channel2)].get(band)


raw = mne.io.read_raw_edf("data/Subject15_11_4_2022/Subject15_11_4_2022 01.001.01  EO.edf")
# # raw.plot(block=True)

# SAMPLING_FREQUENCY   = raw.info['sfreq']
CROP_LENGTH = 10 # seconds
data, times = raw[:, 0:(CROP_LENGTH * raw.info['sfreq'])]
data2, times2 = raw[:, 200+0:200+(CROP_LENGTH * raw.info['sfreq'])]

patient = QEEGPatient(subject_id="15", eeg_signal=data)
patient.add_segment("Baseline", segment_data=data)
patient.add_segment("Simulation", segment_data=data2)

# print(patient.compute_absolute_power('Baseline'))

# patient.compute_absolute_power(segment_name="baseline", channel="Fp1", band="delta", value=2.4)
# patient.compute_coherence(segment_name="baseline", channel1="Fp1", channel2="Fp2", band="delta", value=0.45)
# delta_power_fp1 = patient.get_absolute_power(segment_name="baseline", channel="Fp1", band="delta")
# coherence_fp1_fp2_delta = patient.get_coherence(segment_name="baseline", channel1="Fp1", channel2="Fp2", band="delta")

print()

# print(f"Delta Power Fp1: {delta_power_fp1}")
# print(f"Coherence Fp1-Fp2 (Delta): {coherence_fp1_fp2_delta}")