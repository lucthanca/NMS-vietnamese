"""
NMS MXML Translator Helper

Main entry point for the application.
"""

import sys
import os
import signal
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow


def signal_handler(signum, frame):
    """Handle Ctrl+C and other termination signals."""
    print("\n\n🛑 Received termination signal - Force exiting...")
    print("If translation threads are running, they will be terminated.")
    os._exit(0)  # Force exit immediately, bypassing cleanup


def main():
    """
    Main application entry point.

    Initializes the Qt application and displays the main window.
    """
    # Set up signal handlers for forced termination
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGBREAK'):  # Windows
        signal.signal(signal.SIGBREAK, signal_handler)

    app = QApplication(sys.argv)
    app.setApplicationName("NMS MXML Translator Helper")
    app.setOrganizationName("NMS Vietnamese Translation Team")

    window = MainWindow()
    window.show()

    try:
        exit_code = app.exec()
        # Force exit after app closes to ensure threads don't hang
        print("Application closed - force exiting to terminate background threads...")
        os._exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n🛑 Keyboard interrupt - Force exiting...")
        os._exit(0)


if __name__ == "__main__":
    main()
