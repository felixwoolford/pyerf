from itertools import cycle
import time
from vispy import scene

from matplotlib.figure import Figure
from matplotlib.animation import Animation
from matplotlib.lines import Line2D
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

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
class BaseTS(Animation):
    frontend = "matplotlib"

    def __init__(self, vars_=[], xrange=None, timer = None, figsize=(800, 800), dpi=100):
        x, y = figsize
        self.fig = Figure((x/dpi, y/dpi), dpi)
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        self._tracked_vars = []
        self.lines = []
        if timer is not None:
            self.static = False
        else:
            self.static = True
        self.colors = [
            "xkcd: coral",
            "xkcd: gold",
            "xkcd: lightblue",
            "xkcd: fuchsia",
            "xkcd: lightgreen",
            "xkcd: ivory",
            "xkcd: silver",
        ]
        
        for var in vars_:
            self.add_var(var)
        self.xrange = xrange
        self.ax.set_xlim(xrange)
        self.ax.set_xlabel("time")
        self.t = time.time()
        # self.ax.set_ylabel('x')
        if not self.static:
            self.timer = timer
            super().__init__(self.fig, event_source = self, blit=True)
    
    def add_var(self, var):
        self._tracked_vars.append(var)
        line = Line2D([], [], color='b', linewidth=3)
        if self.static:
            line.set_animated(True)
        self.lines.append(line)
        self.ax.add_line(line)
    
    # override if neccesary
    # update on custom call and/or on tab switch - used for static plots
    def update_triggered(self):
        self.min = 0
        self.max = 1
        if self.static:
            for i in range(len(self.lines)):
                lam = self._tracked_vars[i]
                x = lam[0](lam[1]).tracked_variables[lam[2]][0]
                y = lam[0](lam[1]).tracked_variables[lam[2]][1]
                self.lines[i] = Line2D(x, y)
                self.ax.add_line(self.lines[i])
                # self.ax.draw_artist(self.lines[i])
                if x[-1] > self.max:
                    self.max = x[-1]
            if self.xrange is not None:
                self.ax.set_xlim(self.xrange)
            else:
                self.ax.set_xlim((self.min, self.max))
            self.canvas.draw()
            # self.canvas.flush_events()
        else:
            pass

    # Not needed in this class
    def iterate(self):
        pass

    #Overriding animation functions
    def new_frame_seq(self):
        self._drawn_artists = [] # TODO
        for i in range(len(self.lines)):
            self.lines[i].set_data([], [])
            self._drawn_artists.append(self.lines[i]) # TODO

    def _step(self, *args):
        self._draw_next_frame(None, self._blit)
        return True

    def _draw_frame(self, framedata):
        self._drawn_artists = []
        for i in range(len(self.lines)):
            lam = self._tracked_vars[i]
            x = lam[0](lam[1]).tracked_variables[lam[2]][0]
            y = lam[0](lam[1]).tracked_variables[lam[2]][1]
            self.lines[i].set_data(x, y)
            self._drawn_artists.append(self.lines[i])

    # HACK functions to workaround the animation wanting a different timer
    def stop(self):
        self.timer.stop()

    def start(self):
        self.timer.start()

    def remove_callback(self, *args):
        self.timer.timeout.disconnect(self._step)

    def add_callback(self, *args):
        self.timer.timeout.connect(self._step)
