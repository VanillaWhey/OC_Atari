from ._helper_methods import _convert_number
from .game_objects import GameObject, ValueObject
import sys

"""
RAM extraction for the game Freeway.
"""

MAX_NB_OBJECTS =  {
    'Chicken': 2,
    'Car': 10
}
MAX_NB_OBJECTS_HUD =  MAX_NB_OBJECTS | {
    'PlayerScore' : 2
}


class Chicken(GameObject):
    """
    The player figure i.e., the chicken. 
    """
    
    def __init__(self):
        super(Chicken, self).__init__()
        self._xy = 0, 0
        self.wh = 6, 8
        self.rgb = 252, 252, 84
        self.hud = False


class Car(GameObject):
    """
    The vehicles on the freeway. 
    """
    
    def __init__(self):
        super(Car, self).__init__()
        self._xy = 0, 0
        self.wh = 8, 10
        self.rgb = 167, 26, 26
        self.hud = False


class PlayerScore(ValueObject):
    """
    The player's score display (HUD).
    """
    
    def __init__(self):
        super(PlayerScore, self).__init__()
        self._xy = 49, 5
        self.wh = 6, 8
        self.rgb = 228, 111, 111
        self.hud = True
        self.value = 0


car_colors = {"car1": [167, 26, 26], "car2": [180, 231, 117], "car3": [105, 105, 15],
              "car4": [228, 111, 111], "car5": [24, 26, 167], "car6": [162, 98, 33],
              "car7": [84, 92, 214], "car8": [184, 50, 50], "car9": [135, 183, 84],
              "car10": [210, 210, 64]
              }


def _init_objects_ram(hud=False):
    """
    (Re)Initialize the objects
    """
    objects = [Chicken(), Chicken()]
    y = 27
    for color in car_colors.values():
        car = Car()
        car.rgb = (*color, )
        car.xy = 0, y
        objects.append(car)
        y += 16

    if hud:
        objects.append(PlayerScore())
        s = PlayerScore()
        s.xy = 113, 5
        objects.append(s)

    return objects


def _detect_objects_ram(objects, ram_state, hud=False):
    """
    For all objects:
    (x, y, w, h, r, g, b)
    """
    c1, c2 = objects[:2]
    cars = objects[2:12]
    scores = objects[12:14]

    c1.xy = 44, 193 - ram_state[14]
    c2.xy = 108, 193 - ram_state[15]

    for i, car in enumerate(cars):
        x = ram_state[117 - i] - 3
        car.x = x

    if hud:
        for i, score in enumerate(scores):
            score_value = _convert_number(ram_state[103 + i])
            if score_value is not None and score_value >= 10:
                score.x = 41 + i * 64
                score.w = 14
            score.value = score_value


def _detect_objects_freeway_raw(info, ram_state):
    info["chicken1_y"] = ram_state[14]
    info["chicken2_y"] = ram_state[15]
    info["score1"] = _convert_number(ram_state[103])
    info["score2"] = _convert_number(ram_state[104])
    info["car_x"] = ram_state[108:117]
