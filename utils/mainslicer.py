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
from utils import QEEGPatient, misc, segmentWindow, searchWindow
import json

settingWindow = None

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

########### SET DEFAULT PARAMETER ##############################################################
        
        self.FILTER_50HZ = True

        self.SAMPLING_FREQUENCY = 256 # per second
        self.STRESS_QUADRANT_OFFSET = 1 # seconds
        self.STRESS_SLICE_OFFSET = 0.5 # seconds
        # self.OVERLAPPING = 0 # percentage
        self.segmentExtend = True # slide Q segment Extend?
        # self.plottingSegment = False # plot segment plot?
        self.ylimit = 5e-4

        self.edf_file_path = None
        self.excel_file_path = None
        self.save_folder_path = None
################################################################################################
        self.raw = None
        self.trigger = None

        self.patient_data = {}
        self.trigger_data = {}

        self.currentPatient = None
        self.patientNo = 0

        self.setWindowTitle("EEG Slicer")
        self.setGeometry(100, 100, 1400, 800)

        layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        
        self.uploadSubjectsFolder = QPushButton("Upload Subjects Folder", self)
        # self.excel_upload_btn = QPushButton("Upload Excel File", self)
        # self.baseline_btn = QPushButton("Baseline", self)
        # self.simulation_btn = QPushButton("Simulation", self)
        # self.slice_all_btn = QPushButton("Slice All",self)
        # self.Q1_btn = QPushButton("Quadrant1", self)
        # self.Q2_btn = QPushButton("Quadrant2", self)
        # self.Q3_btn = QPushButton("Quadrant3", self)
        # self.Q4_btn = QPushButton("Quadrant4", self)
        # self.floss_btn = QPushButton("Floss", self)
        self.setting_btn = QPushButton("Setting", self)
        self.Extend_btn = QPushButton("Q-Extend")
        self.QUADRANT_OFFSET_spinbox = QDoubleSpinBox()
        # self.ylimit_label = QLabel("Ylimit",self)
        # self.plotylimit_spinbox = QDoubleSpinBox(self)
        # self.overlapping_label = QLabel("Overlapping Window %:",self)
        # self.overlapping_spinbox = QDoubleSpinBox(self)

        self.confirm_btn = QPushButton("Start Sliding", self)

        # self.stress_btn = QPushButton("Stress", self)

        self.edf_label = QLabel("No EDF file uploaded", self)
        self.excel_label = QLabel("No Excel file uploaded", self)

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
        
        self.Extend_btn.setStyleSheet("background-color : coral") 
        self.QUADRANT_OFFSET_spinbox.setRange(0.5, 10.0)  
        self.QUADRANT_OFFSET_spinbox.setSingleStep(0.5)
        self.QUADRANT_OFFSET_spinbox.setValue(1.0)

        # self.plotylimit_spinbox.setRange(0.00005, 0.005) 
        # self.plotylimit_spinbox.setSingleStep(0.00005)
        # self.plotylimit_spinbox.setDecimals(5)
        # self.plotylimit_spinbox.setValue(0.0005)

        # self.overlapping_spinbox.setRange(0, 1) 
        # self.overlapping_spinbox.setSingleStep(0.05)
        # self.overlapping_spinbox.setValue(0)

        # self.plotylimit_spinbox.valueChanged.connect(self.updateylimit)
        self.QUADRANT_OFFSET_spinbox.valueChanged.connect(self.updateQoffset)
        # self.overlapping_spinbox.valueChanged.connect(self.updateOverlapping)
        self.confirm_btn.clicked.connect(searchWindow.openSearchWindow)

        self.uploadSubjectsFolder.clicked.connect(self.upload_folder)
        # self.excel_upload_btn.clicked.connect(self.upload_excel_folder)
        # self.slice_all_btn.clicked.connect(self.slice_all)
        # self.baseline_btn.clicked.connect(lambda : self.map_segment("Baseline",1))
        # self.simulation_btn.clicked.connect(lambda : self.map_segment("Simulate_teeth_scraping",1))
        # self.Q1_btn.clicked.connect(lambda : self.map_segment("Q1","p"))
        # self.Q2_btn.clicked.connect(lambda : self.map_segment("Q2","q"))
        # self.Q3_btn.clicked.connect(lambda : self.map_segment("Q3","r"))
        # self.Q4_btn.clicked.connect(lambda : self.map_segment("Q4","s"))
        self.setting_btn.clicked.connect(self.configureSetting)
        self.Extend_btn.clicked.connect(self.toggleExtend)
        # self.floss_btn.clicked.connect(lambda : self.map_segment("Floss_teeth",1))
        # self.stress_btn.clicked.connect(lambda : self.map_segment("Stress",1))
        
        main_layout_components = [self.uploadSubjectsFolder, self.edf_label,  self.excel_label,
                                  self.canvas, self.canvasT, self.patientInfoTable] # self.excel_upload_btn,

        button_layout_components = [self.setting_btn,  
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

    def configureSetting(self):
        global settingWindow
        settinglayout = QVBoxLayout()
        settingWindow = QWidget()
        

        settingWindow.setWindowTitle(f"Slide Setting")
        settingWindow.setGeometry(100, 100, 320, 280)

        ww_label = QLabel("Window Width (second): ", self)
        ww_edit = QLineEdit()
        op_label = QLabel("Overlapping (0-100) :", self)
        op_edit = QLineEdit()
        confirm_btn = QPushButton("Confirm Setting", self)
        
        widgets = [self.patient_selector, self.Extend_btn, self.QUADRANT_OFFSET_spinbox, ww_label, ww_edit, op_label, op_edit, confirm_btn]
        
        self.patient_selector.currentIndexChanged.connect(self.update_plots)

        for i in widgets:
            settinglayout.addWidget(i)


        settingWindow.setLayout(settinglayout)
        settingWindow.show()
    
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
            self.patientNo, 3, QTableWidgetItem( str(  np.round((patient.full_raw.shape[1] / self.SAMPLING_FREQUENCY),2)   )))
        self.patientInfoTable.setItem(    
            self.patientNo, 4, QTableWidgetItem( str(  np.round(((patient.full_raw.shape[1] / self.SAMPLING_FREQUENCY)/60),2)  )))
        self.patientInfoTable.setItem(
            self.patientNo, 5, QTableWidgetItem( str(patient.ch_list)))
        self.patientInfoTable.setItem(
            self.patientNo, 6, QTableWidgetItem( str( len(patient.ch_list) )))
        self.patientInfoTable.setItem(
            self.patientNo, 7, QTableWidgetItem( str(patient.segments)))
        
        segment_btn = QPushButton(f"Show Segments")
        segment_btn.clicked.connect(lambda: segmentWindow.showSegmentTable(patient.segments, patient.subject_id))
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
                    self.cut_segment(interval_datapoint[1:], segmentName)
                else:
                    self.cut_segment(interval_datapoint[:1], segmentName)

        elif segmentName in ['Q1','Q2','Q3','Q4']:  
            
            idx = np.where(self.trigger[segmentName] == activate)[0]
            interval = misc.group_number(idx) # interval 0 = Baseline, 1 = Post Intervention
            interval_datapoint = misc.convert_timescale(interval, self.SAMPLING_FREQUENCY)

            # Quadrant, extend ( 1s each)
            # Segment Offset : +- 1 s ####################################################################   
            if self.segmentExtend: # tradtional method
                offset = self.STRESS_QUADRANT_OFFSET * self.SAMPLING_FREQUENCY
                print("IDP", interval_datapoint)
                interval_datapoint[0][0] -= offset
                interval_datapoint[0][1] += offset
                print("IDP offset", interval_datapoint)
            self.cut_segment(interval_datapoint, segmentName)
                
        else :  # No extend,     # Simulation, Floss
            idx = np.where(self.trigger[segmentName]==activate)[0]
            interval = misc.group_number(idx)
            interval_datapoint = misc.convert_timescale(interval, self.SAMPLING_FREQUENCY)
            self.cut_segment(interval_datapoint, segmentName)

    def cut_segment(self, interval_datapoint, segmentName):
        if self.raw is None or self.trigger is None:
            return
        
        # interval_count = len(interval_datapoint)
        # print("IntCopunt" , interval_count)
        # for i in range(interval_count):
            # start_idx = int(interval_datapoint[i][0])
            # stop_idx = int(interval_datapoint[i][1])
        
        start_idx = int(interval_datapoint[0][0])
        stop_idx = int(interval_datapoint[0][1])

        self.segmentdata, self.segmentTimes = self.raw[:, start_idx:stop_idx]  # segment cut
        if(len(self.segmentTimes)!=0):
            self.segmentPoint = (self.segmentTimes - self.segmentTimes[0]) * self.SAMPLING_FREQUENCY

            if( segmentName in ["Q1","Q2","Q3","Q4"] and self.segmentExtend):
                extend = True
                # SUBSEGMENT OFFSET : +- 0.5 s ############################################################### 
                offset = self.STRESS_SLICE_OFFSET * self.SAMPLING_FREQUENCY
                for i in range(2):  # 0 non stress,   # 1 :stress interval
                    idx = np.where(self.trigger['Stress']==i)[0] 
                    interval = misc.group_number(idx)
                    interval_datapoint = misc.convert_timescale(interval, self.SAMPLING_FREQUENCY)
                    
                    if (i==0):
                        stress_suffix = "_Non-Stress"
                    elif (i==1):
                        stress_suffix = "_Stress"

                    for js in range(len(interval_datapoint)):
                        interval_datapoint[js][0] -= offset
                        interval_datapoint[js][1] += offset
                        delete_row = []
                    for j in range(interval_datapoint.shape[0]):
                        intervalLength = interval_datapoint[j][1] - interval_datapoint[j][0]
                        # print("Interval Length: ",intervalLength)

                        if ( intervalLength <384): # (1.5 s)
                            delete_row.append(j)

                    interval_datapoint = np.delete(interval_datapoint, delete_row, axis=0)
                    subSegmentName = segmentName+stress_suffix
                    # self.cut_subSegment(subSegmentName)
            else :
                extend = False

            # Add segment to patient Information ##########################################################
            self.currentPatient.add_segment(segmentName, self.segmentdata, self.segmentTimes, extend, interval_datapoint)
            self.save_segment(segmentName, self.segmentdata, self.segmentTimes)

        print("--- RUNTIME : %.2f seconds ---" % (time.time() - self.start_time))

#########################################################################################
    # def cut_subSegment(self, segmentName, segmentdata, segmentTimes):

    def save_segment(self, segmentName, segmentData, segmentTimes):
        if segmentName is None:
            return

        if self.save_folder_path is None:
            self.save_folder_path = QFileDialog.getExistingDirectory(self, "Select Output Folder")
            if not self.save_folder_path:
                print("No save folder selected.")
                return
            print("+" *20)
            print("Selected output folder TO ", self.save_folder_path)
        
        patient_segment_folder = os.path.join(self.save_folder_path,f'Patient_{self.currentPatient.subject_id}',"Segment")
        
        os.makedirs(patient_segment_folder, exist_ok=True)
        save_path = os.path.join(patient_segment_folder, f'Segment_{segmentName}.json')
        n_channels = segmentData.shape[0]

        print("+" *20)
        print("SAVE ", segmentData.shape ,segmentData ," to ", save_path)
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
            print(f"Segment saved at: {save_path}")
        except OSError as e:
            print(f"Error saving segment: {e}")

    def save_subSegment(self, subSegmentName):
        if subSegmentName is None:
            return

        
            
    def upload_folder(self):
        folder_dialog = QFileDialog()
        subjectsfolder = folder_dialog.getExistingDirectory(self, "Select Folder Containing Subject Folders")
                
        self.start_time = time.time()
        self.patient_selector.clear()

        if subjectsfolder:
            # loop through each patient
            for subject_folder in os.listdir(subjectsfolder): 
                subject_path = os.path.join(subjectsfolder, subject_folder)

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
                        print(self.excel_file_path)
                        self.trigger_data[subject_id] = pd.read_excel(fullxlsx_path, engine='openpyxl')
                    
                    self.plot_trigger(subject_id)
                    self.slice_all()


            self.edf_label.setText(f"Processed EDF files from {subjectsfolder}")
            self.excel_label.setText(f"Processed xlsx files from {subjectsfolder}")
            print("All patients processed.")

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

    def updateylimit(self):
        self.ylimit = self.plotylimit_spinbox.value()

    def updateQoffset(self):
        self.STRESS_QUADRANT_OFFSET = self.STRESS_QUADRANT_OFFSET_spinbox.value()

    def updateOverlapping(self):
        self.OVERLAPPING = self.overlapping_spinbox.value()
    
    def toggleExtend(self):
        if  not self.segmentExtend:
            self.Extend_btn.setText("Q-Extend")
            self.segmentExtend = True
            self.Extend_btn.setStyleSheet("background-color : coral") 
        else:
            self.Extend_btn.setText("Q-Intend")
            self.segmentExtend = False
            self.Extend_btn.setStyleSheet("background-color : lightblue") 
            
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