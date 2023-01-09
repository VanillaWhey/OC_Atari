from matplotlib import pyplot as plt
import sys
# import pathlib
sys.path.insert(0, '../../ocatari') # noqa
from ocatari import core
from ocatari.vision.utils import plot_bounding_boxes_from_info
from ocatari.vision.utils import find_objects, plot_bounding_boxes # noqa
import queue
import os
import pathlib

"""
trying to automate the creation of vision
mouse button :      to select the object   (you have to be very precise)
enter / close :    end selection / print out colors, code etc.
"""
rgb_array = []
name = "object0"
index = 0
objects = {}
colors = {}

callback_queue = queue.Queue() #for threading

def on_click(event):
    global index, name

    x, y = event.xdata, event.ydata
    if x is not None and y is not None:
        color = rgb_array[int(y)][int(x)]
        print(rgb_array[int(y)][int(x)])

        objects[name] = find_objects(rgb_array, color)
        colors[name] = color.tolist()
        print(objects[name])

        index += 1
        name = name[:-1] + str(index)
        show_altered_image()

def on_key_pressed(event):
    if event.key == "enter":
        plt.close()


def show_image():
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.add_artist(plt.imshow(rgb_array))
    cid = fig.canvas.mpl_connect("button_press_event", on_click)
    cid2 = fig.canvas.mpl_connect("key_press_event", on_key_pressed)
    cid2 = fig.canvas.mpl_connect("close_event", on_close)
    plt.show()

def show_altered_image():
    # threading.Thread(target = get_user_input, daemon = True).start()
    plt.close()
    info["objects"] = objects
    info["objects_colors"] = colors
    plot_bounding_boxes_from_info(rgb_array, info)
    show_image()

def on_close(event):
    print(colors)

def get_user_input():
    global name
    try:
        name = input("Enter " +str(index+1) +". Object Name:")
    except:
        pass
    # threading.main_thread()
    # callback_queue.put(plt.close)



def generate_code(game_name):
    code = "from .utils import find_objects\n\n\n"
    code += "objects_colors = " + str(colors) +"\n\n"
    code += "def _detect_objects_" + str(game_name) + "(info, obs):\n"
    code += "   objects = {}\n"
    for obj, col in colors.items():
        code += "   " + str(obj) + " = find_objects(obs, objects_colors['"+ str(obj) + "'], min_distance=1)\n"
        code += "    objects['" + str(obj) + "'] = " + str(obj) + "\n\n"

    code += "   info['objects_colors'] = objects_colors\n"
    code += "   info['objects'] = objects\n\n\n"

    return code


def write_code_to_file(code, game_name, overwrite = False):
    path = str(pathlib.Path().resolve()) + "/../../ocatari/vision/" + str(game_name) +".py"

    if not os.path.exists(path) or overwrite:
        with open(path, 'w') as f:
            print(code, file=f)
            print("code printed")


if __name__ == "__main__":
    GAME_NAME = "Skiingabc"
    env = core.OCAtari("Skiing", mode="vision", render_mode='rgb_array')
    rgb_array, info = env.reset()
    rgb_array = env.render()

    try:
        show_altered_image()
    except:
        on_close()

    code = generate_code(GAME_NAME)
    print("\n\n")
    print(code)
    write_code_to_file(code, GAME_NAME)




