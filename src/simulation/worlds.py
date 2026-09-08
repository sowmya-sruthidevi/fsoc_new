from PySide6.QtGui import QColor


class World:

    SPACE = "SPACE"
    SKY = "SKY"
    URBAN = "URBAN"


def get_background_color(world):

    if world == World.SPACE:
        return QColor(15, 20, 35)

    elif world == World.SKY:
        return QColor(80, 170, 230)

    elif world == World.URBAN:
        return QColor(70, 70, 75)

    return QColor(15, 20, 35)