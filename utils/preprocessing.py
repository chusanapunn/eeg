import mne
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import datetime
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QPushButton, QVBoxLayout, QHBoxLayout,QLabel,QWidget, QDoubleSpinBox              
from scipy.fft import fft

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.edf_file_path = None
        self.excel_file_path = None
        self.raw = None
        self.trigger = None

        self.SAMPLING_FREQUENCY= 256 # per second
        self.QUADRANT_OFFSET = 1 # seconds
        self.STRESS_OFFSET = 0.5 # seconds
        self.slideQ_external = False # slide Q segment External?
        self.ylimit = 5e-4

        self.setWindowTitle("File Upload and Plot Interface")
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

        self.External_btn = QPushButton("Q-Internal", self)
        self.QUADRANT_OFFSET_spinbox = QDoubleSpinBox(self)
        self.ylimit_label = QLabel("Ylimit",self)
        self.plotylimit_spinbox = QDoubleSpinBox(self)

        # self.stress_btn = QPushButton("Stress", self)

        self.edf_label = QLabel("No EDF file uploaded", self)
        self.excel_label = QLabel("No Excel file uploaded", self)

        self.canvas = FigureCanvas(plt.Figure())
        self.canvasT = FigureCanvas(plt.Figure())

        container = QWidget()

        self.External_btn.setStyleSheet("background-color : lightblue") 
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
        self.External_btn.clicked.connect(self.toggleExternal)
        self.floss_btn.clicked.connect(lambda : self.slice_each("Floss_teeth",1))
        # self.stress_btn.clicked.connect(lambda : self.slice_each("Stress",1))
        
        layout.addWidget(self.edf_upload_btn)
        layout.addWidget(self.edf_label)
        layout.addWidget(self.excel_upload_btn)
        layout.addWidget(self.excel_label)
        layout.addLayout(pp_layout)

        pp_layout.addWidget(self.slice_all_btn)
        pp_layout.addWidget(self.baseline_btn)
        pp_layout.addWidget(self.simulation_btn)
        pp_layout.addWidget(self.Q1_btn)
        pp_layout.addWidget(self.Q2_btn)
        pp_layout.addWidget(self.Q3_btn)
        pp_layout.addWidget(self.Q4_btn)
        pp_layout.addWidget(self.floss_btn)
        pp_layout.addWidget(self.External_btn)
        pp_layout.addWidget(self.QUADRANT_OFFSET_spinbox)
        pp_layout.addWidget(self.ylimit_label)
        pp_layout.addWidget(self.plotylimit_spinbox)

        layout.addWidget(self.canvas)
        layout.addWidget(self.canvasT)

        container.setLayout(layout)
        self.setCentralWidget(container)
    
    def updateylimit(self):
        self.ylimit = self.plotylimit_spinbox.value()

    def updateQoffset(self):
        self.QUADRANT_OFFSET = self.QUADRANT_OFFSET_spinbox.value()
    
    def toggleExternal(self):
        if  not self.slideQ_external:
            self.External_btn.setText("Q-External")
            self.slideQ_external = True
            self.External_btn.setStyleSheet("background-color : coral") 
        else:
            self.External_btn.setText("Q-Internal")
            self.slideQ_external = False
            self.External_btn.setStyleSheet("background-color : lightblue") 
    
    # EDF
            
    def upload_edf_file(self):
        file_dialog = QFileDialog()
        edf_file, _ = file_dialog.getOpenFileName(self, "Select EDF File", "", "EDF Files (*.edf)")
        
        if edf_file:
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
        
        print("#"*20)
        print("EDF Data",data.shape)
        print("EDF Times",times.shape[0]/256) # 256 fs
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
        print("#"*20)
        print("Trigger", self.trigger.head())
        print("Trigger Times", self.trigger.shape[0]/2) # 0.5 s per datapoint;2 data =1 s

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

    def slice_each(self,segment,activate):
        if self.raw is None or self.trigger is None:
            return
        
        idx = np.where(self.trigger[segment]==activate)[0]
        interval = self.group_number_slices(idx)
        
        # Modify interval time scale
        second = np.multiply(interval,.5) # In Second
        rawdatapoint = np.multiply(second,self.SAMPLING_FREQUENCY) # Raw fs
        print("### ", segment," IsExternal?", self.slideQ_external)
        print("Trigger Interval:",interval)
        print("Time (second)   :",second)
        print("Raw Datapoint   :",rawdatapoint)
        
        self.plot_slice(rawdatapoint,segment)

    def plot_slice(self,interval,name):
        if self.raw is None or self.trigger is None:
            return
        
        for i in range(len(interval)):

            # slide external        
            if self.slideQ_external:
                offset=self.QUADRANT_OFFSET*self.SAMPLING_FREQUENCY
                interval[i][0]-=offset
                interval[i][1]+=offset
                print("Quadrant Offset : ", self.QUADRANT_OFFSET,"Offset Sample : ",offset)
            
            self.sliced_data, self.sliced_times = self.raw[:,interval[i][0]:interval[i][1]]
            self.sliced_datapoint= ((self.sliced_times- self.sliced_times[0])*self.SAMPLING_FREQUENCY)
            print("Slice data Shape",self.sliced_data.shape,self.sliced_times.shape)
            print("Interval",interval[i])
            plt.figure()
            plt.plot(self.sliced_datapoint, self.sliced_data.T)
            plt.title(f'Slice {i+1} {name}')
            plt.xlabel('Time (datapoint)')
            plt.ylabel('Value')

            xxlimit = self.roundup_datapoint(self.sliced_datapoint.shape[0])
            
            plt.xlim(xmax = xxlimit)
            plt.ylim(ymin=-self.ylimit,ymax = self.ylimit)
            plt.show()