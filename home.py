import sys
import math
import random

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
)


# ============================================================
# FSOC BACKGROUND ANIMATION
# ============================================================

class FSOCBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        # Background particles
        self.stars = []

        for _ in range(90):
            self.stars.append({
                "x": random.random(),
                "y": random.random(),
                "speed": random.uniform(0.0002, 0.0008),
                "size": random.uniform(1, 2.5),
                "phase": random.uniform(0, math.pi * 2),
            })

        # Beam particles
        self.beam_particles = []

        for _ in range(25):
            self.beam_particles.append({
                "position": random.random(),
                "speed": random.uniform(0.002, 0.006),
                "offset": random.uniform(-1, 1),
            })

        self.animation_time = 0.0

        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(30)

    # --------------------------------------------------------
    # Animation update
    # --------------------------------------------------------

    def update_animation(self):
        self.animation_time += 0.03

        for star in self.stars:
            star["y"] += star["speed"]

            if star["y"] > 1.0:
                star["y"] = 0.0
                star["x"] = random.random()

        for particle in self.beam_particles:
            particle["position"] += particle["speed"]

            if particle["position"] > 1.0:
                particle["position"] = 0.0
                particle["offset"] = random.uniform(-1, 1)

        self.update()

    # --------------------------------------------------------
    # Paint background
    # --------------------------------------------------------

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        # ----------------------------------------------------
        # Main dark background
        # ----------------------------------------------------

        painter.fillRect(
            0,
            0,
            width,
            height,
            QColor(5, 10, 20)
        )

        # ----------------------------------------------------
        # Subtle grid
        # ----------------------------------------------------

        grid_pen = QPen(QColor(20, 35, 55))
        grid_pen.setWidth(1)

        painter.setPen(grid_pen)

        grid_spacing = 60

        for x in range(0, width, grid_spacing):
            painter.drawLine(x, 0, x, height)

        for y in range(0, height, grid_spacing):
            painter.drawLine(0, y, width, y)

        # ----------------------------------------------------
        # Background stars / particles
        # ----------------------------------------------------

        for star in self.stars:

            x = int(star["x"] * width)
            y = int(star["y"] * height)

            pulse = (
                math.sin(
                    self.animation_time * 2
                    + star["phase"]
                )
                + 1
            ) / 2

            alpha = int(40 + pulse * 90)

            painter.setPen(
                QColor(
                    100,
                    180,
                    255,
                    alpha
                )
            )

            size = int(star["size"])

            painter.drawEllipse(
                x,
                y,
                size,
                size
            )

        # ----------------------------------------------------
        # FSOC optical beam
        # ----------------------------------------------------

        tx_x = int(width * 0.14)
        tx_y = int(height * 0.52)

        rx_x = int(width * 0.86)
        rx_y = int(height * 0.52)

        # Main beam
        beam_pen = QPen(
            QColor(
                60,
                170,
                255,
                80
            )
        )

        beam_pen.setWidth(2)

        painter.setPen(beam_pen)

        painter.drawLine(
            tx_x,
            tx_y,
            rx_x,
            rx_y
        )

        # Secondary beam lines
        for offset in (-8, 8):

            secondary_pen = QPen(
                QColor(
                    50,
                    130,
                    220,
                    35
                )
            )

            secondary_pen.setWidth(1)

            painter.setPen(secondary_pen)

            painter.drawLine(
                tx_x,
                tx_y + offset,
                rx_x,
                rx_y + offset
            )

        # ----------------------------------------------------
        # Moving photons
        # ----------------------------------------------------

        for particle in self.beam_particles:

            t = particle["position"]

            x = tx_x + (rx_x - tx_x) * t
            y = tx_y + (rx_y - tx_y) * t

            offset = particle["offset"] * 7

            y += offset

            painter.setPen(
                QPen(
                    QColor(
                        120,
                        210,
                        255,
                        180
                    ),
                    3
                )
            )

            painter.drawPoint(
                int(x),
                int(y)
            )

        # ----------------------------------------------------
        # TRANSMITTER
        # ----------------------------------------------------

        painter.setPen(Qt.NoPen)

        painter.setBrush(
            QColor(
                50,
                150,
                255,
                45
            )
        )

        painter.drawEllipse(
            tx_x - 35,
            tx_y - 35,
            70,
            70
        )

        painter.setBrush(
            QColor(
                80,
                190,
                255,
                100
            )
        )

        painter.drawEllipse(
            tx_x - 14,
            tx_y - 14,
            28,
            28
        )

        painter.setBrush(
            QColor(
                150,
                230,
                255
            )
        )

        painter.drawEllipse(
            tx_x - 6,
            tx_y - 6,
            12,
            12
        )

        # ----------------------------------------------------
        # RECEIVER / BEACON
        # ----------------------------------------------------

        pulse = (
            math.sin(self.animation_time * 3)
            + 1
        ) / 2

        ring_size = int(
            65 + pulse * 20
        )

        painter.setPen(
            QPen(
                QColor(
                    80,
                    190,
                    255,
                    100
                ),
                2
            )
        )

        painter.setBrush(Qt.NoBrush)

        painter.drawEllipse(
            rx_x - ring_size // 2,
            rx_y - ring_size // 2,
            ring_size,
            ring_size
        )

        painter.setPen(
            QPen(
                QColor(
                    100,
                    210,
                    255,
                    150
                ),
                2
            )
        )

        painter.drawEllipse(
            rx_x - 25,
            rx_y - 25,
            50,
            50
        )

        painter.setPen(
            QPen(
                QColor(
                    150,
                    230,
                    255
                ),
                3
            )
        )

        painter.drawLine(
            rx_x - 18,
            rx_y,
            rx_x + 18,
            rx_y
        )

        painter.drawLine(
            rx_x,
            rx_y - 18,
            rx_x,
            rx_y + 18
        )

        painter.setPen(Qt.NoPen)

        painter.setBrush(
            QColor(
                150,
                230,
                255
            )
        )

        painter.drawEllipse(
            rx_x - 6,
            rx_y - 6,
            12,
            12
        )


# ============================================================
# HOME WINDOW
# ============================================================

class HomeWindow(QWidget):

    def __init__(self):
        super().__init__()

        # Keep Environment reference
        self.environment_window = None

        self.setWindowTitle(
            "FSOC Virtual Camera Tracking System"
        )

        self.setMinimumSize(
            1000,
            650
        )

        # ----------------------------------------------------
        # Background
        # ----------------------------------------------------

        self.background = FSOCBackground(self)

        self.background.setGeometry(
            self.rect()
        )

        # ----------------------------------------------------
        # Main layout
        # ----------------------------------------------------

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            80,
            60,
            80,
            50
        )

        main_layout.setSpacing(18)

        main_layout.setAlignment(
            Qt.AlignCenter
        )

        # ----------------------------------------------------
        # Title
        # ----------------------------------------------------

        title = QLabel(
            "FREE-SPACE OPTICAL COMMUNICATION"
        )

        title.setAlignment(
            Qt.AlignCenter
        )

        title.setStyleSheet("""
            QLabel {
                color: #EAF7FF;
                font-size: 30px;
                font-weight: 700;
                letter-spacing: 2px;
                background: transparent;
            }
        """)

        main_layout.addWidget(title)

        # ----------------------------------------------------
        # Subtitle
        # ----------------------------------------------------

        subtitle = QLabel(
            "OPTICAL BEACON TRACKING SYSTEM"
        )

        subtitle.setAlignment(
            Qt.AlignCenter
        )

        subtitle.setStyleSheet("""
            QLabel {
                color: #63C7FF;
                font-size: 19px;
                font-weight: 600;
                letter-spacing: 3px;
                background: transparent;
            }
        """)

        main_layout.addWidget(subtitle)

        # ----------------------------------------------------
        # Description
        # ----------------------------------------------------

        description = QLabel(
            "Pointing • Acquisition • Tracking\n"
            "Real-time optical beacon detection and camera alignment"
        )

        description.setAlignment(
            Qt.AlignCenter
        )

        description.setStyleSheet("""
            QLabel {
                color: #A8B8C8;
                font-size: 14px;
                line-height: 1.5;
                background: transparent;
            }
        """)

        main_layout.addSpacing(8)

        main_layout.addWidget(
            description
        )

        # ----------------------------------------------------
        # System status
        # ----------------------------------------------------

        status = QLabel(
            "●  SYSTEM READY"
        )

        status.setAlignment(
            Qt.AlignCenter
        )

        status.setStyleSheet("""
            QLabel {
                color: #67D7FF;
                font-size: 13px;
                font-weight: 600;
                background: transparent;
            }
        """)

        main_layout.addSpacing(12)

        main_layout.addWidget(
            status
        )

        # ----------------------------------------------------
        # START TRACKING BUTTON
        # ----------------------------------------------------

        start_button = QPushButton(
            "START TRACKING"
        )

        start_button.setCursor(
            Qt.PointingHandCursor
        )

        start_button.setFixedSize(
            240,
            55
        )

        start_button.setStyleSheet("""
            QPushButton {
                background-color: #123A5A;
                color: #EAF7FF;
                border: 1px solid #3DB8FF;
                border-radius: 8px;
                font-size: 15px;
                font-weight: 700;
                letter-spacing: 1px;
            }

            QPushButton:hover {
                background-color: #18537A;
                border: 1px solid #71D2FF;
            }

            QPushButton:pressed {
                background-color: #0D2C45;
            }
        """)

        # THIS IS THE IMPORTANT CONNECTION
        start_button.clicked.connect(
            self.open_environment
        )

        main_layout.addSpacing(10)

        main_layout.addWidget(
            start_button,
            alignment=Qt.AlignCenter
        )

        # ----------------------------------------------------
        # Footer
        # ----------------------------------------------------

        footer = QLabel(
            "VIRTUAL SIMULATION   •   VIDEO ANALYSIS   •   LIVE TRACKING"
        )

        footer.setAlignment(
            Qt.AlignCenter
        )

        footer.setStyleSheet("""
            QLabel {
                color: #627487;
                font-size: 11px;
                letter-spacing: 1px;
                background: transparent;
            }
        """)

        main_layout.addSpacing(20)

        main_layout.addWidget(
            footer
        )

    # ========================================================
    # RESIZE EVENT
    # ========================================================

    def resizeEvent(self, event):

        self.background.setGeometry(
            self.rect()
        )

        super().resizeEvent(event)

    # ========================================================
    # OPEN ENVIRONMENT
    # ========================================================

    def open_environment(self):

        print("START TRACKING CLICKED")

        try:

            # Import only when button is clicked.
            # This avoids unnecessary startup problems.
            from src.simulation.environment import Environment

            print("Environment imported successfully")

            # Create the existing Environment window
            self.environment_window = Environment()

            print("Environment created successfully")

            self.environment_window.setWindowTitle(
                "FSOC Virtual Camera Tracking System"
            )

            # Show Environment
            self.environment_window.showMaximized()

            print("Environment window displayed")

            # Hide Home only after Environment opens
            self.hide()

        except Exception as e:

            print(
                "ERROR OPENING ENVIRONMENT:"
            )

            print(
                type(e).__name__
            )

            print(
                str(e)
            )

            QMessageBox.critical(
                self,
                "Unable to Open Tracking Environment",
                "The Environment window could not be opened.\n\n"
                f"Error: {type(e).__name__}\n"
                f"{str(e)}"
            )


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    app = QApplication(
        sys.argv
    )

    window = HomeWindow()

    window.showMaximized()

    sys.exit(
        app.exec()
    )