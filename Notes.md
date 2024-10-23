
# Traditional Analyze 

PREPROCESSING EEG
7 
- Filtering 50 Hz  raw.notch_filter(50) raw.filter(l_freq=1.0, h_freq=50.0)
- Downsampling
- Re-referencing
- Interpolation
- Artifact Rejection, Correction
- Remove Bad Channels

TODO
- check findminstress (no extend subsegment) not  including smaller  minstress

- evaluate each slice qeeg Metics (Separate App)
- cut definitive sliding method (no extend, defined slice width)
- reverse eeg data -> check updateplot()

# Logical Sliding
every subsegment slice into smallest stress interval 
Extend on Q1-Q4 Segment = +- 1s
Extend on Stress-NonStress SubSegment = +- 0.5s 

Slice width = Smallest Stress Length (No extend)

## Folder STRUCTURE
Segment 1 = Baseline -
    Sub-Segment = Baseline
            Slice = Baseline_0.5_25
                    = Baseline_0.5_50
                    = Baseline_1.5_25
Segment 2 = Simulation -
    Sub-Segment = Simulation
            Slice = Simulation_0.5_25
Segment 3 = Q1
    Sub-Segments = Q1 StressE n/ N-StressE m
            Slice = Q1 Stress_0.5_25
            Slice = Q1 Stress_1.5_25
            Slice = Q1 Stress_1.5_50
Segment 4 = Q2 
    Sub-Segments = Q2 StressE n/ N-StressE m
Segment 5 = Q3
    Sub-Segments = Q3 StressE n/ N-StressE m
Segment 6 = Q4
    Sub-Segments = Q4 StressE n/ N-StressE m
Segment 7 = Floss-teeth -
    Sub-Segment = Floss-teeth
Segment 8 = PostIntervention -
    Sub-Segment = PostIntervention

## SETTING BUTTON
Allow user to configure Analyze type (segment extend), subsegment parameter

SubsegmentWindow
input:
int : windowWidth (0.5 s) -> 128 datapoint (only with DL method)
int : overlapping (25) -> 25 %
output:
int : winPerSS (window number)
________________________________________________

 NumWindow = [( WindowLength - WindowWidth ) /
 ( WindowWidth * ( 1 - overlapping/100 ) ) ] + 1
     
wlength 100, winwidth 10, olap 50
           [( 100 - 10) / (10*0.5) ] + 1
            (90/5) + 1  
                = 18 + 1 = 19
________________________________________________

use that window number to slide into window,
We analyze that smallest window unit
properties
int : totalWindow
int : windowWidth


________________________________________________
# NN Analyze 
Definitive Sliding
Each subsegment, slide the window = constant define int

Folder
Segment 1 = Baseline -
    Sub-Segment = Baseline
            Windows = Baseline_0.5_25
                    = Baseline_0.5_50
                    = Baseline_1.5_25
Segment 2 = Simulation -
    Sub-Segment = Simulation
            Windows = Simulation_0.5_25
Segment 3 = Q1
    Sub-Segments = Q1 StressI n/ N-StressI m
            Windows = Q1 Stress_0.5_25
            Windows = Q1 Stress_1.5_25
            Windows = Q1 Stress_1.5_50
Segment 4 = Q2 
    Sub-Segments = Q2 StressI n/ N-StressI m
Segment 5 = Q3
    Sub-Segments = Q3 StressI n/ N-StressI m
Segment 6 = Q4
    Sub-Segments = Q4 StressI n/ N-StressI m
Segment 7 = Floss-teeth -
    Sub-Segment = Floss-teeth
Segment 8 = PostIntervention -
    Sub-Segment = PostIntervention