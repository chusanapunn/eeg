
# Traditional Analyze 

segment extend +- 1 s on Q1-Q4 /
save segment folder
subsegment extend +- 0.5 s on stress/nstress interval
save subsegment folder
every subsegment slice into smallest stress interval size slice

Extend on Q1-Q4 Segment = +- 1s
Extend on Stress-NonStress SubSegment = +- 0.5s 
Logical Sliding
Each subsegment, slide the window = smallest Stress interval

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
    Sub-Segments = Q1 StressE n/ N-StressE m
            Windows = Q1 Stress_0.5_25
            Windows = Q1 Stress_1.5_25
            Windows = Q1 Stress_1.5_50
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
int : windowWidth (0.5 s) -> 128 datapoint
int : overlapping (25) -> 25 %
output:
int : winPerSS (window number)

NumWindow = [( WindowLength - WindowWidth )      + 1
    ( WindowWidth * ( 1 - overlapping/100 ) ) ] 

            100 - 10 / (10*0.5) +1
            90/5 +1  =18+1 = 19


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