from .game_objects import GameObject, ValueObject
from ._helper_methods import _convert_number
import sys
import numpy as np

"""
RAM extraction for the game GALAXIAN. Supported modes: ram.
"""

# TODO: Diving Enemies, Enemy Missiles, Enemy x pos, width of PlayerScore and Round
MAX_NB_OBJECTS =  {
    'Player': 1,
    'PlayerMissile': 1,
    'EnemyMissile': 2,
    'EnemyShip': 35
}
MAX_NB_OBJECTS_HUD = MAX_NB_OBJECTS | {
    'PlayerScore': 1,
    'Round': 1,
    'Life': 3
}

class Player(GameObject):
    """
    The player figure i.e, the gun.
    """
    
    def __init__(self):
        super().__init__()
        self._xy = 66, 186
        self.wh = 8, 13
        self.rgb = 236, 236, 236
        self.hud = False


class PlayerMissile(GameObject):
    """
    The projectiles fired by the player. 
    """
    
    def __init__(self):
        super().__init__()
        self._xy = 66, 186
        self.wh = 1, 3
        self.rgb = 210, 164, 74
        self.hud = False


class EnemyMissile(GameObject):
    """
    The projectiles fired by the Enemy. 
    """
    
    def __init__(self):
        super().__init__()
        self._xy = 66, 186
        self.wh = 1, 4
        self.rgb = 228, 111, 111
        self.hud = False

class EnemyShip(GameObject):
    """
    The Enemy Ships. 
    """
    
    def __init__(self):
        super().__init__()
        self._xy = 66, 186
        self.wh = 6, 9
        self.rgb = 232, 204, 99
        self.hud = False

class PlayerScore(ValueObject):
    """
    The player's remaining lives (HUD).
    """
    
    def __init__(self):
        super().__init__()
        self.rgb = 232, 204, 99
        self._xy = 63, 4
        self.wh = 39, 7
        self.hud = True

class Round(GameObject):
    """
    The round counter display (HUD).
    """
    
    def __init__(self):
        super().__init__()
        self.rgb = 214, 214, 214
        self._xy = 137, 188
        self.wh = 7, 7
        self.hud = True

class Life(GameObject):
    """
    The remaining lives of the player (HUD).
    """
    
    def __init__(self):
        super().__init__()
        self.rgb = 214, 214, 214
        self._xy = 19, 188
        self.wh = 3, 7
        self.hud = True


def _init_objects_ram(hud=False):
    """
    (Re)Initialize the objects
    """
    objects = [Player(), PlayerMissile()]

    # for i in range(MAX_NB_OBJECTS('EnemyMissile')):
    #     missile = EnemyMissile()
    #     objects.append(missile)

    if hud:
        objects.extend([None, None, None, PlayerScore(), Round()])

    return objects


def _detect_objects_ram(objects, ram_state, hud=False):
    """
       For all objects:
       (x, y, w, h, r, g, b)
    """

    player = objects[0]
    if ram_state[11] != 255: #else player not on screen
        if player is None:
            player = Player()
            objects[0] = player
        player.x, player.y = ram_state[100]+8, 170 
    elif player is not None:
        objects[0] = None

    player_missile = objects[1]
    if ram_state[11] != 255 and ram_state[11] != 151: #else there is no missile
        if player_missile is None:
            player_missile = PlayerMissile()
            objects[1] = player_missile
        player_missile.x, player_missile.y = ram_state[60] + 2, ram_state[11] + 16
    elif player_missile is not None:
        objects[1] = None

    if hud:
        # lives
        for i in range(3):
            life = objects[2 + i]
            if i < ram_state[57] and life is None:
                life = Life()
                life.x += 5 * i
                objects[2 + i] = life
            elif i >= ram_state[57] and life:
                objects[2 + i] = None
        

    # ENEMIES
    # enemies deletion from objects:
    enemy_pos = np.where([isinstance(a, EnemyShip) for a in objects])[0]
    if len(enemy_pos) > 0:
        del objects[enemy_pos[0]:enemy_pos[-1] + 1]

    # The 7 rightmost bits of the ram positions 38 to 44 represent a bitmap of the enemies. 
    # Each bit is 1 if there is an enemy in its position and 0 if there is not.
    row_y = {0:19, 1:32, 2:43, 3:56, 4:67, 5:79} # the y-coordinates of the rows of enemies
    enemies = []
    for i in range(6):
        row = format(ram_state[38 + i] & 0x7F, '07b') #gets a string of the 7 relevant bits
        row = [int(x) for x in row]
        for j in range(len(row)):
            if row[j] == 1:
                enemy_ship = EnemyShip()
                enemy_ship.y = row_y[i]
                enemy_ship.x = 72 + 2 * ram_state[36] + j * 17
                enemies.append(enemy_ship)
                if i == 1 or i == 3:
                    enemy_ship.h = 8
    objects.extend(enemies)
    

def _detect_objects_galaxian_raw(info, ram_state):
    
    info["score"] = _convert_number(ram_state[45]) * 10000 + _convert_number(ram_state[45]) * 100 + _convert_number(ram_state[46])
    info["lives"] = ram_state[57]
    info["round"] = ram_state[47]