from itertools import cycle

from vispy import scene

from matplotlib.figure import Figure
from matplotlib.animation import TimedAnimation
from matplotlib.lines import Line2D

import numpy as np

# Base class for general model visualizations
class BaseVispy:
    frontend = "vispy"

    def __init__(self, widget, axes=None, interactive=True, **kwargs):
        self.canvas = scene.SceneCanvas(
            keys="interactive", parent=widget, show=True, bgcolor="#24000E"
        )
        if axes is not None:
            self.init_axes(**kwargs)
        else:
            self.view = self.canvas.central_widget.add_view()
            self.view.camera = "panzoom"

        self.canvas.events.key_press.connect(self.key_pressed)

    # override this for key events
    def key_pressed(self, event):
        pass

    # TODO a lot of this is hacked in
    def init_axes(self, **kwargs):
        self.grid = self.canvas.central_widget.add_grid(margin=10)
        self.grid.spacing = 0
    
        self.title = scene.Label(kwargs.get("title", "env"), color="w")
        if "title" in kwargs:
            self.title.height_max = 40
        else:
            self.title.height_max = 0
        self.grid.add_widget(self.title, row=0, col=0, col_span=2)

        self.yaxis = scene.AxisWidget(
            orientation="left",
            # axis_label='Y Axis',
            axis_font_size=10,
            axis_label_margin=20,
            tick_label_margin=15,
        )
        self.yaxis.width_max = 80
        self.grid.add_widget(self.yaxis, row=1, col=0)

        self.xaxis = scene.AxisWidget(
            orientation="bottom",
            axis_label="x",
            axis_font_size=10,
            axis_label_margin=40,
            tick_label_margin=15,
        )
        self.xaxis.height_max = 80
        self.grid.add_widget(self.xaxis, row=2, col=1)

        right_padding = self.grid.add_widget(row=1, col=2, row_span=1)
        right_padding.width_max = 50

        self.view = self.grid.add_view(row=1, col=1, border_color="white")
        self.view.camera = "panzoom"
        self.view.camera.set_default_state()

        self.xaxis.link_view(self.view)
        self.yaxis.link_view(self.view)

    def iterate(self):
        raise NotImplementedError

    def set_range(self, rangex, rangey):
        self.view.camera.set_range(x=rangex, y=rangey)

# Base class for custom plots, or model visualizations if vispy is unsuitable
class BaseMPL:
    frontend = "matplotlib"

    def __init__(self, size=(800, 800), dpi=100):
        x, y = size
        self.fig = Figure((x/dpi, y/dpi), dpi)
        self.ax = self.fig.add_subplot(111)

    # update on custom call and/or on tab switch - used for static plots
    def update_triggered(self):
        pass

    # update every frame - used for dynamic plots
    def iterate(self):
        pass

# TODO maybe set up a nice dynamic plotting feature for this too
# Base class for easily setting up time series plots
class BaseTS:
    frontend = "matplotlib"

    def __init__(self, var=None, xrange=None, static=True, size=(800, 800), dpi=100):
        x, y = size
        self.fig = Figure((x/dpi, y/dpi), dpi)
        self.ax = self.fig.add_subplot(111)
        self._tracked_vars = []
        self.lines = []
        if var is not None:
            self.add_var(var)
        self.xrange = xrange
        self.static = static
        self.ax.set_xlabel("time")
        # self.ax.set_ylabel('x')
        self.colors = cycle(
            [
                "xkcd: coral",
                "xkcd: gold",
                "xkcd: lightblue",
                "xkcd: fuchsia",
                "xkcd: lightgreen",
                "xkcd: ivory",
                "xkcd: silver",
            ]
        )

        self.bg_cache = self.fig.canvas.copy_from_bbox(self.ax.bbox)
    
    def add_var(self, var):
        self._tracked_vars.append(var)
        line = Line2D([], [], color=next(self.colors), linewidth=3)
        self.lines.append(line)
        self.ax.add_line(line)

    def update_blit(self, artists):
        self.fig.canvas.restore_region(self.bg_cache)
        for a in artists:
            a.axes.draw_artist(a)

        self.ax.figure.canvas.blit(self.ax.bbox)

    # override if neccesary
    # update on custom call and/or on tab switch - used for static plots
    def update_triggered(self):
        if self.static:
            if self.xrange is not None:
                self.ax.set_xlim(self.xrange)
            for var in self._tracked_vars:
                self.ax.plot(var[0][:], var[1][:])
        else:
            pass

    # override if necessary
    # update every frame - used for dynamic plots
    def iterate(self):
        if self.static:
            pass
        else:
            fig.canvas.draw()

            artists = func(f, *fargs)
            self.update_blit(artists)
            fig.canvas.start_event_loop(interval)
