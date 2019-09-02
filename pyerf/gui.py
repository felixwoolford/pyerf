import sys
import threading

import PyQt5.QtWidgets as pqtw
import PyQt5.QtCore as pqtc
from PyQt5.QtGui import QSurfaceFormat
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class GUIWindow(pqtw.QMainWindow):
    # all custom signals are handled by GUIWindow
    fps_signal = pqtc.pyqtSignal(int)
    reset_signal = pqtc.pyqtSignal(bool)
    add_tab_signal = pqtc.pyqtSignal(str, bool, str)
    insert_visual_signal = pqtc.pyqtSignal(int, int, object, object, object)
    swap_visual_signal = pqtc.pyqtSignal(int, int, int)

    def __init__(self, core, fps):
        super().__init__(None, pqtc.Qt.WindowStaysOnTopHint)
        self.mf = MainFrame(self, core, fps)
        self.setCentralWidget(self.mf)
        self.mf.setMinimumSize(self.mf.qtab.size())
        self.move(200, 0)
        self.setWindowTitle(core.title)
        self.adjustSize()
        self.show()
        self.fps_signal.connect(self.mf.timer.setInterval)
        self.reset_signal.connect(self.mf.reset)
        self.add_tab_signal.connect(self.mf.add_tab)
        self.insert_visual_signal.connect(self.insert_visual) 
        self.swap_visual_signal.connect(self.swap_visual)

    def swap_visual(self, tab, w_index, v_index):
        self.mf.tabs[tab].visuals[w_index].swap_visual(v_index)

    def insert_visual(self, tab, index, class_, *args, **kwargs):
        self.mf.tabs[tab].visuals[index].insert_visual(class_, *args, **kwargs)
    
    
class MainFrame(pqtw.QFrame):
    def __init__(self, parent, core, fps):
        super().__init__(parent)
        self.core = core
        self.setAutoFillBackground(True)

        self.setStyleSheet(
            """             QFrame{background-color: black; color: white}
                            \\\\VispyFrame{background-color: #110626}
                            VispyFrame{background-color: #24000E}
                            QDialog{background-color: black}
                            QTabWidget{
                                background-color: black; 
                                color: yellow; 
                                background: yellow
                            }
                            QTabBar{
                                background: yellow;
                                border: 2px solid black;
                                border-bottom-color: yellow;
                                border-left-color: yellow;
                                border-right-color: yellow;
                                border-top-left-radius: 4px;
                                border-top-right-radius: 4px;
                                min-width: 8ex;
                                padding: 2px;
                            }
                            V
                            QComboBox{background-color: black; color: white}
                            QLineEdit{background-color: black; color: white}
                            QDial{background-color:yellow}
                            QTextEdit{background-color: white; color: black;}
                            QPushButton {background-color: yellow; color: black}
                        """
        )

        self.qtab = pqtw.QTabWidget(self)

        self.timer = pqtc.QTimer(self)
        self.timer.setInterval(fps)

        self.tabs = []
        self.timer.timeout.connect(self.update)
        self.timer.start()

    def add_tab(self, name, buttons, layout):
        new_tab = VisualTab(self, buttons, layout)
        self.tabs.append(new_tab)
        self.qtab.addTab(new_tab, name)
        self.qtab.adjustSize()    

    def update(self):
        if self.core.framesync:
            self.timer.stop()
            self.core._sync_guiturn.wait()
            self.timer.start()
            for tab in self.tabs:
                tab.update()
            self.core._sync_guiturn.clear()
            self.core._sync_expturn.set()
        else:
            for tab in self.tabs:
                tab.update()

    def pause(self):
        paused = self.core.pause()
        if paused:
            self.timer.stop()
        else:
            self.timer.start()

    def reset(self, reseed=False):
        self.core.reset(reseed=reseed)
        for tab in self.tabs:
            for visual in tab.visuals:
                visual.reset()

class VisualTab(pqtw.QWidget):
    def __init__(self, mf, buttons, layout):
        super().__init__()
        self.mf = mf
        self.buttons = buttons
        self.visuals = []
        self.init_ui()
        if layout is not None:
            self.layout_frames(layout)

    def init_ui(self):
        self.v_layout = pqtw.QVBoxLayout()
        self.g_layout = pqtw.QGridLayout()

        self.v_layout.addLayout(self.g_layout)
        if self.buttons:
            self.button_layout = self.init_buttons()
            self.v_layout.addLayout(self.button_layout)

        self.setLayout(self.v_layout)

    def init_buttons(self):
        button_layout = pqtw.QGridLayout()

        pause_button = pqtw.QPushButton("Pause", self)
        reset_button = pqtw.QPushButton("Reset", self)
        reseed_button = pqtw.QPushButton("Reseed and Reset", self)

        button_layout.addWidget(pause_button, 0, 1, 1, 1)
        button_layout.addWidget(reset_button, 0, 2, 1, 1)
        button_layout.addWidget(reseed_button, 0, 0, 1, 1)

        pause_button.clicked.connect(lambda: self.mf.pause())
        reset_button.clicked.connect(lambda: self.mf.reset())
        reseed_button.clicked.connect(lambda: self.mf.reset(reseed=True))
        self.button_pos = 3
        return button_layout

    def update(self):
        for visual in self.visuals:
            visual.update()

    def new_visual_frame(self, class_, *args, **kwargs):
        pos = kwargs.pop("pos", (0, 0, 1, 1))
        new_visual_frame = VisualFrame(self, class_, *args, **kwargs)
        self.visuals.append(new_visual_frame)
        self.g_layout.addWidget(new_visual_frame, *pos)
        self.adjustSize()

    def insert_button(self, label, function):
        new_button = pqtw.QPushButton(label, self)
        self.button_layout.addWidget(new_button, 0, self.button_pos, 1, 1)
        new_button.clicked.connect(function)
        self.button_pos += 1

    def layout_frames(self, layout):
        if layout == "square":
            self.new_visual_frame(None, size = (self.mf.core.full_size,
                self.mf.core.full_size), pos = (0,0,6,6))
        elif layout == "pair":
            self.new_visual_frame(None, size = (self.mf.core.full_size,
                self.mf.core.full_size), pos = (0,0,6,6))
            self.new_visual_frame(None, size = (self.mf.core.full_size,
                self.mf.core.full_size), pos = (0,6,6,6))
        elif layout == "longpair":
            self.new_visual_frame(None, size = (self.mf.core.full_size*2,
                self.mf.core.half_size), pos = (0, 0, 3, 12))
            self.new_visual_frame(None, size = (self.mf.core.full_size*2,
                self.mf.core.half_size), pos = (3, 0, 3, 12))
        elif layout == "triple1":
            self.new_visual_frame(None, size = (self.mf.core.full_size,
                self.mf.core.full_size), pos = (0,0,6,6))
            self.new_visual_frame(None, size = (self.mf.core.full_size,
                self.mf.core.half_size), pos = (0,6,3,6))
            self.new_visual_frame(None, size = (self.mf.core.full_size, self.mf.core.half_size), pos = (3,6,3,6))

class VisualFrame(pqtw.QFrame):
    def __init__(self, parent, class_, *args, **kwargs):
        super(VisualFrame, self).__init__(parent)
        self.box = pqtw.QHBoxLayout(self)
        self.index = 0
        size = kwargs.pop("size", (parent.mf.core.full_size, parent.mf.core.full_size))
        self.visual_canvases = {}
        self.setMaximumSize(*size)
        self.visuals = []
        if class_ is not None:
            self.visuals.append(class_(self, *args, **kwargs))
            self.add_widget()
        self.show()

    def insert_visual(self, class_, *args, **kwargs):
        self.visuals.append(class_(self, *args, **kwargs))
        if len(self.visuals) > 1:
            self.box.itemAt(self.index).widget().hide()
        self.index = len(self.visuals) - 1
        self.add_widget()

    def swap_visual(self, index):
        self.box.itemAt(self.index).widget().hide()
        self.index = index
        self.box.itemAt(self.index).widget().show()

    def update(self):
        if self.visuals:
            self.visuals[self.index].iterate()

    def reset(self):
        if self.visuals:
            self.visuals[self.index].reset()

    def add_widget(self):
        if self.visuals[self.index].frontend == "vispy":
            self.box.addWidget(self.visuals[self.index].canvas.native)
        elif self.visuals[self.index].frontend == "matplotlib":
            self.visual_canvases[self.index] = FigureCanvas(self.visuals[self.index].fig)
            self.box.addWidget(self.visual_canvases[self.index])
        else:
            raise NameError("Only vispy and matplotlib currently supported")


class GUI:
    def __init__(self, core, fps):
        core = core
        fps = fps
        if pqtw.QApplication.instance() is None:
            self._app = pqtw.QApplication(sys.argv)
        self._window = GUIWindow(core, fps)

    def fps(self, fps):
        self._window.fps_signal.emit(1000 // fps)

    def quit(self):
        self._window.close()

    def reset(self, reseed=False):
        self._window.reset_signal.emit(reseed)

    def add_visual_frame(self, tab, class_, *args, **kwargs):
        if threading.current_thread().name == "cli":
            print("Adding frames from CLI unsupported, add a new tab instead")
        else:
            self._window.mf.tabs[tab].new_visual_frame(class_, *args, **kwargs)
            self._window.mf.qtab.adjustSize()
            self._window.mf.setMinimumSize(self._window.mf.qtab.size())

    def add_tab(self, name = "tab", buttons = True, layout = None):
        if threading.current_thread().name == "cli":
            if layout is None:
                print("Must assign a standard layout from CLI")
            else:
                self._window.add_tab_signal.emit(name, buttons, layout)
        else:        
            self._window.mf.add_tab(name, buttons, layout)

    def insert_visual(self, tab, index, class_, *args, **kwargs):
        if threading.current_thread().name == "cli":
            self._window.insert_visual_signal.emit(tab, index, class_, args, kwargs)
        else:
            self._window.mf.tabs[tab].visuals[index].insert_visual(class_, *args, **kwargs)

    def swap_visual(self, tab, w_index, v_index):
        if threading.current_thread().name == "cli":
            self._window.swap_visual_signal.emit(tab, w_index, v_index)
        else:    
            self._window.mf.tabs[tab].visuals[w_index].swap_visual(v_index)

    def _begin(self):
        self._app.exec_()
