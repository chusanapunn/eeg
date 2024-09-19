import re
import mne
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import PyQt5.QtWidgets as QtWidgets
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QPushButton, QVBoxLayout, QHBoxLayout,QLabel,QWidget, QDoubleSpinBox, QTableWidget, QTableWidgetItem           
from utils import QEEGPatient, misc, segmentWindow, searchWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

########### SET DEFAULT PARAMETER ##############################################################
        
        self.FILTER_50HZ = True

        self.SAMPLING_FREQUENCY = 256 # per second
        self.QUADRANT_OFFSET = 1 # seconds
        self.STRESS_OFFSET = 0.5 # seconds
        self.OVERLAPPING = 0 # percentage
        self.segmentExtend = False # slide Q segment Extend?
        self.ylimit = 5e-4

        self.edf_file_path = None
        self.excel_file_path = None

################################################################################################
        self.raw = None
        self.trigger = None

        self.currentPatient = None
        self.patientNo = 0

        self.setWindowTitle("EEG Slicer")
        self.setGeometry(100, 100, 1200, 800)

        layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        
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
        self.overlapping_label = QLabel("Overlapping Window %:",self)
        self.overlapping_spinbox = QDoubleSpinBox(self)

        self.search_btn = QPushButton("Search Metrics", self)

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

        self.overlapping_spinbox.setRange(0, 1) 
        self.overlapping_spinbox.setSingleStep(0.05)
        self.overlapping_spinbox.setValue(0)

        self.plotylimit_spinbox.valueChanged.connect(self.updateylimit)
        self.QUADRANT_OFFSET_spinbox.valueChanged.connect(self.updateQoffset)
        self.overlapping_spinbox.valueChanged.connect(self.updateOverlapping)
        self.search_btn.clicked.connect(searchWindow.openSearchWindow)

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
        
        main_layout_components = [self.edf_upload_btn, self.edf_label, self.excel_upload_btn, self.excel_label,
                                  self.canvas, self.canvasT, self.patientInfoTable]

        button_layout_components = [self.slice_all_btn, self.baseline_btn, self.simulation_btn, self.Q1_btn, self.Q2_btn,
                    self.Q3_btn, self.Q4_btn, self.floss_btn, self.Extend_btn, self.QUADRANT_OFFSET_spinbox, 
                    self.ylimit_label, self.plotylimit_spinbox, self.overlapping_label, self.overlapping_spinbox ,
                    self.search_btn]
        
        for component in main_layout_components:
            layout.addWidget(component)

        for component in button_layout_components:
            button_layout.addWidget(component)

        layout.addLayout(button_layout)
        container.setLayout(layout)
        self.setCentralWidget(container)
         
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

        # self.patientNo += 1  # Move to next patient

# slice & plot ------------------------------------------------------------------------------------

    def plot_slice(self, interval_datapoint, segment):
        if self.raw is None or self.trigger is None:
            return
        
        fig, axs = plt.subplots(len(interval_datapoint), 1, figsize=(10, len(interval_datapoint) * 3))  
        fig.tight_layout(pad=4.0)  

        for i in range(len(interval_datapoint)):
            print("#" * 20)
            start_idx = int(interval_datapoint[i][0])
            stop_idx = int(interval_datapoint[i][1])
            if self.segmentExtend:  # Slide Extend OFFSET
                offset = self.QUADRANT_OFFSET * self.SAMPLING_FREQUENCY
                start_idx -= offset
                stop_idx += offset
                print("Quadrant Offset:", self.QUADRANT_OFFSET, "Offset Sample:", offset,
                    "## Length +", 2 * self.QUADRANT_OFFSET, "Seconds")

            self.sliced_data, self.sliced_times = self.raw[:, start_idx:stop_idx]
            self.sliced_datapoint = (self.sliced_times - self.sliced_times[0]) * self.SAMPLING_FREQUENCY

            # Add segment to patient Information

            self.currentPatient.add_segment(segment, self.sliced_data, self.segmentExtend, interval_datapoint, self.OVERLAPPING)
            ax = axs[i] if len(interval_datapoint) > 1 else axs  # If only one plot, axs is not an array
            
            ax.plot(self.sliced_datapoint, self.sliced_data.T)
            ax.set_title(f'Slice {i+1} {segment}')
            ax.set_xlabel('Time (datapoint)')
            ax.set_ylabel('Value')

            # Set limits
            xxlimit = misc.roundup_datapoint(self.sliced_datapoint.shape[0])
            ax.set_xlim(xmax=xxlimit)
            ax.set_ylim(ymin=-self.ylimit, ymax=self.ylimit)

        plt.show()
    
    def slice_each(self, segment, activate):
        if self.raw is None or self.trigger is None:
            return
        
        if segment in ['Q1','Q2','Q3','Q4']:
            for i in range(2):  # 0 non stress,   # 1 :stress interval
                idx = np.where( (self.trigger[segment]==activate) & (self.trigger['Stress']==i))[0] 
                interval = misc.group_number_slices(idx)
                interval_datapoint = misc.convert_timescale(interval, self.SAMPLING_FREQUENCY)
                start_idx = int(interval_datapoint[i][0])
                stop_idx = int(interval_datapoint[i][1])
                if i==1: # Stress -> Offset
                    offset = self.STRESS_OFFSET * self.SAMPLING_FREQUENCY
                    start_idx -= offset
                    stop_idx += offset
                    stress_suffix = "_Stress"
                    print("Stress Offset:", self.STRESS_OFFSET, "Offset Sample:", offset,
                        "## Length +", 2 * self.STRESS_OFFSET, "Seconds")
                else : 
                    stress_suffix = "_Non-Stress"
                seg_name = segment+stress_suffix

                self.plot_slice(interval_datapoint, seg_name)
            # self.slice_each("Stress",1)
        else :
            idx = np.where(self.trigger[segment]==activate)[0] # Q1 == p
            interval = misc.group_number_slices(idx)
            interval_datapoint = misc.convert_timescale(interval, self.SAMPLING_FREQUENCY)
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

# EDF ------------------------------------------------------------------------
            
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

        self.raw = mne.io.read_raw_edf(self.edf_file_path, preload=True)
        self.SAMPLING_FREQUENCY   = self.raw.info['sfreq']
        
        if self.FILTER_50HZ:
            self.raw = self.raw.notch_filter(freqs=50)
# FULL LENGTH
        data, times = self.raw[:, :]
        times = times*self.SAMPLING_FREQUENCY
        # edf_length_second = times.shape[0]/256
        # edf_length_minute=np.round(edf_length_second/60,2)
        ch_names = [ch_name[4:] for ch_name in self.raw.ch_names]
        subject_id = re.search(r'Subject(\d+)', self.edf_file_path)
# Patient Class Information record ########################################################
        self.currentPatient = QEEGPatient.QEEGPatient(
            subject_id.group(1),
            data,
            ch_names,
            )
# #########################################################################################
        self.add_patientInfoTable(self.currentPatient)
        
        # print("#"*20)
        # print("Patient : ", self.currentPatient.subject_id)
        # print("Raw data: ", self.currentPatient.full_raw)
        # print("Channel List:", self.currentPatient.ch_list)
        # print("EDF Data",   data.shape)
        
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

    # EXCEL ------------------------------------------------------------------------------------

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

        self.plot_trigger()

    def plot_trigger(self):
        if not self.excel_file_path:
            return
        
        for i in ['Baseline','Simulate_teeth_scraping','Floss_teeth']:
            self.trigger[i] = pd.to_numeric(self.trigger[i], errors='coerce')
        
        self.trigger['Sample'] = self.trigger['Time'].apply(lambda x: misc.convert_datetime_sample(x, self.SAMPLING_FREQUENCY))
        self.trigger['Q1N'] = self.trigger["Q1"].apply(lambda x: misc.convertQtoInt(x,"p"))
        self.trigger['Q2N'] = self.trigger["Q2"].apply(lambda x: misc.convertQtoInt(x,"q"))
        self.trigger['Q3N'] = self.trigger["Q3"].apply(lambda x: misc.convertQtoInt(x,"r"))
        self.trigger['Q4N'] = self.trigger["Q4"].apply(lambda x: misc.convertQtoInt(x,"s"))
        
        self.canvasT.figure.clear()
        ax2 = self.canvasT.figure.add_subplot(111)
        ax2.plot( self.trigger['Sample'], self.trigger['Baseline'],color="black",label="Baseline")
        ax2.plot( self.trigger['Sample'], self.trigger['Simulate_teeth_scraping'],color="blue",label="Simulation")
        ax2.plot( self.trigger['Sample'], self.trigger['Q1N'],color="coral",label="Q1")
        ax2.plot( self.trigger['Sample'], self.trigger['Q2N'],color="tomato",label="Q2")
        ax2.plot( self.trigger['Sample'], self.trigger['Q3N'],color="red",label="Q3")
        ax2.plot( self.trigger['Sample'], self.trigger['Q4N'],color="darkred",label="Q4")
        ax2.plot( self.trigger['Sample'], self.trigger['Floss_teeth'],color="olive",label="Floss_teeth")
        ax2.plot( self.trigger['Sample'], self.trigger['Stress'],color="goldenrod",label="Stress")
        ax2.fill_between( self.trigger['Sample'],  self.trigger['Stress'],color="goldenrod", alpha=0.3)

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
        self.QUADRANT_OFFSET = self.QUADRANT_OFFSET_spinbox.value()

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
