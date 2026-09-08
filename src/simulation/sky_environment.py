import random
import math

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


class SkyEnvironment:

    def __init__(self):

        # -----------------------------
        # CREATE MOVING CLOUDS
        # -----------------------------

        self.clouds = []

        for _ in range(10):

            cloud = {
                "x": random.randint(-200, 1200),
                "y": random.randint(40, 450),
                "size": random.randint(60, 130),
                "speed": random.uniform(0.3, 0.8)
            }

            self.clouds.append(cloud)

    # ---------------------------------
    # UPDATE CLOUD POSITIONS
    # ---------------------------------

    def update(self, width):

        for cloud in self.clouds:

            cloud["x"] += cloud["speed"]

            # Reset cloud when it leaves screen

            if cloud["x"] > width + 200:

                cloud["x"] = -200

                cloud["y"] = random.randint(
                    40,
                    450
                )

    # ---------------------------------
    # DRAW SKY ENVIRONMENT
    # ---------------------------------

    def draw(
        self,
        painter,
        width,
        height
    ):

        # -----------------------------
        # SKY BACKGROUND
        # -----------------------------

        painter.fillRect(
            0,
            0,
            width,
            height,
            QColor(80, 160, 230)
        )

        # -----------------------------
        # DRAW CLOUDS
        # -----------------------------

        painter.setPen(Qt.NoPen)

        for cloud in self.clouds:

            x = int(cloud["x"])
            y = int(cloud["y"])
            size = cloud["size"]

            # Slight transparency

            painter.setBrush(
                QColor(
                    255,
                    255,
                    255,
                    180
                )
            )

            # Cloud circles

            painter.drawEllipse(
                x,
                y,
                size,
                size // 2
            )

            painter.drawEllipse(
                x + size // 3,
                y - size // 4,
                size,
                size // 2
            )

            painter.drawEllipse(
                x + size // 2,
                y,
                size,
                size // 2
            )

            # Bottom cloud body

            painter.drawEllipse(
                x + size // 6,
                y + size // 5,
                size + 20,
                size // 3
            )

    # ---------------------------------
    # DRAW MOVING SUN TARGET
    # ---------------------------------

    def draw_sun_target(
        self,
        painter,
        beacon_x,
        beacon_y,
        animation_time
    ):

        # Pulsing animation

        pulse = (
            math.sin(
                animation_time * 5
            )
            + 1
        ) / 2

        # Main sun radius

        sun_radius = 15 + pulse * 6

        # -----------------------------
        # OUTER SUN GLOW
        # -----------------------------

        glow_radius = (
            sun_radius * 2.5
        )

        painter.setPen(Qt.NoPen)

        painter.setBrush(

            QColor(
                255,
                180,
                0,
                int(
                    40 + pulse * 70
                )
            )

        )

        painter.drawEllipse(

            int(
                beacon_x - glow_radius
            ),

            int(
                beacon_y - glow_radius
            ),

            int(
                glow_radius * 2
            ),

            int(
                glow_radius * 2
            )

        )

        # -----------------------------
        # SUN RAYS
        # -----------------------------

        painter.setPen(
            QColor(
                255,
                220,
                80
            )
        )

        ray_length = (
            sun_radius
            + 10
            + pulse * 5
        )

        for angle in range(
            0,
            360,
            45
        ):

            radians = math.radians(
                angle
            )

            x1 = (
                beacon_x
                + math.cos(radians)
                * sun_radius
            )

            y1 = (
                beacon_y
                + math.sin(radians)
                * sun_radius
            )

            x2 = (
                beacon_x
                + math.cos(radians)
                * ray_length
            )

            y2 = (
                beacon_y
                + math.sin(radians)
                * ray_length
            )

            painter.drawLine(

                int(x1),
                int(y1),

                int(x2),
                int(y2)

            )

        # -----------------------------
        # MAIN SUN
        # -----------------------------

        painter.setPen(Qt.NoPen)

        painter.setBrush(
            QColor(
                255,
                210,
                50
            )
        )

        painter.drawEllipse(

            int(
                beacon_x - sun_radius
            ),

            int(
                beacon_y - sun_radius
            ),

            int(
                sun_radius * 2
            ),

            int(
                sun_radius * 2
            )

        )

        # -----------------------------
        # SUN CENTER
        # -----------------------------

        inner_radius = (
            sun_radius * 0.55
        )

        painter.setBrush(
            QColor(
                255,
                245,
                180
            )
        )

        painter.drawEllipse(

            int(
                beacon_x - inner_radius
            ),

            int(
                beacon_y - inner_radius
            ),

            int(
                inner_radius * 2
            ),

            int(
                inner_radius * 2
            )

        )