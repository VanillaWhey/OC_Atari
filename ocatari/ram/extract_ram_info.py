import sys
from termcolor import colored
import numpy as np

FEATURE_SIZE = 4

def get_max_objects(game_name, hud):
    p_module = __name__.split('.')[:-1] + [game_name.lower()]
    game_module = '.'.join(p_module)
    try:
        mod = sys.modules[game_module]
        objects = []
        if hud:
            max_obj_dict = mod.MAX_NB_OBJECTS_HUD
        else:
            max_obj_dict = mod.MAX_NB_OBJECTS
        for k, v in max_obj_dict.items():
            for _ in range(0, v):
                objects.append(getattr(mod, k)())
        return objects
    except KeyError as err:
        print(colored(f"Game module does not exist: {game_module}", "red"))
        raise err
    except AttributeError as err:
        print(colored(f"_get_max_objects not implemented for game: {game_name}", "red"))
        raise err


def init_objects(game_name, hud):
    p_module = __name__.split('.')[:-1] + [game_name.lower()]
    game_module = '.'.join(p_module)

    try:
        mod = sys.modules[game_module]
        return mod._init_objects_ram(hud)
    except KeyError as err:
        print(colored(f"Game module does not exist: {game_module}", "red"))
        raise err
    except AttributeError as err:
        print(colored(f"_init_objects_ram not implemented for game: {game_name}", "red"))
        raise err

def detect_objects_raw(info, ram_state, game_name):
    p_module = __name__.split('.')[:-1] + [game_name.lower()]
    game_module = '.'.join(p_module)

    try:
        mod = sys.modules[game_module]
        mod._detect_objects_raw(info, ram_state)
    except KeyError as err:
        print(colored(f"Game module does not exist: {game_module}", "red"))
        raise err
    except AttributeError as err:
        print(colored(f"_detect_objects_raw not implemented for game: {game_name}", "red"))
        raise err

def detect_objects_ram(objects, ram_state, game_name, hud):
    p_module = __name__.split('.')[:-1] + [game_name.lower()]
    game_module = '.'.join(p_module)
    for obj in objects:  # saving the previsous positions
        if obj is not None:
            obj._save_prev()
    try:
        mod = sys.modules[game_module]
        mod._detect_objects_ram(objects, ram_state, hud)
    except KeyError as err:
        print(colored(f"Game module does not exist: {game_module}", "red"))
        raise err
    except AttributeError as err:
        print(colored(f"_detect_objects_ram not implemented for game: {game_name}", "red"))
        raise err

def get_object_state_size(game_name, hud):
    p_module = __name__.split('.')[:-1] + [game_name.lower()]
    game_module = '.'.join(p_module)
    try:
        mod = sys.modules[game_module]
        if hud:
            return np.sum(list(mod.MAX_NB_OBJECTS_HUD.values()))
        return np.sum(list(mod.MAX_NB_OBJECTS.values()))
    except KeyError as err:
        print(colored(f"Game module does not exist: {game_module}", "red"))
        raise err
    

def get_object_state(reference_list, objects, game_name):
    p_module = __name__.split('.')[:-1] + [game_name.lower()]
    game_module = '.'.join(p_module)

    try:
        mod = sys.modules[game_module]
        state = mod._get_object_state(reference_list, objects)
        return state
    except KeyError as err:
        print(colored(f"Game module does not exist: {game_module}", "red"))
        raise err
    except AttributeError as err:
        #print(colored(f"_get_object_state not implemented for game: {game_name}", "red"))
        #print(colored(f"Try Default get_object_state", "red"))
        try:
            temp_ref_list = reference_list.copy()
            state = reference_list.copy()
            for o in objects: # populate out_vector with object instance
                if o is None:
                    continue
                idx = temp_ref_list.index(o.category) #at position of first category occurance
                state[idx] = o.xywh #write the slice
                temp_ref_list[idx] = "" #remove reference from reference list
            for i, d in enumerate(temp_ref_list):
                if d != "": #fill not populated category instances with 0.0's
                    state[i] = [0.0] * FEATURE_SIZE
            return state
        except AssertionError as err:
            raise err