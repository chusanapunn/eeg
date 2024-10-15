import mne
import pandas as pd
import os
from PyQt5.QtWidgets import QApplication, QFileDialog
import sys
import pyedflib

def preocess_edf_data(edf_file_path, output_path):
    # Load the EDF file using MNE
    raw = mne.io.read_raw_edf(edf_file_path, preload=True)
    # preocess the data along the time axis
    proc_raw = raw.notch_filter(freqs=50)
    Processed_edf_path = os.path.join(output_path, 'proc' + os.path.basename(edf_file_path))

    signal_headers = pyedflib.highlevel.make_signal_headers(raw.ch_names[:len(proc_raw)], sample_frequency=raw.info['sfreq'])
    
    pyedflib.highlevel.write_edf(Processed_edf_path, proc_raw, signal_headers)
    
    print(f"Processed EDF saved at: {Processed_edf_path}")

def preocess_trigger_data(trigger_file_path, output_path):
    # Load the trigger data
    trigger_df = pd.read_excel(trigger_file_path, engine='openpyxl')
    
    # preocess the trigger data
    Processed_trigger_df = trigger_df.iloc[::-1].reset_index(drop=True)
    
    # Save the Processed trigger file
    Processed_trigger_path = os.path.join(output_path, 'Processed_' + os.path.basename(trigger_file_path))
    Processed_trigger_df.to_excel(Processed_trigger_path, index=False)
    print(f"Processed trigger file saved at: {Processed_trigger_path}")

def main():
    app = QApplication(sys.argv)
    
    # Select EDF file
    edf_file_path, _ = QFileDialog.getOpenFileName(None, "Select EDF File", "", "EDF Files (*.edf)")
    if not edf_file_path:
        print("No EDF file selected.")
        return

    # Select trigger file
    trigger_file_path, _ = QFileDialog.getOpenFileName(None, "Select Trigger File", "", "Excel Files (*.xlsx)")
    if not trigger_file_path:
        print("No trigger file selected.")
        return

    # Select output folder
    output_path = QFileDialog.getExistingDirectory(None, "Select Output Folder")
    if not output_path:
        print("No output folder selected.")
        return

    # preocess and save EDF data
    preocess_edf_data(edf_file_path, output_path)
    
    # preocess and save trigger data
    preocess_trigger_data(trigger_file_path, output_path)

if __name__ == '__main__':
    main()
