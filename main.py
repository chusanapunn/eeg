import sys
from PyQt5.QtWidgets import QApplication
from utils.preprocessing import MainWindow

def main():
    app = QApplication(sys.argv)
    
    appwindow = MainWindow()
    appwindow.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()