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
        _ = mod._init_objects_ram
        _ = mod.MAX_NB_OBJECTS
        _ = mod.MAX_NB_OBJECTS_HUD
    except AttributeError as e:
        raise NotImplementedError(colored(f"{e.name} not implemented for game: {game_name}", "red"))
    return mod


def get_max_objects(game_module, hud):
    objects = []
    if hud:
        max_obj_dict = game_module.MAX_NB_OBJECTS_HUD
    else:
        max_obj_dict = game_module.MAX_NB_OBJECTS
    for k, v in max_obj_dict.items():
        for _ in range(0, v):
            objects.append(getattr(game_module, k)())
    return objects


def init_objects(game_module, hud):
    return game_module._init_objects_ram(hud)


def detect_objects_ram(objects, ram_state, game_module, hud):
    for obj in objects:  # saving the previous positions
        if obj is not None:
            obj._save_prev()
    game_module._detect_objects_ram(objects, ram_state, hud)


def get_object_state_size(game_module, hud):
    if hud:
        return sum(game_module.MAX_NB_OBJECTS_HUD.values())
    return sum(game_module.MAX_NB_OBJECTS.values())
    

def get_object_state(reference_list, objects, feature_attr, num_features):
    temp_ref_list = reference_list.copy()
    state = [[0] * num_features] * len(reference_list)

    for o in objects:  # populate out_vector with object instance
        if o is not None:
            idx = temp_ref_list.index(o.category)  # at position of first category occurrence
            state[idx] = getattr(o, feature_attr)  # write the slice
            temp_ref_list[idx] = False  # remove reference from reference list
    return state