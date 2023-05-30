"""
Set of helper methods that are used in multiple Atari games
"""


def _convert_number(number):
    """
    Almost every Atari Game displays the time/score in hexadecimal numbers, while the ram extraction
    displays it as an integer.
    This results in a required conversion from the extracted ram number (in dec) to a hex number, which we then display
    as a dec number.

    e.g.: game shows 10 seconds, but the ram display saves it as 16
    """
    number_str = str(hex(number))
    number_list = [*number_str]
    number_str = ""
    count = 0
    for x in number_list:
        if count > 1:
            number_str += x
        count += 1
    return int(number_str)


def number_to_bitfield(n):
    """
    Convert number to 8 bit bitfield.

    Games like SpaceInvaders or Breakout use the bit representation of the number in the RAM to display or not display
    the objects. In most cases a 1 means the objects is displayed and a 0 means the object is not displayed.
    In SpaceInvaders the bit sequence needs to be reversed.
    """
    lst = [1 if digit == '1' else 0 for digit in bin(n)[2:]]
    buffer = [0] * (8 - len(lst))
    buffer.extend(lst)
    return buffer


def bitfield_to_number(b, flip=False):
    """
    Convert Bitfield to a number.
    """
    exp = len(b)-1
    if flip:
        exp = 0
    res = 0
    for bit in b:
        if bit == 1:
            res = res + pow(2, exp)

        if flip:
            exp = exp + 1
        else:
            exp = exp - 1

    return res

def get_iou(obj1, obj2):
    # determine the (x, y)-coordinates of the intersection rectangle
    xA = max(obj1.x, obj2.x)
    yA = max(obj1.y, obj2.y)
    xB = min(obj1.x+obj1.w, obj2.x+obj2.w)
    yB = min(obj1.y+obj1.h, obj2.y+obj2.h)
    # compute the area of intersection rectangle
    interArea = max(0, xB - xA) * max(0, yB - yA)
    # compute the area of both the prediction and ground-truth
    # rectangles
    boxAArea = (obj1.w) * (obj1.h)
    boxBArea = (obj2.w) * (obj2.h)
    # compute the intersection over union by taking the intersection
    # area and dividing it by the sum of prediction + ground-truth
    # areas - the interesection area
    iou = interArea / float(boxAArea + boxBArea - interArea)
    # return the intersection over union value
    return iou
