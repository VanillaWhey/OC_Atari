from .game_objects import GameObject


class Player(GameObject):
    class Player(GameObject):
        def __init__(self, x, y, w, h, num, *args, **kwargs):
            super().__init__(x, y, w, h, *args, **kwargs)
            self.rgb = 187, 187, 53
            self.player_num = num
            # self.visible = False
            self._xy = 0, 0
            self.wh = 8, 11  # at some point 16, 11
            self.hud = False


class Cauldron(GameObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rgb = 167, 26, 26
        # self.visible = False
        self._xy = 0, 0
        self.wh = 6, 8
        self.hud = False


class Enemy(GameObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rgb = 228, 111, 111
        # self.visible = False
        self._xy = 0, 0
        self.wh = 7, 11
        self.hud = False


class Score(GameObject):
    def __init__(self, x, y, w, h, num, *args, **kwargs):
        super().__init__(x, y, w, h, *args, **kwargs)
        self.rgb = 187, 187, 53  # same color as player
        # self.visible = True
        self._xy = 0, 0
        self.wh = 8, 11
        self.hud = True


class Lives(GameObject):
    def __init__(self, y, *args, **kwargs):
        super().__init__(y, *args, **kwargs)
        self.rgb = 187, 187, 53  # same color as player
        # self.visible = True
        self._xy = 0, 0
        self.wh = 6, 7
        self.hud = True


# class Reward(GameObject):
#     def __init__(self, num, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.rgb = (
#             (198, 89, 179),
#             (135, 183, 84),
#             (195, 144, 61),
#             (213, 130, 74),
#             (135, 183, 84),
#             (163, 57, 21)
#         )[num - 1]
#         # self.visible = True
#         self._xy = 0, 0
#         self.wh = 6, 11
#         self.hud = False


class Helmet(GameObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rgb = 240, 128, 128
        # self.visible = True
        self._xy = 0, 0
        self.wh = 7, 11
        self.hud = False


class Shield(GameObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rgb = 214, 214, 214
        # self.visible = True
        self._xy = 0, 0
        self.wh = 5, 11
        self.hud = False


class Lamp(GameObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rgb = 187, 53, 53
        # self.visible = True
        self._xy = 0, 0
        self.wh = 8, 11
        self.hud = False


class Apple(GameObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rgb = 184, 50, 50
        # self.visible = True
        self._xy = 0, 0
        self.wh = 8, 11
        self.hud = False


class Fish(GameObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rgb = 198, 89, 179
        # self.visible = True
        self._xy = 0, 0
        self.wh = 8, 5
        self.hud = False


class Meat(GameObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rgb = 184, 50, 50  # ], [214, 214, 214]]
        # self.visible = True
        self._xy = 0, 0
        self.wh = 5, 11
        self.hud = False


class Mug(GameObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rgb = 184, 50, 50  # ], [214, 214, 214]]
        # self.visible = True
        self._xy = 0, 0
        self.wh = 7, 11
        self.hud = False



def _init_objects_asterix_ram(hud=False):
    """
    (Re)Initialize the objects
    """
    objects = [Player, Enemy, Cauldron, Helmet, Shield, Lamp, Apple, Fish, Meat, Mug]
    if hud:
        objects.extend([Score, Lives])

    return objects


def _detect_objects_asterix_raw(info, ram_state):
    info["x_positions"] = ram_state[41:50]  # 41 for player
    info["y_player"] = ram_state[39]  # from 0 to 7 (8 lanes) is there other possible values too!?
    info["score"] = ram_state[94:97]  # on ram in decimal/ on screen in hex(like other 2 games)
    info["lives"] = ram_state[83]
    info["ability_moving_objects"] = ram_state[19:27]
    # info["kind_of_objs"] = ram_state[29:37]  # just if enemy or cauldron (first bit lsb)

    print(ram_state)


def _detect_objects_asterix_revised(objects, ram_state, hud=False):
    objs = None  # could be Enemy, Reward, Cauldron, Helmet, Shield, Lamp, Apple, Fish, Meat or Mug
    player, *objs, score, lives = objects

    # for x in objs:
    #     if type(objs[x]) is Cauldron:
    #         objs[objs[x]].y = objs[objs[x]].y - 2
    #         objs[objs[x]].h = objs[objs[x]].h + 2

    print(ram_state)
    print(objects)
