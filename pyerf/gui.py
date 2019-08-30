import sys
from threading import Thread

import PyQt5.QtWidgets as pqtw
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QSurfaceFormat
import numpy as np


class GUIWindow(pqtw.QMainWindow):
    def __init__(self, core, fps):
        super().__init__()
        self.mf = MainFrame(self, core, fps)
        self.setCentralWidget(self.mf)
        self.mf.setMinimumSize(self.mf.qtab.size())
        self.move(200, 0)
        self.setWindowTitle(core.title)
        self.adjustSize()
        self.show()


class MainFrame(pqtw.QFrame):
    def __init__(self, parent, core, fps):
        super().__init__(parent)
        self.core = core
        self.setAutoFillBackground(True)

        self.setStyleSheet(
            """  QFrame{background-color: black;color: white}
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
                                QComboBox{background-color: black; color: white}
                                QLineEdit{background-color: black; color: white}
                                QDial{background-color:yellow}
                                QTextEdit{background-color: white; color: black;}
				QPushButton {background-color: yellow; color: black}
                            """
        )

        self.qtab = pqtw.QTabWidget(self)

        self.timer = QTimer(self)
        self.timer.setInterval(fps)

        self.sim_tab = SimTab(self, self.core)
        # self.data_tab = DataTab(self)
        self.qtab.addTab(self.sim_tab, "Sim")
        # self.qtab.addTab(self.data_tab,"Data")
        self.qtab.adjustSize()
        self.timer.timeout.connect(self.update)
        self.timer.start()

    def update(self):
        if self.core.framesync:
            self.timer.stop()
            self.core.sync_guiturn.wait()
            self.timer.start()
        self.sim_tab.update()
        # self.data_tab.update()
        if self.core.framesync:
            self.core.sync_guiturn.clear()
            self.core.sync_expturn.set()


class SimTab(pqtw.QWidget):
    def __init__(self, mf, core):
        super().__init__()
        self.mf = mf
        self.core = core
        # self.world_vispy = SimWidget(self, self.sim)
        # self.network_vispy = VispyNetwork(self, self.sim)
        self.visuals = []
        self.init_ui()

    def init_ui(self):
        self.v_layout = pqtw.QVBoxLayout()
        self.h_layout = pqtw.QHBoxLayout()
        self.button_layout = self.init_buttons()

        # TODO
        # self.h_layout.addWidget(self.world_vispy)
        # h_layout.addWidget(self.network_vispy)

        self.v_layout.addLayout(self.h_layout)
        self.v_layout.addLayout(self.button_layout)

        self.setLayout(self.v_layout)

    def init_buttons(self):
        button_layout = pqtw.QGridLayout()

        pause_button = pqtw.QPushButton("Pause Light", self)
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
        if reseed:
            self.core.seed = np.random.randint(2 ** 32)
        self.core.running = False
        for visual in self.visuals:
            visual.reset()

    def pause(self):
        self.core.pause()
        if self.core.paused:
            self.mf.timer.stop()
        else:
            self.mf.timer.start()

    def update(self):
        for visual in self.visuals:
            visual.update()

    def insert_visual(self, class_, *args, **kwargs):
        new_visual = SimWidget(self, class_, *args, **kwargs)
        self.visuals.append(new_visual)
        self.h_layout.addWidget(new_visual)
        self.adjustSize()

    def insert_button(self, label, function):
        new_button = pqtw.QPushButton(label, self)
        self.button_layout.addWidget(new_button, 0, self.button_pos, 1, 1)
        new_button.clicked.connect(function)
        self.button_pos += 1


class SimWidget(pqtw.QWidget):
    def __init__(self, parent, class_, *args, **kwargs):
        super(SimWidget, self).__init__(parent)
        box = pqtw.QHBoxLayout(self)
        self.setMinimumSize(parent.core.visual_size, parent.core.visual_size)
        self.visual = class_(self, *args, **kwargs)
        box.addWidget(self.visual.canvas.native)
        self.show()

    def update(self):
        self.visual.iterate()

    def reset(self):
        self.visual.reset()


class GUI:
    def __init__(self, core, fps):
        core = core
        fps = fps
        if pqtw.QApplication.instance() is None:
            self.app = pqtw.QApplication(sys.argv)
        self.window = GUIWindow(core, fps)

    def add_sim_visual(self, class_, *args, **kwargs):
        self.window.mf.sim_tab.insert_visual(class_, *args, **kwargs)
        self.window.mf.qtab.adjustSize()
        self.window.mf.setMinimumSize(self.window.mf.qtab.size())

    def begin(self):
        self.app.exec_()
