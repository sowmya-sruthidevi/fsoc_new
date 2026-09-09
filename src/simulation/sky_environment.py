import random
import math

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


class SkyEnvironment:

    def __init__(self):

        # ---------------------------------
        # CREATE MOVING CLOUDS
        # ---------------------------------

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
        # SUN OCCLUSION STATUS
        # ---------------------------------

        self.sun_occluded = False


    # ---------------------------------
    # UPDATE CLOUD POSITIONS
    # ---------------------------------

    def update(self, width):

        for cloud in self.clouds:

            # Natural cloud movement
            cloud["x"] += cloud["speed"]

            # Reset cloud when it leaves screen

            if cloud["x"] > width + 200:

                cloud["x"] = -200

                cloud["y"] = random.randint(
                    40,
                    450
                )

                cloud["size"] = random.randint(
                    60,
                    130
                )

                cloud["speed"] = random.uniform(
                    0.3,
                    0.8
                )


    # ---------------------------------
    # CHECK SUN OCCLUSION
    # ---------------------------------

    def check_sun_occlusion(

        self,

        sun_x,

        sun_y,

        sun_radius=25

    ):

        # Default:
        # Sun is visible

        self.sun_occluded = False

        # Check every cloud

        for cloud in self.clouds:

            cloud_x = cloud["x"]
            cloud_y = cloud["y"]
            cloud_size = cloud["size"]

            # ---------------------------------
            # CLOUD VISUAL BOUNDARIES
            # ---------------------------------

            # Your cloud consists of multiple
            # ellipses, so we use a larger
            # approximate rectangle.

            left = cloud_x

            right = (

                cloud_x
                +
                cloud_size * 1.5
            )

            top = (

                cloud_y
                -
                cloud_size * 0.25
            )

            bottom = (

                cloud_y
                +
                cloud_size * 0.7
            )

            # ---------------------------------
            # CHECK IF SUN OVERLAPS CLOUD
            # ---------------------------------

            if (

                sun_x + sun_radius >= left

                and

                sun_x - sun_radius <= right

                and

                sun_y + sun_radius >= top

                and

                sun_y - sun_radius <= bottom

            ):

                self.sun_occluded = True

                return True

        return False


    # ---------------------------------
    # DRAW SKY ENVIRONMENT
    # ---------------------------------

    def draw(

        self,

        painter,

        width,

        height

    ):

        # ---------------------------------
        # SKY BACKGROUND
        # ---------------------------------

        painter.fillRect(

            0,

            0,

            width,

            height,

            QColor(
                80,
                160,
                230
            )

        )

        # ---------------------------------
        # DRAW CLOUDS
        # ---------------------------------

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

        # ---------------------------------
        # PULSING ANIMATION
        # ---------------------------------

        pulse = (

            math.sin(

                animation_time * 5

            )

            + 1

        ) / 2

        # Main sun radius

        sun_radius = (

            15
            +
            pulse * 6

        )

        # ---------------------------------
        # OUTER SUN GLOW
        # ---------------------------------

        glow_radius = (

            sun_radius * 2.5

        )

        painter.setPen(
            Qt.NoPen
        )

        painter.setBrush(

            QColor(

                255,

                180,

                0,

                int(

                    40
                    +
                    pulse * 70

                )

            )

        )

        painter.drawEllipse(

            int(

                beacon_x
                -
                glow_radius

            ),

            int(

                beacon_y
                -
                glow_radius

            ),

            int(

                glow_radius * 2

            ),

            int(

                glow_radius * 2

            )

        )

        # ---------------------------------
        # SUN RAYS
        # ---------------------------------

        painter.setPen(

            QColor(

                255,

                220,

                80

            )

        )

        ray_length = (

            sun_radius

            +

            10

            +

            pulse * 5

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

                +

                math.cos(radians)
                *
                sun_radius

            )

            y1 = (

                beacon_y

                +

                math.sin(radians)
                *
                sun_radius

            )

            x2 = (

                beacon_x

                +

                math.cos(radians)
                *
                ray_length

            )

            y2 = (

                beacon_y

                +

                math.sin(radians)
                *
                ray_length

            )

            painter.drawLine(

                int(x1),

                int(y1),

                int(x2),

                int(y2)

            )

        # ---------------------------------
        # MAIN SUN
        # ---------------------------------

        painter.setPen(
            Qt.NoPen
        )

        painter.setBrush(

            QColor(

                255,

                210,

                50

            )

        )

        painter.drawEllipse(

            int(

                beacon_x
                -
                sun_radius

            ),

            int(

                beacon_y
                -
                sun_radius

            ),

            int(

                sun_radius * 2

            ),

            int(

                sun_radius * 2

            )

        )

        # ---------------------------------
        # SUN CENTER
        # ---------------------------------

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

                beacon_x
                -
                inner_radius

            ),

            int(

                beacon_y
                -
                inner_radius

            ),

            int(

                inner_radius * 2

            ),

            int(

                inner_radius * 2

            )

        )


    # ---------------------------------
    # DRAW CLOUDS IN FRONT OF SUN
    # ---------------------------------

    def draw_foreground_clouds(

        self,

        painter

    ):

        """
        Draw clouds again after the sun.

        This makes a cloud visually cover
        the sun when it naturally passes
        in front of it.
        """

        painter.setPen(Qt.NoPen)

        for cloud in self.clouds:

            x = int(cloud["x"])

            y = int(cloud["y"])

            size = cloud["size"]

            painter.setBrush(

                QColor(

                    255,

                    255,

                    255,

                    200

                )

            )

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

            painter.drawEllipse(

                x + size // 6,

                y + size // 5,

                size + 20,

                size // 3

            )