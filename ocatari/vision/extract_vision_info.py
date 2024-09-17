import sys
from termcolor import colored


def get_module(game_name):
    p_module = __name__.split('.')[:-1] + [game_name.lower()]
    game_module = '.'.join(p_module)
    try:  # get module
        mod = sys.modules[game_module]
    except KeyError as err:
        print(colored(f"Game module does not exist: {game_module}", "red"))
        raise err
    try:  # test if essential elements exist
        _ = mod._detect_objects
    except AttributeError as e:
        raise NotImplementedError(colored(f"{e.name} not implemented for game: {game_name}", "red"))
    return mod


def detect_objects_vision(objects, obs, game_module, hud):
    return game_module._detect_objects(objects, obs, hud)
