import re
import mne
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import datetime
import PyQt5.QtWidgets as QtWidgets
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QPushButton, QVBoxLayout, QHBoxLayout,QLabel,QWidget, QDoubleSpinBox, QLineEdit, QTableWidget, QTableWidgetItem           
from scipy.fft import fft
from utils.QEEGPatient import QEEGPatient

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.edf_file_path = None
        self.excel_file_path = None
        self.raw = None
        self.trigger = None

        self.currentPatient = None
        self.patientNo = 0

        self.SAMPLING_FREQUENCY = 256 # per second
        self.QUADRANT_OFFSET = 1 # seconds
        self.STRESS_OFFSET = 0.5 # seconds
        self.segmentExtend = False # slide Q segment Extend?
        self.ylimit = 5e-4

        self.setWindowTitle("EEG Slicer")
        self.setGeometry(100, 100, 1200, 800)


        layout = QVBoxLayout()
        pp_layout = QHBoxLayout()
        
        self.edf_upload_btn = QPushButton("Upload EDF File", self)
        self.excel_upload_btn = QPushButton("Upload Excel File", self)
        self.baseline_btn = QPushButton("Baseline", self)
        self.simulation_btn = QPushButton("Simulation", self)
        self.slice_all_btn = QPushButton("Slice All",self)
        self.Q1_btn = QPushButton("Quadrant1", self)
        self.Q2_btn = QPushButton("Quadrant2", self)
        self.Q3_btn = QPushButton("Quadrant3", self)
        self.Q4_btn = QPushButton("Quadrant4", self)
        self.floss_btn = QPushButton("Floss", self)

        self.Extend_btn = QPushButton("Q-Intend", self)
        self.QUADRANT_OFFSET_spinbox = QDoubleSpinBox(self)
        self.ylimit_label = QLabel("Ylimit",self)
        self.plotylimit_spinbox = QDoubleSpinBox(self)
        self.ch_interval_input = QLineEdit(self)
        self.ch_input_label = QLabel("Enter Intervals:",self)
        # self.stress_btn = QPushButton("Stress", self)

        self.edf_label = QLabel("No EDF file uploaded", self)
        self.excel_label = QLabel("No Excel file uploaded", self)

        self.canvas = FigureCanvas(plt.Figure())
        self.canvasT = FigureCanvas(plt.Figure())

        self.patientInfoTable = QTableWidget(1,8)
        self.patientInfoTable.setHorizontalHeaderLabels(
            ["Subject ID", "Raw EEG", "Length (Datapoint)", "Length (Second)", "Length (Minute)", "CH_list","CH_num","Segments"]
            )
        
        header = self.patientInfoTable.horizontalHeader()  
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)       
        header.setSectionResizeMode(7, QtWidgets.QHeaderView.Stretch)
        
        container = QWidget()

        self.Extend_btn.setStyleSheet("background-color : lightblue") 
        self.QUADRANT_OFFSET_spinbox.setRange(0.5, 10.0)  
        self.QUADRANT_OFFSET_spinbox.setSingleStep(0.5)
        self.QUADRANT_OFFSET_spinbox.setValue(1.0)
        self.plotylimit_spinbox.setRange(0.00005, 0.005) 
        self.plotylimit_spinbox.setSingleStep(0.00005)
        self.plotylimit_spinbox.setDecimals(5)
        self.plotylimit_spinbox.setValue(0.0005)

        self.plotylimit_spinbox.valueChanged.connect(self.updateylimit)
        self.QUADRANT_OFFSET_spinbox.valueChanged.connect(self.updateQoffset)
        self.edf_upload_btn.clicked.connect(self.upload_edf_file)
        self.excel_upload_btn.clicked.connect(self.upload_excel_file)
        
        self.slice_all_btn.clicked.connect(self.slice_all)
        self.baseline_btn.clicked.connect(lambda : self.slice_each("Baseline",1))
        self.simulation_btn.clicked.connect(lambda : self.slice_each("Simulate_teeth_scraping",1))
        self.Q1_btn.clicked.connect(lambda : self.slice_each("Q1","p"))
        self.Q2_btn.clicked.connect(lambda : self.slice_each("Q2","q"))
        self.Q3_btn.clicked.connect(lambda : self.slice_each("Q3","r"))
        self.Q4_btn.clicked.connect(lambda : self.slice_each("Q4","s"))
        self.Extend_btn.clicked.connect(self.toggleExtend)
        self.floss_btn.clicked.connect(lambda : self.slice_each("Floss_teeth",1))
        # self.stress_btn.clicked.connect(lambda : self.slice_each("Stress",1))
        
        layout.addWidget(self.edf_upload_btn)
        layout.addWidget(self.edf_label)
        layout.addWidget(self.excel_upload_btn)
        layout.addWidget(self.excel_label)
        layout.addLayout(pp_layout)

        components = [self.slice_all_btn, self.baseline_btn,
                     self.simulation_btn, self.Q1_btn, self.Q2_btn,
                     self.Q3_btn, self.Q4_btn, self.floss_btn, self.Extend_btn,
                     self.QUADRANT_OFFSET_spinbox, self.ylimit_label,
                     self.plotylimit_spinbox, self.ch_input_label, self.ch_interval_input]
        
        for component in components:
            pp_layout.addWidget(component)

        layout.addWidget(self.canvas)
        layout.addWidget(self.canvasT)
        layout.addWidget(self.patientInfoTable)

        container.setLayout(layout)
        self.setCentralWidget(container)

    # def parse_intervals(self, interval_text):
    #     intervals = []
    #     for part in interval_text.split(','):
    #         if ':' in part:
    #             start, end = part.split(':')
    #             intervals.append((int(start), int(end)))
    #         else:
    #             index = int(part)
    #             intervals.append((index, index))
    #     return intervals
         
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
        segment_btn.clicked.connect(lambda: self.showSegmentTable(patient.segments))
        self.patientInfoTable.setCellWidget(self.patientNo, 7, segment_btn)

        # self.patientNo += 1  # Move to next patient
        
    def plot_slice(self, interval, segment):
        if self.raw is None or self.trigger is None:
            return
        
        fig, axs = plt.subplots(len(interval), 1, figsize=(10, len(interval) * 3))  
        fig.tight_layout(pad=4.0)  

        for i in range(len(interval)):
            print("#" * 20)
            
            if self.segmentExtend:  # Slide Extend
                offset = self.QUADRANT_OFFSET * self.SAMPLING_FREQUENCY
                interval[i][0] -= offset
                interval[i][1] += offset
                print("Quadrant Offset:", self.QUADRANT_OFFSET, "Offset Sample:", offset,
                    "## Length +", 2 * self.QUADRANT_OFFSET, "Seconds")

            self.sliced_data, self.sliced_times = self.raw[:, interval[i][0]:interval[i][1]]
            self.sliced_datapoint = (self.sliced_times - self.sliced_times[0]) * self.SAMPLING_FREQUENCY

            # Add segment to patient Information

            self.currentPatient.add_segment(segment, self.sliced_data, self.segmentExtend, interval)
            self.showSegmentTable(self.currentPatient.segments)

            ax = axs[i] if len(interval) > 1 else axs  # If only one plot, axs is not an array
            
            ax.plot(self.sliced_datapoint, self.sliced_data.T)
            ax.set_title(f'Slice {i+1} {segment}')
            ax.set_xlabel('Time (datapoint)')
            ax.set_ylabel('Value')

            # Set limits
            xxlimit = self.roundup_datapoint(self.sliced_datapoint.shape[0])
            ax.set_xlim(xmax=xxlimit)
            ax.set_ylim(ymin=-self.ylimit, ymax=self.ylimit)

        plt.show()
        # for i in range(len(interval)): # -----------------------------------
                
        #     print("#"*20)
        #     if self.segmentExtend:    # slide Extend
                
        #         offset=self.QUADRANT_OFFSET*self.SAMPLING_FREQUENCY

        #         interval[i][0]-=offset
        #         interval[i][1]+=offset
        #         print("Quadrant Offset : ", self.QUADRANT_OFFSET,"Offset Sample : ",
        #               offset, "## Length + ",2*self.QUADRANT_OFFSET,"Second")

        #     self.sliced_data, self.sliced_times = self.raw[:,interval[i][0]:interval[i][1]]
        #     self.sliced_datapoint= ((self.sliced_times- self.sliced_times[0])*self.SAMPLING_FREQUENCY)
            
        #     # Add segment to patient Information
        #     self.currentPatient.add_segment(segment, self.sliced_data, self.segmentExtend) 
        #     self.showSegmentTable(self.currentPatient.segments)

        #     # print("Slice data Shape",self.sliced_data.shape,self.sliced_times.shape)
        #     # print("Interval",interval[i])
        #     plt.figure()
        #     plt.plot(self.sliced_datapoint, self.sliced_data.T)
        #     plt.title(f'Slice {i+1} {segment}')
        #     plt.xlabel('Time (datapoint)')
        #     plt.ylabel('Value') # ---------------------------------------------

            # xxlimit = self.roundup_datapoint(self.sliced_datapoint.shape[0])
            
            # plt.xlim(xmax = xxlimit)
            # plt.ylim(ymin=-self.ylimit,ymax = self.ylimit)
            # plt.show()

    def showSegmentTable(self, patientsegments):

        layout = QVBoxLayout()
        self.segmentWindow = QWidget()
        self.segmentTable = QTableWidget(len(patientsegments), 12)
        segmenttable_col = ["Segment Name", "Segment Data (microV)", "Is Extend", "Absolute Power", "Relative Power",
             "Amplitude Asymmetry","Phase Lag", "Coherence", "Band Ratios","Interval list", "Interval count",'Expand Row']
        
        seg_col_key = ['segment_data', 'is_extend', 'absolute_power','relative_power','amplitude_asymmetry',
                'phase_lag', 'coherence', 'band_ratios', 'interval_list', 'interval_count']
        
        self.segmentWindow.setWindowTitle("Patient Segment Table")
        self.segmentWindow.setGeometry(100, 100, 1600, 900)
        self.segmentTable.setHorizontalHeaderLabels( segmenttable_col )
        layout.addWidget(self.segmentTable)
        self.segmentWindow.setLayout(layout)
        self.segmentWindow.show()

        self.show_btn = {}
        self.row_map = {}

        # print("Patient Segment", patientsegments)
        for seg_id,seg_name in enumerate(patientsegments):
            # print("Patient Segment :", seg_name,' ID :',seg_id)
            patientsegment = patientsegments[seg_name]
            self.segmentTable.setItem(
                seg_id, 0, QTableWidgetItem( str(seg_name)))
            for key_id, key in enumerate(seg_col_key):
                self.segmentTable.setItem(
                    seg_id, key_id+1, QTableWidgetItem( str(patientsegment.get(key))  ))

            # self.segmentTable.setItem(
            #     seg_id, 0, QTableWidgetItem( str(seg_name)))
            # self.segmentTable.setItem(
            #     seg_id, 1, QTableWidgetItem( str(patientsegment.get("is_extend"))))
            # self.segmentTable.setItem(
            #     seg_id, 2, QTableWidgetItem( str(patientsegment.get("segment_data"))))
            # self.segmentTable.setItem(
            #     seg_id, 3, QTableWidgetItem( str(patientsegment.get("absolute_power"))))
            # self.segmentTable.setItem(
            #     seg_id, 4, QTableWidgetItem( str(patientsegment.get("relative_power"))))
            # self.segmentTable.setItem(
            #     seg_id, 5, QTableWidgetItem( str(patientsegment.get("amplitude_asymmetry"))))
            # self.segmentTable.setItem(
            #     seg_id, 6, QTableWidgetItem( str(patientsegment.get("phase_lag"))))
            # self.segmentTable.setItem(
            #     seg_id, 7, QTableWidgetItem( str(patientsegment.get("coherence"))))
            # self.segmentTable.setItem(
            #     seg_id, 8, QTableWidgetItem( str(patientsegment.get("band_ratios"))))
            # self.segmentTable.setItem(
            #     seg_id, 9, QTableWidgetItem( str(patientsegment.get("interval_list"))))
            # self.segmentTable.setItem(
            #     seg_id, 10, QTableWidgetItem( str(patientsegment.get("interval_count"))))
            
            
            show_btn = QPushButton("Expand")
            # show_btn.clicked.connect(lambda : self.toggleHiddenRow(patientsegment, seg_id))
            show_btn.clicked.connect(lambda checked, seg_id=seg_id: self.toggleHiddenRow(patientsegment, seg_id))

            self.show_btn[seg_id] = show_btn
            self.segmentTable.setCellWidget(seg_id, 11, show_btn)
            
            self.row_map[seg_id] = []

            for ch_data in patientsegment.get('segment_data'):  # loop channel(subrow) of every column
                sub_row = self.segmentTable.rowCount() + (seg_id)  # 
                self.segmentTable.insertRow(sub_row)

                self.segmentTable.setItem(sub_row, 1, QTableWidgetItem(str(ch_data)))
                # self.segmentTable.setItem(sub_row, 1, QTableWidgetItem(str(patientsegment[seg_col_key[0]].get(ch_data)))) # segment data
                self.segmentTable.setItem(sub_row, 2, QTableWidgetItem(str(patientsegment[seg_col_key[1]]))) # is extend
                self.segmentTable.setItem(sub_row, 3, QTableWidgetItem(str(patientsegment[seg_col_key[2]].get(ch_data)))) # absoqlute power
                self.segmentTable.setItem(sub_row, 4, QTableWidgetItem(str(patientsegment[seg_col_key[3]].get(ch_data)))) # relative power  
                self.segmentTable.setItem(sub_row, 5, QTableWidgetItem(str(patientsegment[seg_col_key[4]].get(ch_data)))) # amplitude asymmetry
                # self.segmentTable.setItem(sub_row, 6, QTableWidgetItem(str(patientsegment[seg_col_key[5]].get(ch_data)))) # phase_lag
                # self.segmentTable.setItem(sub_row, 7, QTableWidgetItem(str(patientsegment[seg_col_key[6]].get(ch_data)))) # coherence
                self.segmentTable.setItem(sub_row, 8, QTableWidgetItem(str(patientsegment[seg_col_key[7]].get(ch_data)))) # band_ratios
                self.segmentTable.setItem(sub_row, 9, QTableWidgetItem(str(patientsegment[seg_col_key[8]]))) # interval_list
                self.segmentTable.setItem(sub_row, 10, QTableWidgetItem(str(patientsegment[seg_col_key[9]]))) # interval_count

                self.row_map[seg_id].append(sub_row)
                self.segmentTable.setRowHidden(sub_row, True)

    def toggleHiddenRow(self, patientsegment, seg_id):

        hideCh = patientsegment.get("hideCh") 
        patientsegment['hideCh'] = not hideCh
        
        for sub_row in self.row_map[seg_id]:
            self.segmentTable.setRowHidden(sub_row, not hideCh)
        
        # for sub_row in self.row_map[seg_id]:
        #     self.segmentTable.setRowHidden(sub_row, hideCh)
            
        # ch = len(patientsegment['segment_data'])

        # for sub_row in range(ch):
        #     print("Segment ",seg_id)
        #     print("Hide/Show Row ",sub_row+1+(seg_id*ch))
        #     self.segmentTable.setRowHidden(sub_row+1+(seg_id*ch), patientsegment.get("hideCh"))  
                

    def updateylimit(self):
        self.ylimit = self.plotylimit_spinbox.value()

    def updateQoffset(self):
        self.QUADRANT_OFFSET = self.QUADRANT_OFFSET_spinbox.value()
    
    def toggleExtend(self):
        if  not self.segmentExtend:
            self.Extend_btn.setText("Q-Extend")
            self.segmentExtend = True
            self.Extend_btn.setStyleSheet("background-color : coral") 
        else:
            self.Extend_btn.setText("Q-Intend")
            self.segmentExtend = False
            self.Extend_btn.setStyleSheet("background-color : lightblue") 
    
    def slice_each(self, segment, activate):
        if self.raw is None or self.trigger is None:
            return
        
        if segment in ['Q1','Q2','Q3','Q4']:
            for i in range(2):  # 0 non stress,   # 1 :stress interval
                idx = np.where( (self.trigger[segment]==activate) & (self.trigger['Stress']==i))[0] 
                interval = self.group_number_slices(idx)
                interval_datapoint = self.convert_timescale(interval)
                stress_suffix = "_Non-Stress" if i==0 else "_Stress"
                seg_name = segment+stress_suffix

                self.plot_slice(interval_datapoint, seg_name)
            # self.slice_each("Stress",1)
        else :
            idx = np.where(self.trigger[segment]==activate)[0] # Q1 == p
            interval = self.group_number_slices(idx)
            interval_datapoint = self.convert_timescale(interval)
            self.plot_slice(interval_datapoint, segment)

    def slice_all(self):
        if self.raw is None or self.trigger is None:
            return
        
        self.slice_each("Baseline",1)
        self.slice_each("Simulate_teeth_scraping",1)

        self.slice_each("Q1","p")   
        self.slice_each("Q2","q")
        self.slice_each("Q3","r")
        self.slice_each("Q4","s")

        self.slice_each("Floss_teeth",1)

    def convert_timescale(self,interval):
        # Modify : Trigger to time scale
        second = np.multiply(interval,.5) # In Second
        # length = second[0][1]-second[0][0]
        interval_datapoint = np.multiply(second,self.SAMPLING_FREQUENCY) # Raw fs

        # print("### ", segment," IsExtend?", self.segmentExtend)
        # print("Trigger Interval:", interval)
        # print("Time (second)   :", second,"## Length :", length, " second")
        # print("Raw Datapoint   :", interval_datapoint)
        return interval_datapoint


    # EDF
            
    def upload_edf_file(self):
        file_dialog = QFileDialog()
        edf_file, _ = file_dialog.getOpenFileName(self, "Select EDF File", "", "EDF Files (*.edf)")
        
        if edf_file: # and it's new patient-> add new subject ID _> add new row to table
            self.edf_file_path = edf_file
            self.edf_label.setText(f"EDF File: {edf_file}")
            self.plot_edf_data()

    def plot_edf_data(self):
        if not self.edf_file_path:
            return

        self.raw = mne.io.read_raw_edf(self.edf_file_path)
        self.SAMPLING_FREQUENCY   = self.raw.info['sfreq']

        # FULL LENGTH
        data, times = self.raw[:, :]
        times = times*self.SAMPLING_FREQUENCY
        # edf_length_second = times.shape[0]/256
        # edf_length_minute=np.round(edf_length_second/60,2)

        # Patient Class Information record
        subject_id = re.search(r'Subject(\d+)', self.edf_file_path)
        self.currentPatient = QEEGPatient(
            subject_id.group(1),
            data,
            self.raw.ch_names,
            )
        #----------------------------------
        self.add_patientInfoTable(self.currentPatient)
        
        # print("#"*20)
        # print("Patient : ", self.currentPatient.subject_id)
        # print("Raw data: ", self.currentPatient.full_raw)
        # print("Channel List:", self.currentPatient.ch_list)
        # print("EDF Data",   data.shape)
        
        self.canvas.figure.clear()
        ax = self.canvas.figure.add_subplot(111)
        # use time as sample
        ax.plot(times, data.T)
        ax.set_title('Raw EDF Data')
        ax.set_xlabel('Time (datapoint)')
        ax.set_ylabel('Value')

        xlimit = self.roundup_datapoint(times.shape[0])
        ax.set_xlim(xmax = xlimit)

        self.canvas.draw()

    # EXCEL

    def upload_excel_file(self):
        file_dialog = QFileDialog()
        excel_file, _ = file_dialog.getOpenFileName(self, "Select Excel File", "", "Excel Files (*.xlsx *.xls)")
        
        if excel_file:
            self.excel_file_path = excel_file
            self.excel_label.setText(f"Excel File: {excel_file}")
            self.read_excel_data()

    def read_excel_data(self):
        if not self.excel_file_path:
            return

        self.trigger = pd.read_excel(self.excel_file_path)
        # trigger_length_second = self.trigger.shape[0]/2
        # trigger_length_minute = np.round(trigger_length_second/60,2)

        # print("#"*20)
        # print("Trigger", self.trigger.head())
        # print("Trigger Times", trigger_length_second,"Second",trigger_length_minute,"Minutes") # 0.5 s per datapoint;2 data =1 s

        self.plot_excel_data()

    def plot_excel_data(self):
        if not self.excel_file_path:
            return
        
        for i in ['Baseline','Simulate_teeth_scraping','Floss_teeth']:
            self.trigger[i] = pd.to_numeric(self.trigger[i], errors='coerce')
        
        self.trigger['Sample'] = self.trigger['Time'].apply(lambda x: self.convert_datetime_sample(x))
        self.trigger['Q1N'] = self.trigger["Q1"].apply(lambda x: self.convertQtoInt(x,"p"))
        self.trigger['Q2N'] = self.trigger["Q2"].apply(lambda x: self.convertQtoInt(x,"q"))
        self.trigger['Q3N'] = self.trigger["Q3"].apply(lambda x: self.convertQtoInt(x,"r"))
        self.trigger['Q4N'] = self.trigger["Q4"].apply(lambda x: self.convertQtoInt(x,"s"))
        
        self.canvasT.figure.clear()
        ax2 = self.canvasT.figure.add_subplot(111)
        ax2.plot(self.trigger['Sample'],self.trigger['Baseline'],color="black",label="Baseline")
        ax2.plot(self.trigger['Sample'],self.trigger['Simulate_teeth_scraping'],color="blue",label="Simulation")
        ax2.plot(self.trigger['Sample'],self.trigger['Q1N'],color="mistyrose",label="Q1")
        ax2.plot(self.trigger['Sample'],self.trigger['Q2N'],color="tomato",label="Q2")
        ax2.plot(self.trigger['Sample'],self.trigger['Q3N'],color="red",label="Q3")
        ax2.plot(self.trigger['Sample'],self.trigger['Q4N'],color="darkred",label="Q4")
        ax2.plot(self.trigger['Sample'],self.trigger['Floss_teeth'],color="olive",label="Floss_teeth")
        ax2.set_title('Trigger')
        ax2.set_xlabel('Time (datapoint)')
        ax2.set_ylabel('Value')
        ax2.legend()
        # seconds * sampling rate = datapoint
        xxlimit = self.roundup_datapoint((self.trigger['Sample'].shape[0]*self.SAMPLING_FREQUENCY)/2) # 2 datapoint = 1 second
        ax2.set_xlim(xmax = xxlimit)

        self.canvasT.draw()

    def convert_datetime_sample(self, time_value):
        if isinstance(time_value, datetime.datetime) or isinstance(time_value, datetime.time) :
            h, m, s, ms = time_value.strftime("%H:%M:%S:%f").split(":")
            return(int( ( (int(h)*3600) + (int(m)*60) + int(s)+ (float(ms[:-5])/10))* self.SAMPLING_FREQUENCY ))
        else:
            return None
        
    def convertQtoInt(self, time_value, code):
        if (time_value==code):
            return 1
        
    def roundup_datapoint(self, num): # (digit - 1) (1230 -> 1300) (4->3)
        digit = int(math.floor(math.log10(num))) # 3
        rounding_factor = 10 ** digit  # 1000
        rounded_num = math.ceil(num / rounding_factor) * rounding_factor # divide, round up then multiply back
        # print("Round num ", num)
        # print("Di ", digit)
        # print("rn ", rounded_num)
        
        return rounded_num

    def group_number_slices(self,arr):
        # Grouping number slice
        slice_baseline = []
        start = arr[0]  # always the first index
        stop = arr[0]
        # print("start",start)
        # print('stop',stop)
        for i in range(1,len(arr)):
            # print(arr[i],arr[i-1])
            if (arr[i]==arr[i-1]+1): # continuous
                stop = arr[i]                 # shift stopping point
            else:                                      # breaking point
                slice_baseline.append([start,stop])    # append slice
                start = arr[i]                # move starting point
                if i == len(arr)-1:           # enough index point?
                    # stop = arr[i+1]
                    slice_baseline.append([start,stop])    # append last slice
                stop = arr[i]
        slice_baseline.append((start,stop))
        return slice_baseline