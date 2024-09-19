from PyQt5.QtWidgets import QLineEdit, QPushButton, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QListWidget, QWidget, QHBoxLayout

searchWindow = None
def openSearchWindow():
    global searchWindow

    layout = QVBoxLayout()
    searchWindow = QWidget()

    searchWindow.show()

    searchWindow.setWindowTitle("Search Metrics")
    searchWindow.setGeometry(100, 100, 500, 400)

    # Layout for Search Window
    layout = QVBoxLayout()

    # Textbox for Metric Search
    search_textbox = QLineEdit()
    search_textbox.setPlaceholderText("Enter metric name to search")
    layout.addWidget(search_textbox)

    # Search Button
    search_button = QPushButton("Search")
    search_button.clicked.connect(lambda: searchMetric(search_textbox.text(),result_list))
    layout.addWidget(search_button)

    # List Widget to Display Search Results
    result_list = QListWidget()
    layout.addWidget(result_list)

    searchWindow.setLayout(layout)

def searchMetric(search_str, result_list):

    search_str_ = search_str.split(";")
    for str in search_str_:
        result_list.addItem(str)
    # if search_str in metrics_data:
    #     result = f"{search_str}: {metrics_data[search_str]}"
    # else:
    #     result = f"Metric '{search_str}' not found."

    
    # result_list.addItem(result)



