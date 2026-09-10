import sys

from PySide6.QtWidgets import QApplication

from home import HomeWindow


def main():
    app = QApplication(sys.argv)

    window = HomeWindow()

    window.setWindowTitle(
        "FSOC Virtual Camera Tracking System"
    )

    window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()