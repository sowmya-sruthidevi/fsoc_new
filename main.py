import sys

from PySide6.QtWidgets import QApplication

from src.simulation.environment import Environment


def main():

    app = QApplication(sys.argv)

    window = Environment()

    window.setWindowTitle(
        "FSOC Virtual Camera Tracking System"
    )

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()