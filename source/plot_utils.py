#!/usr/bin/env python
""" Created on Auf 22, 2019

@author: achg
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


class Plot:

    def __init__(self):
        self.next_slot = 0
        return

    @staticmethod
    def set_plot_area(title, **kwargs):
        xlim = kwargs.get('xlim', None)            # Common limits for all plots
        ylim = kwargs.get('ylim', None)            # Common limits for all plots
        xlabel = kwargs.get('xlabel', '')          # Common axis labels
        ylabel = kwargs.get('ylabel', '')
        ncols = kwargs.get('ncols', 1)             # Number of plot columns
        nrows = kwargs.get('nrows', 1)
        remplots = kwargs.get('remplots', None)
        aspect = kwargs.get('aspect', 'auto')      # 'equal' for aspect = 1.0
        fontsize = kwargs.get('fontsize', 9)

        gs = gridspec.GridSpec(nrows, ncols)
        gs.update(wspace=0.03, hspace=0.05)
        plt.rcParams.update({'font.size': fontsize})

        sharex = xlim is not None
        sharey = ylim is not None
        fig, ax_list = plt.subplots(nrows, ncols, figsize=[50, 50],
                                    sharex=sharex, sharey=sharey,
                                    squeeze=False)
        fig.patch.set_facecolor('white')
        fig.suptitle(title)
        fig.tight_layout(pad=8.0)

        for i in range(0, nrows):
            for j in range(0, ncols):
                ax = ax_list[i, j]
                ax.set_aspect(aspect)       # Set equal axes
                if xlim is not None:
                    ax.set_xlim(xlim)
                if ylim is not None:
                    ax.set_ylim(ylim)
                if i == nrows-1 and j == 0:
                    ax.set_xlabel(xlabel)
                    ax.set_ylabel(ylabel)
        if remplots is not None:
            rps = np.atleast_2d(remplots)
            for i in range(0, len(rps)):
                ax_list[rps[i, 0], rps[i, 1]].remove()
        return fig, ax_list

    @staticmethod
    def clear():
        plt.clf()
        plt.close('all')
        return

    @staticmethod
    def show():
        """ Wrapper for matplotlib show function. """
        plt.show()
