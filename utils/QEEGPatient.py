import mne
import pandas as pd
import sys
import matplotlib.pyplot as plt
import numpy as np
# from scipy.fft import fft
from scipy.signal import welch, coherence, csd
# from mne.time_frequency import psd_welch

class QEEGPatient:
    def __init__(self, subject_id, full_raw, ch_list, SAMPLING_FREQUENCY=256):
        self.subject_id = subject_id  # Unique identifier for the patient
        self.full_raw = full_raw      # Patient Raw EEG signal
        self.ch_list = ch_list        # Channels name list
        self.raw_length = full_raw.shape[1]
        self.SAMPLING_FREQUENCY = SAMPLING_FREQUENCY # 256/1 second
        # self.total_window = self.SAMPLING_FREQUENCY
        # self.window_width = 1 # second*samplingfrequency
        # self.window_overlap = 1/2 # 50% 
        self.segments = {}            # Segment Dictionary
        self.rounddigit = 2   # Patient digit precision

        self.band_freqs = {
            "delta": (0.5, 3),
            "theta": (3, 8),
            "alpha": (8, 13),
            "beta":  (13, 30),
            "gamma": (30, 45)
        }

    def add_segment(self, segment_name, segment_data, is_extend, interval):

        seg_suffix="_Extend" if (is_extend) else "_Intend"
        seg_name = segment_name+seg_suffix
        self.segments[seg_name] = {
            # 'segment_name':segment_name,
            'segment_data': {ch: np.round(segment_data[ch_id]*1e6,self.rounddigit) for ch_id, ch in enumerate(self.ch_list)},
            'is_extend': is_extend,
            # 'win_num' : win_num,
            'absolute_power': {ch: {} for ch in self.ch_list},   # each channel, has 5 bands
            'relative_power': {ch: {} for ch in self.ch_list},   # self.segments["Baseline_Extend"].get("absolute_power")
            'amplitude_asymmetry': {ch: {} for ch in self.ch_list},
            'phase_lag': {ch: {} for ch in self.ch_list},
            'coherence': {ch: {} for ch in self.ch_list},
            'band_ratios': {ch: {} for ch in self.ch_list},
            'hideCh':   True,    # hide channel sub row
            'f': {ch:{} for ch in self.ch_list},
            'Pxx': {ch:{} for ch in self.ch_list},
            'interval_list': interval,
            'interval_count': len(interval),
        }
        print("Segment: ", seg_name)

        for ch in self.ch_list:
            ######## Single Channel ####################
            self.compute_absolute_power(seg_name, ch)  
            self.compute_relative_power(seg_name, ch)   

        self.plot_powerSpectralDensity(seg_name)

        for ch in self.ch_list:
            for ch2 in self.ch_list:
                self.compute_coherence(seg_name, ch, ch2) 
                for band1 in self.band_freqs:
                    self.compute_amplitude_asymmetry(seg_name, ch, ch2, band1)   
                    self.compute_phase_lag(seg_name, ch, ch2, band1)     
                    for band2 in self.band_freqs: # loop through every channel band SPECIFICALLY for BAND RATIO?
                        self.compute_band_ratio(seg_name, ch, band1, band2)
             # loop through every channel band
                ######## Pairwise ###################################################

                

    def plot_powerSpectralDensity(self, segment_name):
        
        plt.figure()
        for ch in self.ch_list:
            f = self.segments[segment_name]["f"][ch]
            Pxx = self.segments[segment_name]["Pxx"][ch]
            plt.plot(f, Pxx)

        plt.title(f'Power Spectral Density {segment_name} All Channel ') # {self.segments[segment_name]["interval_list"]}
        # plt.title(f'Power Spectral Density {segment_name} CH: {channel}')

        plt.xlabel('Sample frequency')
        plt.ylabel('Power Spectrum')
        plt.show()

            
    def compute_absolute_power(self, segment_name, channel):
        # print( 1*self.segments.get('segment_data') )
        # self.segments[segment_name]['absolute_power'][channel][band] = 1*self.segments.get('segment_data')[channel]          
        data = self.segments[segment_name]['segment_data'][channel]
        # print("data", data)
        # Separate 5 band, 
        psd_segment_width=2*self.SAMPLING_FREQUENCY
        f, Pxx = welch(data, fs=self.SAMPLING_FREQUENCY, nperseg = psd_segment_width)       
        self.segments[segment_name]["f"][channel] = f
        self.segments[segment_name]["Pxx"][channel]  = Pxx
        # print("Segname ",segment_name,' freq ',f,' PSD ',Pxx)
        
        for band in self.band_freqs:
            band_range = self.band_freqs[band]
            band_mask = (f >= band_range[0]) & (f <= band_range[1])
            band_power = np.trapz(  Pxx[band_mask], f[band_mask] ) # integrate psd over freq
            band_power = np.round(band_power,self.rounddigit)
            self.segments[segment_name]['absolute_power'][channel][band] = band_power    

    def compute_relative_power(self, segment_name, channel):
        # sum of all band power
        total_power = sum(self.segments[segment_name]['absolute_power'][channel].values())

        if total_power == 0:  # avoid division by zero
            return 0  
        
        for band in self.band_freqs:
            # power of the specified band
            band_power = self.segments[segment_name]['absolute_power'][channel][band]
            self.segments[segment_name]['relative_power'][channel][band] = np.round(band_power / total_power, self.rounddigit) 
        # current band power / sum of all band power

  
    def compute_band_ratio(self, segment_name, channel, band1, band2):
        # Ensure that absolute power for both bands exists
        if band1 not in self.band_freqs or band2 not in self.band_freqs:
            raise ValueError(f"Band {band1} or {band2} not found in band frequencies.")

        # Get the power for both bands from the 'absolute_power' dictionary
        power_band1 = self.segments[segment_name]['absolute_power'][channel].get(band1, 0)
        power_band2 = self.segments[segment_name]['absolute_power'][channel].get(band2, 1)  # Avoid division by zero by setting default to 1

        # Calculate the ratio
        if power_band2 == 0:
            return float('inf')  # To avoid division by zero, return infinity if power_band2 is zero
        band_ratio = power_band1 / power_band2
        
        # Store the result in the 'band_ratios' dictionary
        self.segments[segment_name]['band_ratios'][channel][f'{band1}/{band2}'] = np.round(band_ratio, self.rounddigit)

#------------PAIRWISE-------------------------------------------------------------------------  

    def compute_amplitude_asymmetry(self, segment_name, ch1, ch2, band):
        power_ch1 = self.segments[segment_name]['absolute_power'][ch1][band]
        power_ch2 = self.segments[segment_name]['absolute_power'][ch2][band]
        self.segments[segment_name]['amplitude_asymmetry'][ch1][f'{ch1}-{ch2}_{band}'] =  np.round( (power_ch1 - power_ch2) / (power_ch1 + power_ch2), self.rounddigit )
    

    def compute_phase_lag(self, segment_name, channel1, channel2, band):
        data_ch1 = self.segments[segment_name]['segment_data'][channel1]
        data_ch2 = self.segments[segment_name]['segment_data'][channel2]
        
        # Compute the cross power spectral density using Welch's method
        f, Pxy = csd(data_ch1, data_ch2, fs=self.SAMPLING_FREQUENCY, nperseg=2*self.SAMPLING_FREQUENCY)

        # Find the index corresponding to the frequency band of interest
        band_range = self.band_freqs[band]
        band_mask = (f >= band_range[0]) & (f <= band_range[1])

        # Extract phase angles for the selected band
        phase_lag = np.angle(Pxy[band_mask])

        # Calculate the mean phase lag over the frequency range in the band
        mean_phase_lag = np.mean(phase_lag)
        
        # Store the result in the 'phase_lag' dictionary
        self.segments[segment_name]['phase_lag'][(channel1, channel2)] = np.round(mean_phase_lag, self.rounddigit)

        # return mean_phase_lag

    def compute_coherence(self, segment_name, ch1, ch2):

        for band in self.band_freqs:

            data1 = self.segments[segment_name]['segment_data'][ch1]
            data2 = self.segments[segment_name]['segment_data'][ch2]

            # f, Cxy = coherence(data1, data2, fs=self.SAMPLING_FREQUENCY)
            
            # self.segments[segment_name]['coherence'][f'{ch1}_{ch2}'][band] = Cxy
  

            #   # Compute the cross-spectral density (CSD) between the two signals
            f, Pxy = csd(data1, data2, fs=self.SAMPLING_FREQUENCY, nperseg=2*self.SAMPLING_FREQUENCY)
            
            # Compute the power spectral densities (PSD) for each channel
            _, Pxx = welch(data1, fs=self.SAMPLING_FREQUENCY, nperseg=2*self.SAMPLING_FREQUENCY)
            _, Pyy = welch(data2, fs=self.SAMPLING_FREQUENCY, nperseg=2*self.SAMPLING_FREQUENCY)
            
            # # Compute the coherence
            coherence = np.abs(Pxy) ** 2 / (Pxx * Pyy)
            self.segments[segment_name]['coherence'][f'{ch1}_{ch2}'] = coherence