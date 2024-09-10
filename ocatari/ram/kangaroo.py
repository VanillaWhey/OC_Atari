from typing import Type, Sequence, Dict

from .game_objects import GameObject, ValueObject, Orientation
from ._helper_methods import _convert_number
import sys

"""
RAM extraction for the game KANGAROO. Supported modes: ram.

"""

MAX_NB_OBJECTS = {
    'Player': 1,
    'Child': 1,
    'Fruit': 3,
    'Bell': 1,
    'Platform': 20,
    'Ladder': 6,
    'Monkey': 4,
    'FallingCoconut': 1,
    'ThrownCoconut': 3,
    'Life': 8,
    'Time': 1,
}

MAX_NB_OBJECTS_HUD = MAX_NB_OBJECTS | {
    'Score': 1
}


class Player(GameObject):
    """
    The player figure: Mother Kangaroo.
    """

    def __init__(self):
        super(Player, self).__init__()
        self._xy = 78, 103
        self.wh = 8, 24
        self.rgb = 223, 183, 85
        self.hud = False
        self.crashed = False
        self.climbing = False


class Child(GameObject):
    """
    Baby Kangaroo.
    """

    def __init__(self):
        super(Child, self).__init__()
        self._xy = 78, 12
        self.wh = 8, 15
        self.rgb = 223, 183, 85
        self.hud = False


class Monkey(GameObject):
    """
    The Monkey monkeys.
    """

    def __init__(self):
        super(Monkey, self).__init__()
        super().__init__()
        self._xy = 79, 57
        self.wh = 6, 15
        self.rgb = 227, 159, 89
        self.hud = False


class Fruit(GameObject):
    """
    The collectable fruits.
    """

    def __init__(self):
        super(Fruit, self).__init__()
        self._xy = 125, 173
        self.wh = 7, 11
        self.rgb = 214, 92, 92
        self.hud = False


class Ladder(GameObject):
    """
    The ladders.
    """

    def __init__(self, x=0, y=0, w=8, h=35):
        super(Ladder, self).__init__()
        self._xy = x, y
        self._prev_xy = x, y
        self.wh = w, h
        self.rgb = 162, 98, 33
        self.hud = False


class Platform(GameObject):
    """
    The platforms.
    """

    def __init__(self, x=0, y=0, w=8, h=4):
        super(Platform, self).__init__()
        self._xy = x, y
        self._prev_xy = x, y
        self.wh = w, h
        self.rgb = 162, 98, 33
        self.hud = False


class FallingCoconut(GameObject):
    """
    The dangerous apples dropping down from the top.
    """

    def __init__(self):
        super(FallingCoconut, self).__init__()
        self._xy = 0, 0
        self.wh = 2, 3
        self.rgb = 162, 98, 33
        self.hud = False


class ThrownCoconut(GameObject):
    """
    The apples thrown at the player by the monkeys.
    """

    def __init__(self):
        super(ThrownCoconut, self).__init__()
        self._xy = 0, 0
        self.wh = 2, 3
        self.rgb = 227, 159, 89
        self.hud = False


class Bell(GameObject):
    """
    The bell that can be used to replenish the collectable fruits.
    """

    def __init__(self):
        super(Bell, self).__init__()
        self._xy = 126, 173
        self.wh = 6, 11
        self.rgb = 210, 164, 74
        self.hud = False


class Score(ValueObject):
    """
    The player's score display (HUD).
    """

    def __init__(self):
        super(Score, self).__init__()
        self._xy = 129, 183
        self.wh = 15, 7
        self.rgb = 160, 171, 79
        self.hud = True
        self.value = 0


class Life(GameObject):
    """
    The player's remaining lives (HUD).
    """

    def __init__(self):
        super(Life, self).__init__()
        self._xy = 16, 183
        self.wh = 4, 7
        self.rgb = 160, 171, 79
        self.hud = False


class Time(ValueObject):
    """
    The time indicator (HUD).
    """

    def __init__(self):
        super(Time, self).__init__()
        self._xy = 80, 191
        self.wh = 15, 5
        self.rgb = 160, 171, 79
        self.hud = False
        self.value = 20


# def _init_all_objects() -> Dict[Type[GameObject], Sequence[GameObject]]:
#     mod = sys.modules[__name__]
#     all_objects = {}
#     for obj_cls_name, max_obj_count in MAX_ALL_OBJECTS.items():
#         obj_cls = getattr(mod, obj_cls_name)
#         all_objects[obj_cls] = max_obj_count * [None]
#     return all_objects



def _init_objects_ram(hud=True):
    """
    (Re)Initialize the objects
    """
    objects = [Player(), Child(), Monkey(), Monkey(), Monkey(), Monkey(),
               FallingCoconut(), ThrownCoconut(), ThrownCoconut(), ThrownCoconut(), Fruit(), Fruit(), Fruit(), Bell(),
               Platform(16, 172, w=128), Platform(16, 28, w=128)]
    objects.extend([None]* 26)
    if hud: 
        objects.extend([Score(), Time(), Life(), Life()])
        objects.extend([None]* 6)
    return objects


def _detect_objects_ram(objects, ram_state, hud=True):

    player = objects[0]

    x = ram_state[17] + 15
    y = ram_state[16] * 8 + 4

    orientation = Orientation.E if ram_state[18] in [8, 9, 28, 73, 74] else Orientation.W
    climbing = ram_state[18] in [39, 47]
    crashed = ram_state[54] in [1, 128]

    # Determine height during jump animation or during duck
    if ram_state[18] in [20, 28]:
        h = 16  # ducking
    elif ram_state[18] in [66, 74]:
        h = 15  # jump stooped
    elif ram_state[18] in [65, 73]:
        h = 23  # jump stretched
    else:
        h = 24  # default

    player.xy = x, y
    player.wh = 8, h
    player.orientation = orientation
    player.climbing = climbing
    player.crashed = crashed

    child = objects[1]
    # if ram_state[16] > 3 or (ram_state[83] != ram_state[17]):
    if ram_state[16] > 3:
        child.xy = ram_state[83] + 15, 12
    else:
        fruits = 0
        for i in range(3):
            if ram_state[42+i]&128:
                fruits +=1
        if fruits == 0:
            fruits = 1
        if ram_state[68] == fruits:         
            child.xy = ram_state[83] + 15, 12

    monkey = objects[2:6]

    for i in range(MAX_NB_OBJECTS["Monkey"]):
        if ram_state[11 - i] != 255 and ram_state[11 - i] != 127:
            x = ram_state[15 - i] + 16
            y = ram_state[11 - i] * 8 + 5
            if objects[2+i] is None:
                objects[2+i] = Monkey()
            objects[2+i].xy = x, y
        else:
            objects[2+i] = None

    # Falling coconut
    if ram_state[33] != 255:
        x = ram_state[34] + 14
        y = (ram_state[33] - 22 * ram_state[36]) * 8 + 9
        if objects[6] is None:
            objects[6] = FallingCoconut()
        objects[6].xy = x, y
    else:
        objects[6] = None

    # Thrown coconuts
    # This projectiles visual representation seems to differ from its RAM x position,
    # therefore you will see it leaving the bounding box on both left and right depending on the situation
    for i in range(MAX_NB_OBJECTS["ThrownCoconut"]):
        if ram_state[25 + i] != 255:
            x = ram_state[28 + i] + 15
            y = (ram_state[25 + i] * 8) + 1
            if objects[7+i] is None:
                objects[7+i] = ThrownCoconut()
            objects[7+i].xy = x, y
        else:
            objects[7+i] = None


    for i in range(MAX_NB_OBJECTS["Fruit"]):
        properties = _get_fruit_properties(ram_state[42 + i])
        if properties is not None:
            fruit = objects[10+i]
            wh, rgb = properties
            if ram_state[87] == ram_state[86]:
                y = (ram_state[84 + i] * 8) + 4
            else:
                y = (ram_state[85 + i] * 8) + 4
            if ram_state[92] == ram_state[91]:
                x = ram_state[89 + i] + 15
            else:
                x = ram_state[90 + i] + 15
            if fruit is None:
                fruit = Fruit()
            fruit.xy = x, y
            fruit.wh = wh
            fruit.rgb = rgb
        else:
            objects[10+i] = None


    # bell
    lvl = ram_state[36]
    if ram_state[41] == 128:
        objects[13] = None
    elif lvl < 3:
        x = [93, 31, 130][lvl]
        y = 36
        objects[13].xy = x, y

    # Only on level change
    current_level = ram_state[36]
    if objects[17] is None \
        or (current_level == 0 and objects[17].xy[1] != 76) \
        or (current_level == 1 and objects[17].xy[1] != 124) \
        or (current_level == 2 and objects[17].xy[1] != 140):
        platform = manage_platforms(current_level, objects)
        for i in range(26):
            if platform[i]:
                objects[14+i] = platform[i]
            else:
                objects[14+i] = None


    if hud:

        # score
        score_value = _convert_number(ram_state[39]) * 10000 + \
                    _convert_number(ram_state[40]) * 100

        if score_value < 100:
            x = 129
            w = 15
        elif 100 <= score_value < 1000:
            x = 121
            w = 23
        elif 1000 <= score_value < 10000:
            x = 113
            w = 31
        elif 10000 <= score_value < 100000:
            x = 105
            w = 39
        else:
            x = 97
            w = 47

        objects[-10].xy = x, 183
        objects[-10].wh = w, 7
        objects[-10].value = score_value

        # time
        time_value = ram_state[59]
        if time_value <= 32:
            time_remaining = _convert_number(time_value)
        else:
            time_remaining = time_value - 160
        objects[-9].value = time_remaining

        # lives
        n_lives = ram_state[45]
        for i in range(MAX_NB_OBJECTS["Life"]):
            if i < n_lives != 255:
                if objects[-8+i] is None:
                    objects[-8+i] = Life()
                x = 16 + (i * 8)
                y = 183
                objects[-8+i].xy = x, y
            else:
                objects[-8+i] = None


def _detect_objects_kangaroo_raw(info, ram_state):
    # for proper y coordinates you will have to multiply by 8
    # if the coordinates equal 255 they are not visible on screen
    info["ram_slice"] = ram_state[0:18] + ram_state[25], ram_state[28], ram_state[33:35], ram_state[83]


def _get_fruit_properties(ram_value):
    """Returns the fruit properties depending on the given RAM value.
    Returns (wh, rgb) or None if no Fruit there."""

    if ram_value < 128:
        if ram_value % 4 == 0:
            return (7, 11), (214, 92, 92)
        elif ram_value % 4 == 1:
            return (7, 9), (214, 92, 92)
        elif ram_value % 4 == 2:
            return (8, 11), (214, 92, 92)
        if ram_value % 4 == 3:
            return (8, 11), (195, 144, 61)
    else:
        return None


def manage_platforms(current_lvl_val, _):
    platforms = [Platform(16, 172, w=128), Platform(16, 28, w=128)]

    # There is a total of 3 levels
    if current_lvl_val == 0:
        platforms.extend([
            Ladder(132, 132),
            Ladder(20, 85),
            Ladder(132, 37),
            None,
            None,
            None,
            Platform(16, 76, w=128),
            Platform(16, 124, w=128),
        ])
        platforms.extend([None]*16)

    elif current_lvl_val == 1:
        platforms.extend([
            Ladder(120, 132, h=4),
            Ladder(24, 116, h=4),
            Ladder(128, 36, h=4),
            None,
            None,
            None,
            Platform(16, 124, w=28), Platform(52, 124, w=92),
            Platform(16, 76, w=60), Platform(84, 76, w=60),
            Platform(28, 164, w=24), Platform(112, 84, w=24),
            Platform(120, 44, w=24), Platform(48, 156, w=32),
            Platform(76, 148, w=32), Platform(104, 140, w=32),
            Platform(16, 108, w=32), Platform(56, 100, w=20),
            Platform(84, 92, w=20), Platform(64, 60, w=20),
            Platform(92, 52, w=20), Platform(28, 68, w=28)
        ])
        platforms.extend([None]*10)

    else:  # current_lvl_val == 2
        platforms.extend([
            Ladder(20, 36, h=28),
            Ladder(20, 148, h=4),
            Ladder(36, 116, h=20),
            Ladder(104, 36, h=20),
            Ladder(120, 68, h=4),
            Ladder(132, 84, h=4),
            Platform(88, 140, w=16), Platform(64, 148, w=16), Platform(100, 116, w=16),
            Platform(48, 100, w=16), Platform(76, 52, w=16), Platform(80, 36, w=16),
            Platform(104, 132, w=20), Platform(84, 156, w=20), Platform(124, 124, w=20),
            Platform(52, 84, w=20), Platform(108, 164, w=36), Platform(16, 108, w=80),
            Platform(16, 92, w=28), Platform(76, 92, w=68), Platform(16, 140, w=32),
            Platform(96, 60, w=36), Platform(100, 76, w=44), Platform(60, 44, w=12)
        ])
    return platforms