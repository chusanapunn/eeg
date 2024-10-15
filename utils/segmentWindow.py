from PyQt5.QtWidgets import  QPushButton, QVBoxLayout ,QWidget, QTableWidget, QTableWidgetItem   

segmentWindow = None
compareWindows = {}
segmentWindows= {}
segmentTable = None

# SEGMENT & METRICS COMPARE WINDOW ######################################
def showSegmentTable(patientsegments, subject_id):
    global segmentWindow, segmentWindows

    if subject_id in segmentWindows:
        segmentWindows[subject_id].close()
        del segmentWindows[subject_id]

    layout = QVBoxLayout()
    segmentWindow = QWidget()
    
    segmenttable_col = [ "Segment Name", "Segment Data (microV)", "Is Extend", "Absolute Power", "Relative Power",
            "Band Ratios","Amplitude Asymmetry","Phase Lag", "Coherence", "Interval list", "Interval count", "Interval length (Second)" ,'Expand Info']
    
    seg_col_key = ['segment_data', 'is_extend', 'absolute_power','relative_power','band_ratios',
            'amplitude_asymmetry', 'phase_lag', 'coherence',  'interval_list', 'interval_count', 'interval_length']
    
    col_length = len(segmenttable_col)
    segmentTable = QTableWidget(len(patientsegments), col_length)
    segmentTable.setHorizontalHeaderLabels( segmenttable_col )

    segmentWindow.setWindowTitle(f"Subject: {subject_id} Segments Table")
    segmentWindow.setGeometry(100, 100, 1400, len(patientsegments)*56)

    
    layout.addWidget(segmentTable)
    segmentWindow.setLayout(layout)
    segmentWindow.show()

    segmentWindows[subject_id] = segmentWindow 


    # SEGMENT ROW
    for seg_id, seg_name in enumerate(patientsegments):
        # print("Patient Segment :", seg_name,' ID :',seg_id)
        patientsegment = patientsegments[seg_name]
        segmentTable.setItem(
            seg_id, 0, QTableWidgetItem( str(seg_name)))
        
        # SEGMENT COLUMN
        for key_id, key in enumerate(seg_col_key):
            segmentTable.setItem(
                seg_id, key_id+1, QTableWidgetItem( str(patientsegment.get(key))  ))

        ExpandInfo_btn = QPushButton("Expand Info")
        ExpandInfo_btn.clicked.connect(lambda checked, seg_name=seg_name: expandInfoWindow(patientsegments, seg_name))
        segmentTable.setCellWidget(seg_id, col_length-1, ExpandInfo_btn)


        # current_row = 0
        # CHANNEL SUBROW ##################################################
        # for ch_id, ch_data in enumerate(patientsegment.get('segment_data', [])):  # loop channel(subrow) of every column
        #     current_row += 1  
        #     segmentTable.insertRow(current_row)

        #     segmentTable.setItem(current_row, 1, QTableWidgetItem(f"Channel {ch_id} : {str(ch_data)}"))
        #     # segmentTable.setItem(current_row, 1, QTableWidgetItem(str(patientsegment[seg_col_key[0]].get(ch_data)))) # segment data
        #     # segmentTable.setItem(current_row, 2, QTableWidgetItem(str(patientsegment[seg_col_key[1]]))) # is extend
        #     segmentTable.setItem(current_row, 3, QTableWidgetItem(str(patientsegment[seg_col_key[2]].get(ch_data)))) # absoqlute power
        #     segmentTable.setItem(current_row, 4, QTableWidgetItem(str(patientsegment[seg_col_key[3]].get(ch_data)))) # relative power 
        #     segmentTable.setItem(current_row, 5, QTableWidgetItem(str(patientsegment[seg_col_key[4]].get(ch_data)))) # band_ratios
        #     segmentTable.setItem(current_row, 6, QTableWidgetItem(str(patientsegment[seg_col_key[5]].get(ch_data)))) # amplitude asymmetry
        #     segmentTable.setItem(current_row, 7, QTableWidgetItem(str(patientsegment[seg_col_key[6]].get(ch_data)))) # phase_lag
        #     segmentTable.setItem(current_row, 8, QTableWidgetItem(str(patientsegment[seg_col_key[7]].get(ch_data)))) # coherence
            # segmentTable.setItem(current_row, 9, QTableWidgetItem(str(patientsegment[seg_col_key[8]]))) # interval_list
            # segmentTable.setItem(current_row, 10, QTableWidgetItem(str(patientsegment[seg_col_key[9]]))) # interval_count

        #     row_map[seg_id].append(current_row)
        # current_row += 1 
        # hidden = patientsegment.get("hideCh")
        # for sub_row in row_map[seg_id]:
        #     segmentTable.setRowHidden(sub_row, hidden )
            # segmentTable.setRowHidden(current_row,   )
        

def toggleHiddenRow(patientsegment, seg_id, segmentTable, row_map):

    hideCh = patientsegment.get("hideCh") 
    patientsegment['hideCh'] = not hideCh
    
    for sub_row in row_map[seg_id]:
        segmentTable.setRowHidden(sub_row, not hideCh)

def expandInfoWindow(patientsegments, seg_name):
    global compareWindows
    print("Expand ",seg_name)

    if seg_name not in compareWindows:
        compareWindow = QWidget()
        compareWindow.setWindowTitle(f"Expanded Info for Segment {seg_name}")
        compareWindow.setGeometry(100, 100, 800, 720)

        layout = QVBoxLayout()
        comparisonTable = QTableWidget(len(patientsegments[seg_name]['segment_data']), 7)  # Adjust size to match metrics
        
        # Column headers for expanded channel info
        comparisontable_colname = ["Channel", "absolute_power", "relative_power","band_ratios",  "amplitude_asymmetry", 
            "phase_lag", "coherence" ]
        
        comparisonTable.setHorizontalHeaderLabels(comparisontable_colname)
        segment = patientsegments[seg_name]
    
        # Loop through each channel and gather data for expanded info
        for row, ch_data in enumerate(segment['segment_data']):
            for i in range(len(comparisontable_colname)):
                if i == 0:
                    comparisonTable.setItem(row, i, QTableWidgetItem(f"CH {ch_data}"))
                else:
                    itemValue = segment[comparisontable_colname[i]].get(ch_data)
                    comparisonTable.setItem(row, i, QTableWidgetItem(str(itemValue))) # block = 

                    

        layout.addWidget(comparisonTable)
        compareWindow.setLayout(layout)
        compareWindow.show() 

        compareWindows[seg_name] = compareWindow # store the Expand info window