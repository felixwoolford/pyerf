from itertools import cycle

from vispy import scene

from matplotlib.figure import Figure
from matplotlib.animation import Animation
from matplotlib.lines import Line2D
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

import numpy as np

COLORS = [
    "#fc5a50",
    "#7bc8f6",
    "#c20078",
    "#ffffcb",
    "#fac205",
    "#76ff7b",
    "#c5c9c7",
]

# Base class for general model visualizations
class BaseVispy:
    frontend = "vispy"

    def __init__(self, widget, axes=False, range_ = None, interactive=True, aspect = None, **kwargs):
        self.canvas = scene.SceneCanvas(
            keys="interactive", parent=widget, show=True, bgcolor="#24000E"
        )
        if axes:
            self.init_axes(**kwargs)
        else:
            self.view = self.canvas.central_widget.add_view()
            self.view.camera = "panzoom"

        if aspect is not None:
            self.view.camera.aspect = aspect
        self.range_ = range_
        if range_ is not None:
            self.view.camera.set_range(*range_)
        self.canvas.events.key_press.connect(self.key_pressed)  

    # override this for key events
    def key_pressed(self, event):
        pass

    def init_axes(self, **kwargs):
        self.grid = self.canvas.central_widget.add_grid(margin=10)
        self.grid.spacing = 0
        self.r = 0

        self.title = scene.Label(kwargs.get("title", ""), color="w")
        self.title.height_max = 40
        self.grid.add_widget(self.title, row=0, col=0, col_span=2)
        self.r += 1
        self.yaxis = scene.AxisWidget(
            orientation="left",
            axis_label=kwargs.get("y_label", ""),
            axis_font_size=10,
            axis_label_margin=40, #20?
            tick_label_margin=15,
        )
        self.yaxis.width_max = 80
        self.grid.add_widget(self.yaxis, row=self.r, col=0)

        self.xaxis = scene.AxisWidget(
            orientation="bottom",
            axis_label=kwargs.get("x_label", ""),
            axis_font_size=10,
            axis_label_margin=40,
            tick_label_margin=15,
        )
        self.xaxis.height_max = 80
        self.grid.add_widget(self.xaxis, row=self.r+1, col=1)

        right_padding = self.grid.add_widget(row=self.r, col=2, row_span=1)
        right_padding.width_max = 50

        self.view = self.grid.add_view(row=self.r, col=1, border_color="white")
        self.view.camera = "panzoom"
        self.view.camera.set_default_state()

        self.xaxis.link_view(self.view)
        self.yaxis.link_view(self.view)

    def iterate(self):
        raise NotImplementedError

    def reset(self):
        raise NotImplementedError
        
    
class BaseVispyTS(BaseVispy):
    def __init__(self, widget, vars_ = [], **kwargs):
        super().__init__(widget, axes = True, **kwargs)
        self._tracked_vars = []
        self.lines = []
        for var in vars_:
            self.add_var(var)
        self.minx = 0
        self.maxx = 1
        self.maxy = -np.inf
        self.miny = np.inf

    def add_var(self, var):
        self._tracked_vars.append(var)
        self.lines.append(
            scene.LinePlot(
                np.empty((2,1)), 
                color=COLORS[len(self.lines)%len(COLORS)], 
                marker_size=0, 
                parent = self.view.scene,
            )
        )

    def iterate(self):
        for i, lam in enumerate(self._tracked_vars):
            x = lam[0](lam[1]).tracked_variables[lam[2]][0]
            if len(lam) == 4:
                y = [x.item(lam[3]) for x in lam[0](lam[1]).tracked_variables[lam[2]][1]]
            else:
                y = lam[0](lam[1]).tracked_variables[lam[2]][1]
            self.lines[i].set_data((x, y), marker_size=0)
            if x[-1] > self.maxx:
                self.maxx = x[-1]
            if x[-1] < self.minx:
                self.minx = x[-1]
            if y[-1] > self.maxy:
                self.maxy = y[-1]
            if y[-1] < self.miny:
                self.miny = y[-1]
        if self.range_ is None:
            self.view.camera.set_range((self.minx, self.maxx),(self.miny, self.maxy))

    def reset(self):
        self.minx = 0
        self.maxx = 1
        self.maxy = -np.inf
        self.miny = np.inf
        self.iterate()

# Base class for custom plots, or model visualizations if vispy is unsuitable
class BaseMPL:
    frontend = "matplotlib"

    def __init__(self, size=(800, 800), dpi=100):
        x, y = size
        self.fig = Figure((x/dpi, y/dpi), dpi)
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)

    # update on custom call and/or on tab switch - used for static plots
    def update_triggered(self):
        pass

    # update every frame - used for dynamic plots
    def iterate(self):
        pass

# Base class for easily setting up time series plots
class BaseTS:
    frontend = "matplotlib"

    def __init__(self, vars_=[], xrange=None, update_r=0, figsize=(800, 800), dpi=100):
        x, y = figsize
        self.fig = Figure((x/dpi, y/dpi), dpi)
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        self._tracked_vars = []
        self.lines = []
        self.update_rate = update_r
        self.update_i = 0
        for var in vars_:
            self.add_var(var)
        self.xrange = xrange
        self.ax.set_xlim(xrange)
        self.ax.set_xlabel("time")
        self.set_colors()
        # self.ax.set_ylabel('x')
        self.minx = 0
        self.maxx = 1
        self.maxy = -np.inf
        self.miny = np.inf
    
    def add_var(self, var):
        self._tracked_vars.append(var)
    
    # override if neccesary
    def update_triggered(self):
        self.ax.lines = [] 
        for i, lam in enumerate(self._tracked_vars):
            x = lam[0](lam[1]).tracked_variables[lam[2]][0]
            if len(lam) == 4:
                y = [x.item(lam[3]) for x in lam[0](lam[1]).tracked_variables[lam[2]][1]]
            else:
                y = lam[0](lam[1]).tracked_variables[lam[2]][1]
            lines = Line2D(x, y, color = COLORS[i%len(COLORS)])
            self.ax.add_line(lines)
            if x[-1] > self.maxx:
                self.maxx = x[-1]
            if x[-1] < self.minx:
                self.minx = x[-1]
            if y[-1] > self.maxy:
                self.maxy = y[-1]
            if y[-1] < self.miny:
                self.miny = y[-1]
        if self.xrange is not None:
            self.ax.set_xlim(self.xrange)
        else:
            self.ax.set_xlim((self.minx, self.maxx))
            self.ax.set_ylim((self.miny, self.maxy))
        self.canvas.draw()
        self.canvas.flush_events()

    def reset(self):
        self.minx = 0
        self.maxx = 1
        self.maxy = -np.inf
        self.miny = np.inf
        self.update_triggered()

    def iterate(self):
        if self.update_rate:
            self.update_i += 1
            if self.update_i % self.update_rate == 0:
                self.update_i = 0
                self.update_triggered()

    def set_colors(self):

        line_color = "#FFFFFF"
        face_color = "#000000"

        self.fig.patch.set_facecolor(face_color)
        self.ax.patch.set_facecolor(face_color)

        self.ax.spines['bottom'].set_color(line_color)
        self.ax.spines['top'].set_color(line_color)
        self.ax.xaxis.label.set_color(line_color)
        self.ax.tick_params(axis='x', colors=line_color)

        self.ax.spines['right'].set_color(line_color)
        self.ax.spines['left'].set_color(line_color)
        self.ax.yaxis.label.set_color(line_color)
        self.ax.tick_params(axis='y', colors=line_color)
