"""
NMS MXML Translator Helper

Main entry point for the application.
"""

import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    """
    Main application entry point.
    
    Initializes the Qt application and displays the main window.
    """
    app = QApplication(sys.argv)
    app.setApplicationName("NMS MXML Translator Helper")
    app.setOrganizationName("NMS Vietnamese Translation Team")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
