import sys
import numpy as np
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


def get_object_types(game_module, hud):
    if hud:
        return list(game_module.MAX_NB_OBJECTS_HUD.keys())
    else:
        return list(game_module.MAX_NB_OBJECTS.keys())


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


def get_reference_list(game_module, hud):
    ref_list = []
    if hud:
        max_obj_dict = game_module.MAX_NB_OBJECTS_HUD
    else:
        max_obj_dict = game_module.MAX_NB_OBJECTS
    for o in max_obj_dict.keys():
        ref_list.extend([o for _ in range(max_obj_dict[o])])
    return ref_list

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

def get_masked_dqn_state(objects):
    state = np.zeros((210, 160))
    for o in objects:
        if o is not None:
            x,y,w,h = o.xywh

            if x+w > 0 and y+h > 0:
                for i in range(max(0, y), min(y+h, 209)):
                    for j in range(max(0, x), min(x+w, 159)):
                        state[i, j] = 255
    return state


def get_masked_dqn_state2(objects, object_types):
    state = np.zeros((210, 160))
    for o in objects:
        if o is not None:
            x,y,w,h = o.xywh
            value = 255 * (1 + object_types.index(o.category)) // len(object_types)

            if x+w > 0 and y+h > 0:
                for i in range(max(0, y), min(y+h, 209)):
                    for j in range(max(0, x), min(x+w, 159)):
                        state[i, j] = value
    return state


def get_masked_dqn_state3(objects, gray_scale_img):
    state = np.zeros((210, 160))
    for o in objects:
        if o is not None:
            x,y,w,h = o.xywh

            if x+w > 0 and y+h > 0:
                for i in range(max(0, y), min(y+h, 209)):
                    for j in range(max(0, x), min(x+w, 159)):
                        state[i, j] = gray_scale_img[i, j]
    return state