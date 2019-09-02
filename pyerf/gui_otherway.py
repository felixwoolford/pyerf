import sys
import threading

import PyQt5.QtWidgets as pqtw
import PyQt5.QtCore as pqtc
from PyQt5.QtGui import QSurfaceFormat
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class GUIWindow(pqtw.QMainWindow):
    #All custom signals are handled by GUIWindow
    fps_signal = pqtc.pyqtSignal(int)
    reset_signal = pqtc.pyqtSignal(bool)
    swap_visual_signal = pqtc.pyqtSignal(str, int, object)

    def __init__(self, core, fps):
        super().__init__(None, pqtc.Qt.WindowStaysOnTopHint)
        self.mf = MainFrame(self, core, fps)
        self.setCentralWidget(self.mf)
        self.mf.setMinimumSize(self.mf.qtab.size())
        self.move(200, 0)
        self.setWindowTitle(core.title)
        self.adjustSize()
        self.show()
        self.fps_signal.connect(lambda fps: self.set_fps(fps))
        self.reset_signal.connect(lambda reseed: self.mf.sim_tab.reset(reseed))
        # TODO - this is hacked because i'll sort out this tab thing later
        self.swap_visual_signal.connect(
            lambda x, w_index, v: self.mf.sim_tab.visuals[w_index].insert_visual(v)
        )

    def set_fps(self, fps):
        self.mf.timer.setInterval(fps)


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

        self.sim_tab = VisualTab(self, self.core)
        self.data_tab = VisualTab(self, self.core)
        self.qtab.addTab(self.sim_tab, "Sim")
        self.qtab.addTab(self.data_tab, "Data")
        self.qtab.adjustSize()
        self.timer.timeout.connect(self.update)
        self.timer.start()

    def update(self):
        if self.core.framesync:
            self.timer.stop()
            self.core._sync_guiturn.wait()
            self.timer.start()
            self.sim_tab.update()
            self.data_tab.update()
            self.core._sync_guiturn.clear()
            self.core._sync_expturn.set()
        else:
            self.sim_tab.update()


class VisualTab(pqtw.QWidget):
    def __init__(self, mf, core):
        super().__init__()
        self.mf = mf
        self.core = core
        self.visuals = []
        self.init_ui()

    def init_ui(self):
        self.v_layout = pqtw.QVBoxLayout()
        self.g_layout = pqtw.QGridLayout()
        self.button_layout = self.init_buttons()

        self.v_layout.addLayout(self.g_layout)
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

        pause_button.clicked.connect(lambda: self.pause())
        reset_button.clicked.connect(lambda: self.reset())
        reseed_button.clicked.connect(lambda: self.reset(reseed=True))
        self.button_pos = 3
        return button_layout

    def reset(self, reseed=False):
        self.core.reset(reseed=reseed)
        for visual in self.visuals:
            visual.reset()

    def pause(self):
        paused = self.core.pause()
        if paused:
            self.mf.timer.stop()
        else:
            self.mf.timer.start()

    def update(self):
        for visual in self.visuals:
            visual.update()

    def new_visual_frame(self, visual, size, pos):
        new_visual_frame = VisualFrame(self, visual, size)
        self.visuals.append(new_visual_frame)
        self.g_layout.addWidget(new_visual_frame, *pos)
        self.adjustSize()

    def insert_button(self, label, function):
        new_button = pqtw.QPushButton(label, self)
        self.button_layout.addWidget(new_button, 0, self.button_pos, 1, 1)
        new_button.clicked.connect(function)
        self.button_pos += 1


class VisualFrame(pqtw.QFrame):
    def __init__(self, parent, visual, size):
        super(VisualFrame, self).__init__(parent)
        self.box = pqtw.QHBoxLayout(self)
        self.setMaximumSize(*size)
        self._aw(visual)
        self.show()

    def insert_visual(self, visual):
        if self.box.count() > 0:
            # self.box.itemAt(0).widget().hide()
            self.box.removeWidget(self.box.itemAt(0).widget())
            self.box.update()
        self._aw(visual)

    def swap_visual(self, visual):
        self.box.itemAt(self.index).widget().hide()
        self.index = index
        self.box.itemAt(self.index).widget().show()

    def update(self):
        self.visual.iterate()

    def reset(self):
        self.visual.reset()

    def _aw(self, visual):
        self.visual = visual
        if self.visual.frontend == "vispy":
            self.box.addWidget(self.visual.canvas.native)
        elif self.visual.frontend == "matplotlib":
            self.box.addWidget(self.visual.fig)
        else:
            raise NameError("Only vispy and matplotlib currently supported")


class GUI:
    def __init__(self, core, fps):
        self.core = core
        if pqtw.QApplication.instance() is None:
            self._app = pqtw.QApplication(sys.argv)
        self._window = GUIWindow(core, fps)
        self._visuals_dict = {}

    def fps(self, fps):
        self._window.fps_signal.emit(1000 // fps)

    def quit(self):
        self._window.close()

    def reset(self, reseed=False):
        self._window.reset_signal.emit(reseed)


    def add_visual_frame(self, type, name, class_, *args, **kwargs):
        if threading.current_thread().name == "cli":
            print("This function must not be called from CLI")
            return
        #TODO
        if type == "sim":
            size = kwargs.pop("size", (self.core.full_size, self.core.full_size))
            pos = kwargs.pop("pos", (0, 0, 1, 1))
            self._visuals_dict[name] = class_(self._window, *args,**kwargs)
            self._window.mf.sim_tab.new_visual_frame(self._visuals_dict[name], size, pos)
        elif type == "data":
            pass
        else:
            raise NameError("Unknown type: {0}".format(type))
        self._window.mf.qtab.adjustSize()
        self._window.mf.setMinimumSize(self._window.mf.qtab.size())

    def insert_visual(self, type, index, name, class_, *args, **kwargs):
        # TODO
        if type == "sim":
            self._visuals_dict[name] = class_(self._window, *args,**kwargs)
            self._window.mf.sim_tab.visuals[index].insert_visual(self._visuals_dict[name])
        elif type == "data":
            pass
        else:
            raise NameError("Unknown type: {0}".format(type))

    def swap_visual(self, type, w_index, name):
        if threading.current_thread().name == "cli":
            self._window.swap_visual_signal.emit(type, w_index, self._visuals_dict[name])
        # TODO    
        elif type == "sim":
            self._window.mf.sim_tab.visuals[w_index].insert_visual(self._visuals_dict[name])
        elif type == "data":
            pass
        else:
            raise NameError("Unknown type: {0}".format(type))

    def _begin(self):
        self._app.exec_()
