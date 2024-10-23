import re
import os
import mne
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import PyQt5.QtWidgets as QtWidgets
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QPushButton, QComboBox, QVBoxLayout, QHBoxLayout,QLabel,QWidget, QDoubleSpinBox, QTableWidget, QTableWidgetItem, QLineEdit           
from utils import QEEGPatient, misc, segmentWindow
import json

settingWindow = None

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

########### SET DEFAULT PARAMETER ##############################################################
        
        self.FILTER_50HZ = True

        self.SAMPLING_FREQUENCY = 256 # per second
        self.STRESS_QUADRANT_OFFSET = 1 # seconds
        self.STRESS_SUBSEGMENT_OFFSET = 0.5 # seconds
        self.OVERLAPPING = 0 # percentage
        # self.segmentExtend = True # slide Q segment Extend?
        # self.plottingSegment = False # plot segment plot?
        self.ylimit = 5e-4

        self.edf_file_path = None
        self.excel_file_path = None
        self.save_folder_path = None
        self.subjectsfolder  = None
################################################################################################
        self.raw = None
        self.trigger = None
        self.minStressLength = float("inf") # ensure any valid length is smaller
        self.patient_data = {}
        self.trigger_data = {}
        self.windowWidth = None

        self.currentPatient = None
        self.patientNo = 0

        self.setWindowTitle("EEG Slicer")
        self.setGeometry(100, 100, 1400, 800)

        layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        
        self.SubjectsFolder = QPushButton("Upload Subjects Folder", self)
        self.selectSaveFolder = QPushButton("Select Export Folder", self)
        self.setting_btn = QPushButton("Setting", self)

        self.extendQ_label = QLabel("Q-Extend Offset")
        self.QUADRANT_OFFSET_spinbox = QDoubleSpinBox()
        self.extendSS_label = QLabel("S/NS SubSegment-Extend Offset")
        self.SUBSEGMENT_OFFSET_spinbox = QDoubleSpinBox()
        self.LABEL_OFFSETQ = QLabel(f"Quadrant Offset Value : {self.STRESS_QUADRANT_OFFSET}")
        self.LABEL_OFFSETSS = QLabel(f"Subsegment Offset Value : {self.STRESS_SUBSEGMENT_OFFSET}")
        self.LABEL_WindowWidth = QLabel(f"Window Width Value : {self.windowWidth}")
        self.LABEL_OVERLAPPING = QLabel(f"Overlapping Value : {self.OVERLAPPING}")

        self.confirm_btn = QPushButton("Slide && Export", self)

        # self.stress_btn = QPushButton("Stress", self)

        self.edf_label = QLabel("No EDF file uploaded", self)
        self.excel_label = QLabel("No Excel file uploaded", self)
        self.savefolder_label = QLabel("No Save folder select", self)

        self.canvas = FigureCanvas(plt.Figure())
        self.canvasT = FigureCanvas(plt.Figure())

        self.patientInfoTable = QTableWidget(1,8)
        self.patientInfoTable.setHorizontalHeaderLabels(
            ["Subject ID", "Raw EEG", "Length (Datapoint)", "Length (Second)", "Length (Minute)", "CH_list","CH_num","Segments"]
            )
        self.patientInfoTable.setMinimumHeight(240)
        
        header = self.patientInfoTable.horizontalHeader()  
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)       
        header.setSectionResizeMode(7, QtWidgets.QHeaderView.Stretch)
        
        container = QWidget()
        self.patient_selector = QComboBox()

        self.SubjectsFolder.clicked.connect(self.upload_folder)
        self.selectSaveFolder.clicked.connect(self.setExportFolder)
        self.setting_btn.clicked.connect(self.configureSetting)
        self.confirm_btn.clicked.connect(self.startSlicing)

        self.QUADRANT_OFFSET_spinbox.valueChanged.connect(self.QSPINBOX)
        self.SUBSEGMENT_OFFSET_spinbox.valueChanged.connect(self.SSPINBOX)
        
        main_layout_components = [self.SubjectsFolder,self.selectSaveFolder, self.edf_label,  self.excel_label,
                                  self.savefolder_label, self.canvas, self.canvasT, self.patientInfoTable] # self.excel_upload_btn,

        button_layout_components = [self.LABEL_OFFSETQ, self.LABEL_OFFSETSS, 
                                     self.LABEL_OVERLAPPING, 
                                    self.setting_btn,  
                    # self.ylimit_label, self.plotylimit_spinbox, 
                    self.confirm_btn] # self.overlapping_label, self.overlapping_spinbox ,self.slice_all_btn, self.baseline_btn, self.simulation_btn, self.Q1_btn, self.Q2_btn,
                    # self.Q3_btn, self.Q4_btn, self.floss_btn,
        
        for component in main_layout_components:
            layout.addWidget(component)

        for component in button_layout_components:
            button_layout.addWidget(component)

        layout.addLayout(button_layout)
        container.setLayout(layout)
        self.setCentralWidget(container)

    def QSPINBOX(self):
        self.STRESS_QUADRANT_OFFSET = np.round(self.QUADRANT_OFFSET_spinbox.value(),2)
        self.LABEL_OFFSETQ.setText(f"Quadrant Offset Value : {self.STRESS_QUADRANT_OFFSET}")

    def SSPINBOX(self):
        self.STRESS_SUBSEGMENT_OFFSET = np.round(self.SUBSEGMENT_OFFSET_spinbox.value(),2)
        self.LABEL_OFFSETSS.setText(f"Subsegment Offset Value : {self.STRESS_SUBSEGMENT_OFFSET}")

    def startSlicing(self):
        self.start_time = time.time()
        print("Start Slicing!")
        
        if self.subjectsfolder:
            # loop through each patient
            for subject_folder in os.listdir(self.subjectsfolder): 
                subject_path = os.path.join(self.subjectsfolder, subject_folder)

                if os.path.isdir(subject_path):
                    edf_files = [f for f in os.listdir(subject_path) if f.endswith(".edf")]
                    xlsx_files = [f for f in os.listdir(subject_path) if f.endswith(".xlsx")]

                    if not edf_files:
                        print(f"No EDF files found in {subject_folder}")
                        continue
                    
                    edf_file = edf_files[0] # get only first edf
                    self.edf_file_path = os.path.join(subject_path, edf_file)
                    print(f"Processing EDF File: {self.edf_file_path} in {subject_folder}")
                    
                    subject_id = re.search(r'Subject(\d+)', self.edf_file_path).group(1)
                    self.patient_data[subject_id] = mne.io.read_raw_edf(self.edf_file_path, preload=True)
                    
                    self.plot_edf_data(subject_id)
                    self.patient_selector.addItem(subject_id)

                    if not xlsx_files:
                        print(f"No xlsx files found in {subject_folder}")
                        continue
                    
                    for xlsx_file in xlsx_files:
                        fullxlsx_path = os.path.join(subject_path, xlsx_file)
                        print(f"Processing xlsx File: {xlsx_file} in {subject_folder}")
                        fullxlsx_path = os.path.normpath(fullxlsx_path)
                        self.excel_file_path = fullxlsx_path

                        # print(self.excel_file_path)
                        self.trigger_data[subject_id] = pd.read_excel(fullxlsx_path, engine='openpyxl')
                    
                    
                        
                    self.plot_trigger(subject_id)
                    self.slice_all()

                self.minStressLength = float("inf") # reset min stress length of patient
                print(f"Patient {subject_id} processed")
            self.edf_label.setText(f"Processed EDF files from {self.subjectsfolder}")
            self.excel_label.setText(f"Processed xlsx files from {self.subjectsfolder}")
            print("All patients processed.")
            print("--- RUNTIME : %.2f seconds ---" % (time.time() - self.start_time))

    def setExportFolder(self):
        if self.save_folder_path is None:
            self.save_folder_path = QFileDialog.getExistingDirectory(self, "Select Output Folder")
            if not self.save_folder_path:
                print("No save folder selected.")
                return
            
            print("+" *20)
            print("Selected output folder TO ", self.save_folder_path)
            print("+" *20) 
            self.savefolder_label.setText(f"Set Export Folder to {self.save_folder_path}")
            
    def configureSetting(self):
        
        if hasattr(self, 'settingWindow') and self.settingWindow:
                self.settingWindow.show()
                return

        settinglayout = QVBoxLayout()
        self.settingWindow = QWidget()

        self.patient_selector_label = QLabel("Patient Selected : ", self)

        self.settingWindow.setWindowTitle(f"Slide Setting")
        self.settingWindow.setGeometry(100, 100, 220, 280)

        ww_label = QLabel("Window Width (second): (No input req. for trad. method)", self)
        ww_edit = QLineEdit("windowWidth", self)
        op_label = QLabel("Overlapping (0-100) :", self)
        self.op_edit = QLineEdit(self)
        confirm_btn = QPushButton("Confirm Setting", self)
        
        self.overlapping_lineedit = QLineEdit()

        self.QUADRANT_OFFSET_spinbox.setRange(0, 10.0)  
        self.QUADRANT_OFFSET_spinbox.setSingleStep(0.05)
        self.QUADRANT_OFFSET_spinbox.setValue(1.0) 

        self.SUBSEGMENT_OFFSET_spinbox.setRange(0, 10.0)  
        self.SUBSEGMENT_OFFSET_spinbox.setSingleStep(0.05)
        self.SUBSEGMENT_OFFSET_spinbox.setValue(0.5)

        if not hasattr(self, 'patient_selector'):
            self.patient_selector = QComboBox(self)

        widgets = [self.patient_selector_label, self.patient_selector, self.extendQ_label,
                    self.QUADRANT_OFFSET_spinbox, self.extendSS_label , self.SUBSEGMENT_OFFSET_spinbox,
                    ww_label, ww_edit, op_label, self.op_edit, confirm_btn]
        
        confirm_btn.clicked.connect(self.confirmSetting)

        for widget in widgets:
            settinglayout.addWidget(widget)

        self.settingWindow.setLayout(settinglayout)
        self.settingWindow.show()
    
    def upload_folder(self):
        folder_dialog = QFileDialog()
        self.subjectsfolder = folder_dialog.getExistingDirectory(self, "Select Folder Containing Subject Folders")
                
        self.patient_selector.clear() # when upload new patient set
        print("Uploaded subject folder: ", self.subjectsfolder)
        self.edf_label.setText(f"Loaded EDF file")
        self.excel_label.setText(f"Loaded xlsx file")


    def confirmSetting(self):
        self.patient_selector.currentIndexChanged.connect(self.update_plots)
        self.updateOverlapping()
        self.settingWindow.close()
    
    def update_plots(self):
        subject_id = self.patient_selector.currentData()

        if subject_id and subject_id in self.patient_data:
            
            self.plot_edf_data(subject_id)
            if subject_id in self.trigger_data:
                self.trigger = self.trigger_data[subject_id]
                self.plot_trigger(subject_id)

            
    def add_patientInfoTable(self, patient): 
        # print("Patient : ", patient.subject_id)
        self.patientInfoTable.setRowCount(self.patientNo)  
        self.patientInfoTable.insertRow(self.patientNo)

        self.patientInfoTable.setItem(
            self.patientNo, 0, QTableWidgetItem(patient.subject_id))
        self.patientInfoTable.setItem(
            self.patientNo, 1, QTableWidgetItem( str(patient.full_raw)))
        self.patientInfoTable.setItem(   # Length datapoint
            self.patientNo, 2, QTableWidgetItem( str(patient.full_raw.shape[1])))
        self.patientInfoTable.setItem(   # Length second
            self.patientNo, 3, QTableWidgetItem( str(  np.round((patient.full_raw.shape[1] / 
                                                                 self.SAMPLING_FREQUENCY),2)   )))
        self.patientInfoTable.setItem(    
            self.patientNo, 4, QTableWidgetItem( str(  np.round(((patient.full_raw.shape[1] / 
                                                                  self.SAMPLING_FREQUENCY)/60),2)  )))
        self.patientInfoTable.setItem(
            self.patientNo, 5, QTableWidgetItem( str(patient.ch_list)))
        self.patientInfoTable.setItem(
            self.patientNo, 6, QTableWidgetItem( str( len(patient.ch_list) )))
        self.patientInfoTable.setItem(
            self.patientNo, 7, QTableWidgetItem( str(patient.segments)))
        
        segment_btn = QPushButton(f"Show Segments")
        segment_btn.clicked.connect(lambda: segmentWindow.showSegmentTable(patient.segments, 
                                                                           patient.subject_id))
        self.patientInfoTable.setCellWidget(self.patientNo, 7, segment_btn)

        self.patientNo += 1  # Move to next patient
        

# segment & plot ------------------------------------------------------------------------------------

    def map_segment(self, segmentName, activate):  # BL, PI, SIM, Q1S, Q1NS, Q2S, ...
        if self.raw is None or self.trigger is None:
            return
        
        if segmentName in ["Baseline"]:  # baseline, no extend
            for i in range(2):
                idx = np.where(self.trigger[segmentName] == activate)[0]
                interval = misc.group_number(idx) # interval 0 = Baseline, 1 = Post Intervention
                interval_datapoint = misc.convert_timescale(interval, self.SAMPLING_FREQUENCY)
                if i ==1:
                    segmentName = "Post-Intervention" 
                    self.cut_segment(interval_datapoint[1:], segmentName, activate)
                else:
                    self.cut_segment(interval_datapoint[:1], segmentName, activate)

        elif segmentName in ['Q1','Q2','Q3','Q4']:  
            idx = np.where(self.trigger[segmentName] == activate)[0]
            interval = misc.group_number(idx) # interval 0 = Baseline, 1 = Post Intervention
            interval_datapoint = misc.convert_timescale(interval, self.SAMPLING_FREQUENCY)

            offset = self.STRESS_QUADRANT_OFFSET * self.SAMPLING_FREQUENCY
            # print("IDP", interval_datapoint)
            interval_datapoint[0][0] -= offset
            interval_datapoint[0][1] += offset
            # print("IDP offset", interval_datapoint)
            self.cut_segment(interval_datapoint, segmentName, activate)
                
        else :  # No extend,     # Simulation, Floss
            idx = np.where(self.trigger[segmentName]==activate)[0]
            interval = misc.group_number(idx)
            interval_datapoint = misc.convert_timescale(interval, self.SAMPLING_FREQUENCY)
            self.cut_segment(interval_datapoint, segmentName, activate)

    def cut_segment(self, interval_datapoint, segmentName, activate):
        if self.raw is None or self.trigger is None:
            return
        
        # interval_count = len(interval_datapoint)
        # print("IntCopunt" , interval_count)
        # for i in range(interval_count):
        start_idx = int(interval_datapoint[0][0])
        stop_idx = int(interval_datapoint[0][1])
    
        # start_idx = int(interval_datapoint[0][0])
        # stop_idx = int(interval_datapoint[0][1])

        self.segmentdata, self.segmentTimes = self.raw[:, start_idx:stop_idx]  # segment cut
        if(len(self.segmentTimes)!=0):
            self.segmentPoint = (self.segmentTimes - self.segmentTimes[0]) * self.SAMPLING_FREQUENCY
            self.cut_subSegment(segmentName, activate, self.segmentdata, self.segmentTimes)

            # Add segment to patient Information ##########################################################
            if( segmentName in ["Q1","Q2","Q3","Q4"] ): # and self.segmentExtend
                extend = True
                segmentName = segmentName+"_Extend"
            else :
                extend = False
                segmentName = segmentName+"_Intend"

            self.currentPatient.add_segment(segmentName, self.segmentdata, self.segmentTimes, extend, interval_datapoint)
            self.save_segment(segmentName, self.segmentdata, self.segmentTimes)


        

    def save_segment(self, segmentName, segmentData, segmentTimes):
        if segmentName is None:
            return
        
        if  self.save_folder_path is None:
            print("Please Select Save Folder")
            return

        patient_segment_folder = os.path.join(self.save_folder_path,f'Patient_{self.currentPatient.subject_id}', "Segment")
        
        os.makedirs(patient_segment_folder, exist_ok=True)
        save_path = os.path.join(patient_segment_folder, f'Segment_{segmentName}.json')
        n_channels = segmentData.shape[0]

        # print("+" *20)
        # print("SAVE SEGMENT", segmentData.shape ," to ", save_path)
        segment_json = {
            "segment_name" : segmentName,
            "length(s)"    : np.round(segmentData.shape[1]/self.SAMPLING_FREQUENCY,2),
            "data"         : segmentData.tolist(),
            "times"        : segmentTimes.tolist(),
            "n_chan"       : n_channels,
            "fs"           : self.SAMPLING_FREQUENCY,
            "shape"        : segmentData.shape
        }

        try:
            with open(save_path,"w") as outfile:
                json.dump(segment_json, outfile)
            # print(f"Segment saved at: {save_path}")
        except OSError as e:
            print(f"Error saving segment: {e}")

#########################################################################################
    def cut_subSegment(self, segmentName, activate , segmentdata, segmentTimes):

        if segmentName in ['Q1','Q2','Q3','Q4']:  
            # SUBSEGMENT OFFSET : +- 0.5 s ############################################################### 
            offset = self.STRESS_SUBSEGMENT_OFFSET * self.SAMPLING_FREQUENCY
            segment_start_time = segmentTimes[0]
            start_datapoint = int(segment_start_time*self.SAMPLING_FREQUENCY)
            # print("start datapoint :",start_datapoint)
            # print("start time : ", segment_start_time)
            for i in range(2):  # 0 non stress,   # 1 :stress interval
                idx = np.where((self.trigger['Stress']==i) & (self.trigger[segmentName]==activate))[0] 
                interval = misc.group_number(idx)
                interval_datapoint = misc.convert_timescale(interval, self.SAMPLING_FREQUENCY)
                
                stress_suffix = "_Non-Stress" if i==0 else "_Stress"
                print("#"*40)
                print(f"Processing {stress_suffix} intervals.")
                print("SegmentName :", segmentName)
                print("#"*20)
                print("Check Data BEFORE : ", segmentdata.shape)

                for js in range(len(interval)):
                    start_idx = interval_datapoint[js][0]-start_datapoint
                    stop_idx = interval_datapoint[js][1]-interval_datapoint[js][0]+start_idx

                    start_idx -= offset
                    stop_idx += offset

                    subSegmentData = segmentdata[:, int(start_idx): int(stop_idx)]
                    subSegmentTimes = segmentTimes[ int(start_idx): int(stop_idx)]
                    print("Check Data AFTER : ", subSegmentData.shape)
                    
                    subSegmentName = segmentName+stress_suffix+"_"+str(js+1)
                    # print("SubSegnebtBane", subSegmentName)
                    self.save_subSegment(subSegmentName, subSegmentData, subSegmentTimes)
        elif segmentName in ["Baseline","Floss_teeth","Post-Intervention","Simulate_teeth_scraping"]:
            subSegmentName = segmentName+"_sub"
            # print("SubSegnebtBane", subSegmentName)
            self.save_subSegment(subSegmentName, segmentdata, segmentTimes)

    def find_min_stress_length(self):
        segment_map = {
        'Q1': 'p',
        'Q2': 'q',
        'Q3': 'r',
        'Q4': 's'
        }
        
        for segmentName, activate in segment_map.items():
            for i in range(2):  # 0: non-stress, 1: stress intervals
                idx = np.where((self.trigger['Stress'] == i) & (self.trigger[segmentName] == activate))[0]
                interval = misc.group_number(idx)
                interval_datapoint = misc.convert_timescale(interval, self.SAMPLING_FREQUENCY)

                for js in range(len(interval)):
                    start_idx = interval_datapoint[js][0]
                    stop_idx = interval_datapoint[js][1]
                    length = stop_idx - start_idx
                    print("#"*20)
                    print("start_stop " , start_idx, stop_idx)
                    
                    print("length ", length)

                    if length < self.minStressLength:
                        if length >= self.SAMPLING_FREQUENCY*(1.5):
                            self.minStressLength = length
                        print(f"Updated minStressLength to: {self.minStressLength}")
                        self.windowWidth = self.minStressLength
                        self.LABEL_WindowWidth.setText(f"WindowWidth : {self.windowWidth}")


    def save_subSegment(self, subSegmentName, subSegmentData, subSegmentTimes):
        if subSegmentName is None:
            return
        
        self.cut_slice(subSegmentName, subSegmentData, subSegmentTimes) # send every subsegment to slicing
        
        if  self.save_folder_path is None:
            print("Please Select Save Folder")
            return
        
        patient_ss_folder = os.path.join(self.save_folder_path,f'Patient_{self.currentPatient.subject_id}',"SubSegment")
        
        os.makedirs(patient_ss_folder, exist_ok=True)
        save_path = os.path.join(patient_ss_folder, f'SubSegment_{subSegmentName}.json')
        n_channels = subSegmentData.shape[0]

        # print("+" *20)
        # print("SAVE SUBSEGMENT", subSegmentData.shape ," to ", save_path)
        subSegment_json = {
            "subSegment_name" : subSegmentName,
            "length(s)"    : np.round(subSegmentData.shape[1]/self.SAMPLING_FREQUENCY,2),
            "data"         : subSegmentData.tolist(),
            "times"        : subSegmentTimes.tolist(),
            "n_chan"       : n_channels,
            "fs"           : self.SAMPLING_FREQUENCY,
            "shape"        : subSegmentData.shape
        }

        try:
            with open(save_path,"w") as outfile:
                json.dump(subSegment_json, outfile)
            # print(f"SubSegment saved at: {save_path}")
        except OSError as e:
            print(f"Error saving SubSegment: {e}")

    def cut_slice(self, subSegmentName , subSegmentData, subSegmentTimes):
        
        data_length = subSegmentData.shape[1]
        numWindow = np.floor(1+( data_length - self.windowWidth )/(self.windowWidth*(1-(self.OVERLAPPING/100))))

        print(f"cut slice from subsegment : {subSegmentName}")
        print(subSegmentData.shape[1])

        print(f"data length : {data_length}")
        print("Slice size = smallest stress subsegment : ", self.windowWidth)
        # print(f"Number of Slice = 1+({data_length} - {self.windowWidth})/({self.windowWidth}*(1 - ({self.OVERLAPPING}/100)))")
        print(f"Number of Slice for {subSegmentName} is {numWindow} " )   

        slicefolderName = subSegmentName+"_"+ str(numWindow)
        patient_slice_folder = os.path.join(self.save_folder_path, f'Patient_{self.currentPatient.subject_id}', "Slice", slicefolderName)
        
        os.makedirs(patient_slice_folder, exist_ok=True)

        for i in range(int(numWindow)):
            start_idx = int(i * self.windowWidth)
            stop_idx = int(start_idx + self.windowWidth)
            sliceName = subSegmentName + "_Slice_"  +str(i+1)

            sliceData = subSegmentData[ :, start_idx : stop_idx]
            sliceTimes = subSegmentTimes[ start_idx: stop_idx]
            self.save_slice(sliceName, sliceData, sliceTimes, numWindow, patient_slice_folder)

    def save_slice(self, sliceName, sliceData, sliceTimes, numWindow, patient_slice_folder):
        if sliceName is None:
            return
        
        
        save_path = os.path.join(patient_slice_folder, f'Slice_{sliceName}.json')
        n_channels = sliceData.shape[0]

        # print("+" *20)
        # print("SAVE SUBSEGMENT", sliceData.shape ," to ", save_path)
        slice_json = {
            "slice_name"   : sliceName,
            "length(s)"    : np.round(sliceData.shape[1]/self.SAMPLING_FREQUENCY,2),
            "totalWindow"  : numWindow,
            "data"         : sliceData.tolist(),
            "times"        : sliceTimes.tolist(),
            "n_chan"       : n_channels,
            "fs"           : self.SAMPLING_FREQUENCY,
            "shape"        : sliceData.shape
        }

        try:
            with open(save_path,"w") as outfile:
                json.dump(slice_json, outfile)
            # print(f"Slice saved at: {save_path}")
        except OSError as e:
            print(f"Error saving SubSegment: {e}")
        # print("+" *20)


    def plot_edf_data(self, subject_id):
        if subject_id not in self.patient_data:
            print(f"No data found for subject {subject_id}")
            return

        self.raw = self.patient_data[subject_id]
        self.SAMPLING_FREQUENCY   = self.raw.info['sfreq']
        
        # PREPROCESSING ####################################################################
        if self.FILTER_50HZ:
            self.raw = self.raw.notch_filter(freqs=50)

# FULL LENGTH
            
        data, times = self.raw[:, :]
        times = times*self.SAMPLING_FREQUENCY
        # edf_length_second = times.shape[0]/256
        # edf_length_minute=np.round(edf_length_second/60,2)
        ch_names = [ch_name[4:] for ch_name in self.raw.ch_names]

# Patient Class Information record ########################################################
        self.currentPatient = QEEGPatient.QEEGPatient(
            subject_id,
            data,
            ch_names,
            )
# #########################################################################################
        self.add_patientInfoTable(self.currentPatient)
        
        print("#"*20)
        print("Patient : ", self.currentPatient.subject_id)
        # print("Raw data: ", self.currentPatient.full_raw)
        # print("Channel List:", self.currentPatient.ch_list)
        print("EDF Data",   data.shape)
        
        # Plot the data
        # self.raw.plot(scalings='auto', show=True)
            
        self.canvas.figure.clear()
        ax = self.canvas.figure.add_subplot(111)
        # use time as sample
        ax.plot(times, data.T)
        ax.set_title('Raw EDF Data')
        ax.set_xlabel('Time (datapoint)')
        ax.set_ylabel('Value')

        xlimit = misc.roundup_datapoint(times.shape[0])
        ax.set_xlim(xmax = xlimit)

        self.canvas.draw()

    def plot_trigger(self, subject_id):
        if subject_id not in self.trigger_data:
            return
        # baselineInt = 0
        self.trigger = self.trigger_data[subject_id]

        if self.minStressLength > 1e6: # do it once per patient
            self.find_min_stress_length()
        

        for i in ['Baseline','Simulate_teeth_scraping','Floss_teeth']:
            # if (i=="Baseline"):
                # baselineInt+=1
            self.trigger[i] = pd.to_numeric(self.trigger[i], errors='coerce')

        self.trigger['Sample'] = self.trigger['Time'].apply(lambda x: misc.convert_datetime_sample(x, self.SAMPLING_FREQUENCY))
        self.trigger['Q1N'] = self.trigger["Q1"].apply(lambda x: misc.convertQtoInt(x,"p"))
        self.trigger['Q2N'] = self.trigger["Q2"].apply(lambda x: misc.convertQtoInt(x,"q"))
        self.trigger['Q3N'] = self.trigger["Q3"].apply(lambda x: misc.convertQtoInt(x,"r"))
        self.trigger['Q4N'] = self.trigger["Q4"].apply(lambda x: misc.convertQtoInt(x,"s"))

        # print("BL length (0.5s per datapoint):",self.trigger['Baseline'].shape)
        halfsample = int(self.trigger["Sample"].shape[0]/2)
        self.canvasT.figure.clear()
        ax2 = self.canvasT.figure.add_subplot(111)
        ax2.plot( self.trigger['Sample'][ : halfsample ], self.trigger['Baseline'][ : halfsample ],color="black",label="Baseline")
        ax2.plot( self.trigger['Sample'], self.trigger['Simulate_teeth_scraping'],color="blue",label="Simulation")
        ax2.plot( self.trigger['Sample'], self.trigger['Q1N'],color="red",label="Q1")
        ax2.plot( self.trigger['Sample'], self.trigger['Q2N'],color="green",label="Q2")
        ax2.plot( self.trigger['Sample'], self.trigger['Q3N'],color="cyan",label="Q3")
        ax2.plot( self.trigger['Sample'], self.trigger['Q4N'],color="yellow",label="Q4")
        ax2.plot( self.trigger['Sample'], self.trigger['Floss_teeth'],color="olive",label="Floss_teeth")
        ax2.plot( self.trigger['Sample'], self.trigger['Stress'],color="goldenrod",label="Stress")
        ax2.fill_between( self.trigger['Sample'],  self.trigger['Stress'],color="goldenrod", alpha=0.3)
        ax2.plot( self.trigger['Sample'][halfsample : ], self.trigger['Baseline'][halfsample : ],color="Gray",label="Post_Intervention")

        ax2.set_title('Trigger')
        ax2.set_xlabel('Time (datapoint)')
        ax2.set_ylabel('Value')
        ax2.legend()
        # seconds * sampling rate = datapoint
        xxlimit = misc.roundup_datapoint((self.trigger['Sample'].shape[0]*self.SAMPLING_FREQUENCY)/2) # 2 datapoint = 1 second
        ax2.set_xlim(xmax = xxlimit)

        self.canvasT.draw()

# UI ------------------------------------------------------------------------------------

    def updateOverlapping(self):
        if self.op_edit.text() =="":
            return
        if (int(self.op_edit.text())<=100):
            try :
                    self.OVERLAPPING = int(self.op_edit.text())
                    self.LABEL_OVERLAPPING.setText(f"Overlapping Value : {self.OVERLAPPING}")
            except:
                print("Invalid overlapping value.")
        else: 
            print("Please enter valid overlapping value. * Automatically set the overlapping to 0 *")
        print("Set overlapping = ", self.OVERLAPPING)
            
    def slice_all(self):
        if self.raw is None or self.trigger is None:
            return
        
        self.map_segment("Baseline",1)
        self.map_segment("Simulate_teeth_scraping",1)

        self.map_segment("Q1","p")   
        self.map_segment("Q2","q")
        self.map_segment("Q3","r")
        self.map_segment("Q4","s")

        self.map_segment("Floss_teeth",1)

# EDF ------------------------------------------------------------------------        
    # def upload_edf_file(self):

    #     file_dialog = QFileDialog()
    #     edf_file, _ = file_dialog.getOpenFileName(self, "Select EDF File", "", "EDF Files (*.edf)")
        
    #     if edf_file: # and it's new patient-> add new subject ID _> add new row to table
    #         self.edf_file_path = edf_file
    #         self.edf_label.setText(f"EDF File: {edf_file}")
    #         self.plot_edf_data()
# EXCEL ------------------------------------------------------------------------------------
    # def upload_excel_file(self): # single
    #     file_dialog = QFileDialog()
    #     excel_file, _ = file_dialog.getOpenFileName(self, "Select Excel File", "", "Excel Files (*.xlsx *.xls)")
        
    #     if excel_file:
    #         self.excel_file_path = excel_file
    #         self.excel_label.setText(f"Excel File: {excel_file}")
    #         self.read_excel_data()