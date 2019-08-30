from vispy import scene
from matplotlib.figure import Figure
import numpy as np

class BaseEnvVisual:
    def __init__(self, widget, axes = None, interactive=True):

        self.canvas = scene.SceneCanvas(keys = "interactive", parent = widget, 
                                            show=True, bgcolor = 'k')
        if axes is not None:
            self.init_axes()
        else:
            self.view = self.canvas.central_widget.add_view()
            self.view.camera = 'panzoom'
    
    # override this and connect to canvas for key events
    # self.canvas.events.key_press.connect(self.key_pressed)
    def key_pressed(self, event):
        raise NotImplementedError



    # TODO a lot of this is hacked in
    def init_axes(self):
        self.grid = self.canvas.central_widget.add_grid(margin=10)
        self.grid.spacing = 0

        self.title = scene.Label("env", color='w')
        self.title.height_max = 40
        self.grid.add_widget(self.title, row=0, col=0, col_span=2)

        self.yaxis = scene.AxisWidget(orientation='left',
                                 #axis_label='Y Axis',
                                 axis_font_size=10,
                                 axis_label_margin=20,
                                 tick_label_margin=15)
        self.yaxis.width_max = 80
        self.grid.add_widget(self.yaxis, row=1, col=0)

        self.xaxis = scene.AxisWidget(orientation='bottom',
                                 axis_label='x',
                                 axis_font_size=10,
                                 axis_label_margin=40,
                                 tick_label_margin=15)

        self.xaxis.height_max = 80
        self.grid.add_widget(self.xaxis, row=2, col=1)

        right_padding = self.grid.add_widget(row=1, col=2, row_span=1)
        right_padding.width_max = 50

        self.view = self.grid.add_view(row=1,col=1, border_color='white')
        self.view.camera = 'panzoom'


        self.view.camera.set_default_state()

        self.xaxis.link_view(self.view)
        self.yaxis.link_view(self.view)

    def update_data(self):
        raise NotImplementedError

    def set_range(self, rangex, rangey):
        self.view.camera.set_range(x=rangex,y=rangey)
        
class BaseTSVisual:
    def __init__(self, x =800, y=400, dpi = 100):
        self.fig = Figure((x/dpi,y/dpi),dpi)
        self.ax = self.fig.add_subplot()
