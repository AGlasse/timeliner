#!/usr/bin/python
class Tools:
    """ Tools.
    """
    colours = ['pink', 'olive', 'cyan', 'aquamarine',
               'skyblue', 'plum', 'palegoldenrod', 'palegreen',
               'powderblue', 'lightsteelblue', 'thistle', 'sandybrown',
               'gold', 'violet', 'forestgreen', 'tomato',
               'mediumorchid', 'slateblue', 'lime', 'dodgerblue',
               'indianred', 'firebrick', 'yellow', 'orangered',
               'coral', 'crimson', 'red', 'chocolate',
               'sienna', 'sandybrown', 'peru', 'steelblue',
               'turquoise', 'teal', 'fuchsia', 'brown',
               'yellowgreen', 'lawngreen', 'indigo', 'brown'
               ]
    colour_index = 12
    colour_index_start = 12
    colour_index_end = 16

    def __init__(self, **kwargs):
        return

    @staticmethod
    def get_colour_list(n_colours, **kwargs):
        """ Generate a table of unique colours, with r, g, b values in
        the range """
        import random

        faint = kwargs.get('faint', 80)
        bright = kwargs.get('bright', 255)
        rgb_min = faint + faint + faint
        rgb_max = bright + bright + bright

        colours = []
        while len(colours) < n_colours:
            r = random.randint(0, 250)      # Avoid bright red bars...
            g = random.randint(0, 255)
            b = random.randint(0, 255)
            rgb = r + g + b
            if rgb_min < rgb and rgb < rgb_max:
                colour = "#{0:02x}{1:02x}{2:02x}".format(r, g, b)
                colours.append(colour)
        return colours

    @staticmethod
    def set_colour_table(**kwargs):
        n_colours = len(Tools.colours)
        table_dict = {'pale': (0, 24), 'dark': (12, n_colours-1)}
        table = kwargs.get('table', 'dark')
        a, b = table_dict[table]
        Tools.colour_index_start, Tools.colour_index_end = table_dict[table]
        Tools.colour_index = Tools.colour_index_start
        return

    @staticmethod
    def get_next_colour():
        idx = Tools.colour_index
        colour = Tools.colours[idx]
        idx += 1
        if idx == Tools.colour_index_end:
            idx = Tools.colour_index_start
        Tools.colour_index = idx
        return colour

    @staticmethod
    def is_dark(colour):
        """ True = Colour is 'dark', so should use a light colour as contrasting text """
        r = int(colour[1:3], 16)
        g = int(colour[3:5], 16)
        b = int(colour[5:7], 16)
        bright = r + g + b
        cut_level = 0x180
        is_dark = bright < cut_level
        return is_dark

    @staticmethod
    def filter_strcom(line):
        """ Filter commas from strings delimited by double quotes
        """
        i1 = line.find('"')
        while i1 > -1:
            pre = line[:i1]
            i2 = line[i1 + 1:].find('"')
            mid = line[i1:i1 + i2 + 2]
            mid = mid.replace(',', ' ')
            post = line[i1 + i2 + 2:]
            line = pre + mid[1:-1] + post
            i1 = line.find('"')
        return line
