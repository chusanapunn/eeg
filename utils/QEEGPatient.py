import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
# from scipy.fft import fft
from scipy.signal import welch, csd

# OBJECT DATA and METRIC CALCULATION ######################################
class QEEGPatient:
    def __init__(self, subject_id, full_raw, ch_list, SAMPLING_FREQUENCY=256):
# INIT patient info###########################################################
        self.subject_id = subject_id  # Unique identifier for the patient
        self.full_raw = full_raw      # Patient Raw EEG signal
        self.ch_list = ch_list        # chs name list
        self.raw_length = full_raw.shape[1]
        self.SAMPLING_FREQUENCY = SAMPLING_FREQUENCY # 256/1 second
        self.segments = {}            # Segment Dictionary
##############################################################################
        # self.total_window = self.SAMPLING_FREQUENCY
        # self.window_width = 1 # second*samplingfrequency

        self.rounddigit = 2   # Patient info digit precision
        self.band_freqs = {
            "D": (0.5, 3),   # Delta
            "T": (3, 8),     # Theta
            "A": (8, 13),    # Alpha
            "B":  (13, 30),  # Beta
            "G": (30, 45)    # Gamma
        }

    def add_segment(self, segment_name, segment_data, is_extend, interval_datapoint, OVERLAPPING):
        interval_count = len(interval_datapoint)
        interval_length =[]
        interval_second = interval_datapoint / self.SAMPLING_FREQUENCY
        for i in range(interval_count):
            interval_length_sec = interval_second[i][1]-interval_second[i][0]
            interval_length.append(interval_length_sec) # int length in seconds

        OVERLAPPING = np.round(OVERLAPPING, self.rounddigit)
        self.nOVERLAPPING = OVERLAPPING * self.SAMPLING_FREQUENCY

        seg_suffix="_Extend " if (is_extend) else "_Intend "
        seg_name = segment_name+seg_suffix+str(OVERLAPPING)+' %'
        
        self.segments[seg_name] = {
            # 'segment_name':segment_name,
            'segment_data': {ch: np.round(segment_data[ch_id]*1e6,self.rounddigit) for ch_id, ch in enumerate(self.ch_list)},
            'is_extend': is_extend,
            # 'win_num' : win_num,
            'absolute_power': {ch: {} for ch in self.ch_list},   # each ch, has 5 bands
            'relative_power': {ch: {} for ch in self.ch_list},   # self.segments["Baseline_Extend"].get("absolute_power")
            'amplitude_asymmetry': {ch: {} for ch in self.ch_list},
            'phase_lag': {ch: {} for ch in self.ch_list},
            'coherence': {ch: {} for ch in self.ch_list},
            'band_ratios': {ch: {} for ch in self.ch_list},
            'hideCh': True,    # hide ch sub row
            'interval_list': interval_datapoint,
            'interval_count': interval_count,
            'interval_length': interval_length,
            
            # for PSD visualization
            'fw':{ch:{} for ch in self.ch_list},  
            'Pxx': {ch:{} for ch in self.ch_list},

            # Single CH Power
            'Pxxband': {ch:{} for ch in self.ch_list},
            # Pairwise CH Power
            'Pxyband': {ch:{} for ch in self.ch_list},
        }
        print("Segment: ", seg_name)

        ######## Single ch #####################################################
        self.compute_absolute_power(seg_name)       # Prerequisite
        self.plot_powerSpectralDensity(seg_name)    # Prerequisite
        for ch1 in self.ch_list:  # loop through very channel
            self.compute_relative_power(seg_name, ch1)   # require (absolute power)-> cal (relative power)
            self.compute_band_ratio(seg_name, ch1)       # require (absolute power)-> cal (band ratio)
        ######## Pairwise ch ###################################################
            for ch2 in self.ch_list:  
                if (not ch1==ch2):
                    self.compute_amplitude_asymmetry(seg_name, ch1, ch2) # require(absolute power)-> cal (amp asym)
                    self.compute_phase_lag(seg_name, ch1, ch2)     # require(fc,Pxy) -> cal(phase lag, fc, Pxy)
                    self.compute_coherence(seg_name, ch1, ch2)     # require (Pxx, Pxy) - > cal(coherence)

    def plot_powerSpectralDensity(self, segment_name):
        
        plt.figure(figsize=(8,4))

        for ch in self.ch_list:
            f = self.segments[segment_name]["fw"][ch]
            Pxx = self.segments[segment_name]["Pxx"][ch]
            plt.plot(f, Pxx)

        plt.title(f'Power Spectral Density {segment_name} All CH, Overlapping {self.nOVERLAPPING} datapoint') # {self.segments[segment_name]["interval_list"]}
        plt.xlabel('Sample frequency')
        plt.ylabel('Power Spectrum')
        plt.show()

    # require (fw,Pxx) calculate (absolute power, f, Pxx)
    def compute_absolute_power(self, segment_name):
        # self.segments[segment_name]['absolute_power'][ch][band] = 1*self.segments.get('segment_data')[ch]  
        for ch in self.ch_list:         
            data = self.segments[segment_name]['segment_data'][ch]

            psd_segment_width=2*self.SAMPLING_FREQUENCY
            fw, Pxx = welch(data, fs=self.SAMPLING_FREQUENCY, nperseg = psd_segment_width, noverlap=self.nOVERLAPPING)       

            # print("Segname ",segment_name,' freq ',f,' PSD ',Pxx)
            self.segments[segment_name]["fw"][ch] = fw
            self.segments[segment_name]["Pxx"][ch]  = Pxx

            for band in self.band_freqs:
                band_range = self.band_freqs[band]
                band_mask = (fw >= band_range[0]) & (fw <= band_range[1])
                band_power = np.trapz(  Pxx[band_mask], fw[band_mask] ) # integrate psd over freq
                band_power = np.round(band_power,self.rounddigit)
                band_start_idx = np.searchsorted(fw, band_range[0], side="left")
                band_end_idx = np.searchsorted(fw, band_range[1], side="right")

                Pxx_band = Pxx[band_start_idx:band_end_idx]
                self.segments[segment_name]['absolute_power'][ch][band] = band_power    
                self.segments[segment_name]["Pxxband"][ch][band]  = Pxx_band

    # require (absolute power)-> cal (relative power)
    def compute_relative_power(self, segment_name, ch):
        # sum of all band power
        total_power = sum(self.segments[segment_name]['absolute_power'][ch].values())

        if total_power == 0:  # avoid division by zero
            return 0  
        
        for band in self.band_freqs: # power of the specified band
            band_power = self.segments[segment_name]['absolute_power'][ch][band]
            relative_power = band_power / total_power
            self.segments[segment_name]['relative_power'][ch][band] = np.round(relative_power, self.rounddigit) 
        # current band power / sum of all band power

  # require (absolute power)-> cal (band ratio)
    def compute_band_ratio(self, segment_name, ch):
        for band1 in self.band_freqs:
            for band2 in self.band_freqs:
                if (not band1 == band2) :
                    power_band1 = self.segments[segment_name]['absolute_power'][ch].get(band1, 0)
                    power_band2 = self.segments[segment_name]['absolute_power'][ch].get(band2, 1)  # Avoid division by zero by setting default to 1

                    if power_band2 == 0:
                        return float('inf')  # To avoid division by zero, return infinity if power_band2 is zero
                    band_ratio = power_band1 / power_band2

                    self.segments[segment_name]['band_ratios'][ch][f'{band1}/{band2}'] = np.round(band_ratio, self.rounddigit)

#------------PAIRWISE-------------------------------------------------------------------------  
    # ch to ch in a specific band, 
                
    # require(absolute power)-> cal (amp asym)
    def compute_amplitude_asymmetry(self, segment_name, ch1, ch2): 
        for band in self.band_freqs:
            power_ch1 = self.segments[segment_name]['absolute_power'][ch1].get(band, 0)
            power_ch2 = self.segments[segment_name]['absolute_power'][ch2].get(band, 1)
            amp_asym = np.round( (power_ch1 - power_ch2) / (power_ch1 + power_ch2), self.rounddigit )
            self.segments[segment_name]['amplitude_asymmetry'][ch1][f'{ch1}_{ch2}_{band}'] =  amp_asym
    
    # require(fc,Pxy) -> cal(phase lag, fc, Pxy)
    def compute_phase_lag(self, segment_name, ch1, ch2):
        data_ch1 = self.segments[segment_name]['segment_data'][ch1]
        data_ch2 = self.segments[segment_name]['segment_data'][ch2]
        
        # Compute the cross power spectral density using Welch's method
        fc, Pxy = csd(data_ch1, data_ch2, fs=self.SAMPLING_FREQUENCY, nperseg=2*self.SAMPLING_FREQUENCY)

        for band in self.band_freqs:
            band_range = self.band_freqs[band]
            band_mask = (fc >= band_range[0]) & (fc <= band_range[1])
            Pxy_band = Pxy[band_mask]
            self.segments[segment_name]["Pxyband"][ch1][f'to {ch2}_{band}']  = Pxy_band

            phase_lag = np.angle(Pxy[band_mask]) # phaselag - angle value of csd
            mean_phase_lag = np.mean(phase_lag)

            self.segments[segment_name]['phase_lag'][ch1][f'to {ch2}_{band}'] = np.round(mean_phase_lag, self.rounddigit)
   
    # require (Pxx, Pxy) - > cal(coherence)
    def compute_coherence(self, segment_name, ch1, ch2):

        for band in self.band_freqs:

            Pxy = self.segments[segment_name]["Pxyband"][ch1][f'to {ch2}_{band}'] 
            Pxx = self.segments[segment_name]["Pxxband"][ch1][band]
            Pyy = self.segments[segment_name]["Pxxband"][ch2][band]
            
            coherence = np.abs(Pxy) ** 2 / (Pxx * Pyy)
            coherence_value = np.mean(coherence)

            if ch1 not in self.segments[segment_name]['coherence']:
                self.segments[segment_name]['coherence'][ch1] = {}
            self.segments[segment_name]['coherence'][ch1][f'to {ch2}_{band}'] = coherence_value