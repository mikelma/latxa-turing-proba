import random


def add_typos(message: str, typo_prob: float = 0.01, upper_prob: float = 0.02) -> str:
    """
    Introduce typos into a given message based on a specified probability.

    Parameters:
    message (str): The original message to modify.
    typo_prob (float): The probability (between 0 and 1) of each character being replaced with a nearby key.
    upper_prob (float): The probability (between 0 and 1) of capitalizing a character if the previous one was capitalized.

    Returns:
    str: The modified message with typos.
    """

    msg = list(message)

    # the number of characters that will be typos
    n_chars_to_flip = round(len(msg) * typo_prob)
    # is a letter capitalized?
    capitalization = [False] * len(msg)
    # make all characters lowercase & record uppercase
    for i in range(len(msg)):
        capitalization[i] = msg[i].isupper()
        msg[i] = msg[i].lower()

    # list of characters that will be flipped
    pos_to_flip = []
    for i in range(n_chars_to_flip):
        pos_to_flip.append(random.randint(0, len(msg) - 1))

    # dictionary... for each letter list of letters
    # nearby on the keyboard
    nearbykeys = {
        'a': ['q','w','s','x','z'],
        'b': ['v','g','h','n'],
        'c': ['x','d','f','v'],
        'd': ['s','e','r','f','c','x'],
        'e': ['w','s','d','r'],
        'f': ['d','r','t','g','v','c'],
        'g': ['f','t','y','h','b','v'],
        'h': ['g','y','u','j','n','b'],
        'i': ['u','j','k','o'],
        'j': ['h','u','i','k','n','m'],
        'k': ['j','i','o','l','m'],
        'l': ['k','o','p'],
        'm': ['n','j','k','l'],
        'n': ['b','h','j','m', 'ñ'],
        'o': ['i','k','l','p'],
        'p': ['o','l'],
        'q': ['w','a','s'],
        'r': ['e','d','f','t'],
        's': ['w','e','d','x','z','a'],
        't': ['r','f','g','y'],
        'u': ['y','h','j','i'],
        'v': ['c','f','g','v','b'],
        'w': ['q','a','s','e'],
        'x': ['z','s','d','c'],
        'y': ['t','g','h','u'],
        'z': ['a','s','x'],
        ' ': ['c','v','n','m'],
        ',': ['m','k','l','.'],
        '.': [',','l',';','-', ':'],
    }

    # insert typos
    for pos in pos_to_flip:
        # try-except in case of special characters
        try:
            typo_arrays = nearbykeys[msg[pos]]
            msg[pos] = random.choice(typo_arrays)
        except:
            break

    # reinsert capitalization
    for i in range(len(msg)):
        if (capitalization[i]):
            msg[i] = msg[i].upper()
        elif i > 0 and capitalization[i-1]:
            if random.random() < upper_prob:
                msg[i] = msg[i].upper()

    # recombine the message into a string
    message = ''.join(msg)

    # show the message in the console
    print(message)

    return message