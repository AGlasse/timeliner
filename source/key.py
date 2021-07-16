class Key:

    def __init__(self):
        return

    def plot(self, ax, xtl, ytl):
        import matplotlib.pyplot as plt

        tab = 120.0
        margin = 2.0
        path = './inputs/key.txt'
        with open(path, 'r') as file:
            text_block = file.read()
        line_list = text_block.split('\n')
        x = xtl + margin
        dy = 8.0        # Line spacing
        fig = plt.figure()
        y = ytl - margin - dy
        xs = [xtl + margin, xtl + margin + tab]
        inf = 9999.0
        x0, x1, y0, y1 = inf, -inf, inf, -inf
        for line in line_list:
            tokens = line.split("\\t")
            for i in range(0, len(tokens)):
                text = ax.text(xs[i], y, tokens[i])
                renderer = fig.canvas.get_renderer()
                transf = ax.transData.inverted()
                bbox_pix = text.get_window_extent(renderer)
                bbox = bbox_pix.transformed(transf)
                x0 = x0 if x0 < bbox.xmin else bbox.xmin
                x1 = x1 if x1 > bbox.xmax else bbox.xmax
                y0 = y0 if y0 < bbox.ymin else bbox.ymin
                y1 = y1 if y1 > bbox.ymax else bbox.ymax
            y -= dy
        x0 -= margin
        y0 -= margin
        x1 += margin + 20.0
        y1 += margin
        x = [x0, x1, x1, x0, x0]
        y = [y0, y0, y1, y1, y0]
        ax.plot(x, y, color='black', ls='-')
        return
