import os
import numpy as np
import json
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt

class EEGSegmentPlotter(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("EEG Segment JSON Plotter")
        self.setGeometry(100, 100, 800, 600)

        # Layout
        layout = QVBoxLayout()

        # json File Selection
        self.json_label = QLabel("Select json File:")
        layout.addWidget(self.json_label)
        self.json_path_input = QLineEdit()
        layout.addWidget(self.json_path_input)
        self.json_browse_button = QPushButton("Browse")
        self.json_browse_button.clicked.connect(self.browse_json_file)
        layout.addWidget(self.json_browse_button)

        # Plot Button
        self.plot_button = QPushButton("Plot Segment")
        self.plot_button.clicked.connect(self.plot_json)
        layout.addWidget(self.plot_button)

        # Set the layout
        self.setLayout(layout)

    def browse_json_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select json File", "", "json Files (*.json)")
        if file_path:
            self.json_path_input.setText(file_path)

    def plot_json(self):
        json_file_path = self.json_path_input.text()
        if not os.path.isfile(json_file_path):
            QMessageBox.critical(self, "File Not Found", f"json file not found: {json_file_path}")
            return
        try:
            self.plot_data(json_file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def plot_data(self, json_path):

        with open(json_path,"r") as openfile:
            json_obj = json.load(openfile)
        # print(json_obj['data'])

        data = [list(x) for x in zip(*json_obj['data'])]
        plt.figure(figsize=(12, 6))
        plt.plot(json_obj['times'], data)
        plt.show()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = EEGSegmentPlotter()
    window.show()
    sys.exit(app.exec_())
