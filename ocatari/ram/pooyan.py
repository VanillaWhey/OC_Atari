import sys
from .game_objects import GameObject, ValueObject
import numpy as np

"""
RAM extraction for the game Pong.

"""

MAX_NB_OBJECTS = {
    'Player': 1,
    'Arrow': 1,
    'Bait': 1,
    'Balloon':6,
    'Enemy': 7,
    'Stone': 1,
    'Rock': 1
}
MAX_NB_OBJECTS_HUD = MAX_NB_OBJECTS | {
    'PlayerScore': 1,
    'Life': 2
}


class Player(GameObject):
    """
    The player figure i.e., the mother pig(Mama).
    """
    
    def __init__(self):
        super().__init__()
        self.xy = 129, 61
        self.wh = 10, 15
        self.rgb = 236, 236, 236
        self.hud = False
        self.name = "Player"


class Arrow(GameObject):
    """
    The arrows thrown by the mother pig.
    """
    
    def __init__(self):
        super().__init__()
        self.xy = 130, 68
        self.wh = 8, 1
        self.rgb = 236, 236, 236
        self.hud = False


class Bait(GameObject):
    """
    The bait thrown by the mother pig.
    """
    
    def __init__(self):
        super().__init__()
        self.xy = 129, 68
        self.wh = 8, 4
        self.rgb = 184, 70, 162
        self.hud = False


class Balloon(GameObject):
    """
    The stones thrown by wolves.
    """
    
    def __init__(self):
        super().__init__()
        self.xy = 43, 61
        self.wh = 7, 7
        self.rgb = 236, 236, 236
        self.status = 0
            # 0: enemy without shield
            # 1: without enemy
            # 2: enemy with shield
            # 3: exploding
            # 4: exploding without enemy
            # 5: exploded and enemy falling
        self.hud = False


class Enemy(GameObject):
    """
    The wolves.
    """
    
    def __init__(self):
        super().__init__()
        self.xy = 44, 69
        self.wh = 8, 7
        self.rgb = 195, 144, 61
        self.hud = False


class Stone(GameObject):
    """
    The stones thrown by wolves.
    """
    
    def __init__(self):
        super().__init__()
        self.xy = 81, 63
        self.wh = 4, 4
        self.rgb = 236, 236, 236
        self.hud = False


class Rock(GameObject):
    """
    The rock thrown by wolves.
    """
    
    def __init__(self):
        super().__init__()
        self.xy = 55, 25
        self.wh = 16, 11
        self.rgb = 162, 98, 33
        self.hud = False


class PlayerScore(ValueObject):
    """
    The player's score display (HUD).
    """
    
    def __init__(self):
        super().__init__()
        self.xy = 96, 3
        self.wh = 5, 9
        self.rgb = 236, 236, 236
        self.score = 0
        self.hud = True

    def __eq__(self, o):
        return isinstance(o, PlayerScore) and self.xy == o.xy


class Life(GameObject):
    """
    The indicator for the remaining lives of the player (HUD). 
    """

    def __init__(self):
        super().__init__()
        self.visible = True
        self.xy = 37, 206
        self.rgb = 0, 0, 0
        self.wh = 2, 6
        self.hud = True



def _init_objects_ram(hud=False):
    """
    (Re)Initialize the objects
    """
    objects = [None] * 19 #Player(), Arrow(), Bait(), Balloon(), Enemy(), Stone(), Rock()
    if hud:
        objects.extend([None] * 3)
    return objects


def _detect_objects_ram(objects, ram_state, hud=False):
    """
    For all objects:
    (x, y, w, h, r, g, b)
    """
    # player
    player = Player()
    player.xy = 129, ram_state[31] * 21 + 40
    if ram_state[31] > 1:
        player.xy = 129, ram_state[31] * 21 + 41
        if ram_state[31] != 6:
            player.wh = 10, 14
    if ram_state[75] == 86:
        player.rgb = 184, 70, 162
    objects[0] = player

    # arrow and bait
    global projectile_offset
    global projectile_x0
    
    projectile = None
    if ram_state[40] == 0 or ram_state[40] == 81:
        projectile_offset = 0
        projectile_x0 = 44
    elif ram_state[40] >= 0:
        if ram_state[63] >= 128:
            shifted_rs63 = ram_state[63] - 128
        else:
            shifted_rs63 = 128 + ram_state[63]
        if shifted_rs63 % 16 != projectile_offset:
            projectile_offset = shifted_rs63 % 16
            if ram_state[66] >= 3 and ram_state[67] == 129:
                projectile_x0 += 1
            else:
                projectile_x0 -= 1
        
        projectile_x = (shifted_rs63 % 16) * 16 - projectile_x0 - shifted_rs63 // 16
        if ram_state[66] in [2, 4, 6]:
            projectile = Arrow()
            projectile.xy = projectile_x, ram_state[40] * 21 + 47
        elif ram_state[66] >= 3:
            projectile = Bait()
            projectile_y = (ram_state[40] % 16) * 21 + ram_state[40] // 16 + 42
            projectile.xy = projectile_x, projectile_y
    
    if ram_state[40] == 81 and ram_state[75] == 15:
        projectile = Bait()
        projectile.wh = 10, 4
    objects[1] = projectile

    # ballon and enemy
    balloons = [None] * 6
    balloon_color = [[236, 236, 236],
                     [127, 92, 213],
                     [160, 171, 79],
                     [187, 187, 53],
                     [92, 186, 92],
                     [214, 92, 92]]
    enemies = [None] * 6
    for i in range(32, 38):
        if ram_state[i] != 0:
            idx = (i - 32) // 2
            balloon = Balloon()
            balloon.xy = 43 + idx * 32, ram_state[i] * 21 + 40 + (ram_state[i] > 1) * 1
            balloon.rgb = balloon_color[i - 32]
            balloon.status = ram_state[i + 12]
            balloon.status = ram_state[i + 12]
            if balloon.status != 1 and balloon.status != 4:
                enemy = Enemy()
                if balloon.status == 2:
                    balloon.wh = 10, 8
                    enemy.xy = balloon.xy[0] + 2, balloon.xy[1] + 8
                    enemy.wh = 7, 8
                enemy.xy = balloon.xy[0] + 1, balloon.xy[1] + 8
                enemies[i - 32] = enemy
            if balloon.status == 5:
                balloon = None
            balloons[i - 32] = balloon
    for i in range(len(balloons)):
        objects[2 + i] = balloons[i]
        objects[8 + i] = enemies[i]
    
    climbing_enemy = None
    if ram_state[38] != 0:
        climbing_enemy = Enemy()
        if ram_state[50] == 0:
            climbing_enemy.xy = 145, ram_state[38] * 21 + 41
            climbing_enemy.wh = 7, 14
        if ram_state[50] == 1:
            climbing_enemy.xy = 141, ram_state[38] * 21 + 41
            climbing_enemy.wh = 8, 14
        if ram_state[50] == 2:
            climbing_enemy.xy = 137, ram_state[38] * 21 + 41
            climbing_enemy.wh = 8, 14
    objects[14] = climbing_enemy

    # stone
    global stone_x0
    global stone_offset
    global stone_column
    
    if not (ram_state[41] in range(17, 39)):
        stone_x0 = [37, 39]
        stone_offset = 0
        stone_column = 0

    stone = None
    stone_color = [[236, 236, 236],
                   [127, 92, 213],
                   [160, 171, 79],
                   [187, 187, 53],
                   [214, 92, 92],
                   [92, 186, 92]]
    if ram_state[41] != 0:
        stone = Stone()
        stone_x = 0
        shifted_rs64 = 0

        if ram_state[64] >= 128:
            shifted_rs64 = ram_state[64] - 128
        else:
            shifted_rs64 = 128 + ram_state[64]
        
        if shifted_rs64 % 16 != stone_offset:
            stone_offset = shifted_rs64 % 16
            stone_x0[0] += 1
            stone_x0[1] += 1
        
        if ram_state[65] > 5:
            starting_x = (shifted_rs64 % 16) * 16 - stone_x0[stone_column] - shifted_rs64 // 16
            if starting_x > 80:
                stone_column = 1
                
        stone_x = (shifted_rs64 % 16) * 16 - stone_x0[stone_column] - shifted_rs64 // 16
        stone_y = (ram_state[41] % 16) * 21 + ram_state[41] // 16 + 42
                
        row = 0
        if ram_state[41] in range(17, 23):
            row = ram_state[41] - 16
            stone_x -= 1
        elif ram_state[41] in range(33, 39):
            row = ram_state[41] - 32
        
        stone.xy = stone_x, stone_y
        
        for i in range(32, 36):
            if ram_state[i] == row:
                stone.rgb = stone_color[i - 32]
            elif ram_state[i] == row + 1:
                stone.rgb = stone_color[i - 32]
    objects[15] = stone
    
    # rock
    rock = None
    rock_x0 = [55, 63, 70, 78, 85, 93, 101]
    if ram_state[18] == 1 or ram_state[18] == 65:
        rock = Rock()
        rock.num_wolfs = ram_state[14]
        rock_x, rock_y = 0, 0
        if ram_state[39] == 0 and ram_state[18] == 1:
            rock_x = rock_x0[ram_state[14]]
            rock_y = 25
        else:
            rock_x = 121
            rock_y = ram_state[39] * 21 + 45
        rock.xy = rock_x, rock_y
    objects[16] = rock
    
    # player score
    player_score = None
    if hud:
        player_score = PlayerScore()
        a = ram_state[9] % 16 + 10 * (ram_state[9] // 16)
        b = ram_state[10] % 16 + 10 * (ram_state[10] // 16)
        player_score.score = a * 100 + b

        if player_score.score < 10:
            player_score.xy = 96, 3
            player_score.wh = 5, 9
        elif player_score.score < 100:
            if player_score.score < 20:
                player_score.xy = 89, 3
                player_score.wh = 12, 9
            else:
                player_score.xy = 88, 3
                player_score.wh = 13, 9
        elif player_score.score < 1000:
            if player_score.score < 200:
                player_score.xy = 81, 3
                player_score.wh = 20, 9
            else:
                player_score.xy = 80, 3
                player_score.wh = 21, 9
        else:
            if player_score.score < 2000:
                player_score.xy = 73, 3
                player_score.wh = 28, 9
            else:
                player_score.xy = 72, 3
                player_score.wh = 29, 9
    objects[17] = player_score

    # lives
    for i in range(2):
        life = objects[18 + i]
        if i < ram_state[22] and life is None:
            life = Life()
            life.x += 4 * i
            objects[18 + i] = life
        elif i >= ram_state[22] and life:
            objects[18 + i] = None
