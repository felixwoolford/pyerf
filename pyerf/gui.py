# seems to be some problems with swapping in MF and inserting from cli
import sys
import threading

import PyQt5.QtWidgets as pqtw
import PyQt5.QtCore as pqtc
from PyQt5.QtGui import QSurfaceFormat
import numpy as np

STYLESHEET = """             QFrame{background-color: black; color: white}
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

class GUIWindow(pqtw.QMainWindow):
    # all custom signals are handled by GUIWindow
    fps_signal = pqtc.pyqtSignal(int)
    reset_signal = pqtc.pyqtSignal(bool)
    add_tab_signal = pqtc.pyqtSignal(str, bool, str)
    insert_visual_signal = pqtc.pyqtSignal(int, int, int, object, object, object)
    add_slave_signal = pqtc.pyqtSignal(object)
    swap_visual_signal = pqtc.pyqtSignal(int, int, int, int)

    def __init__(self, core, fps):
        super().__init__()
        self.mf = MainFrame(self, core, fps)
        self.setCentralWidget(self.mf)
        self.setWindowTitle(core.title)
        # self.setAttribute(pqtc.Qt.WA_TranslucentBackground, True);
        self.fps_signal.connect(self.mf.timer.setInterval)
        self.reset_signal.connect(self.mf.reset)
        self.add_tab_signal.connect(self.mf.add_tab)
        self.insert_visual_signal.connect(self.insert_visual) 
        self.swap_visual_signal.connect(self.swap_visual)
        self.add_slave_signal.connect(self.add_slave)
        self.adjustSize()
        self.show()

    def swap_visual(self, tab, w_index, v_index, window):
        if window == 0:
            self.mf.tabs[tab].frames[w_index].swap_visual(v_index)
        else:
            w = self.mf.slave_windows[window - 1].frame 
            if tab != -1:
                w.tabs[tab].frames[w_index].swap_visual(v_index)
            else:
                w.swap_visual(v_index)

    def insert_visual(self, window, tab, index, class_, *args, **kwargs):
        if window == 0:
            self.mf.tabs[tab].frames[index].insert_visual(class_, *args, **kwargs)
        else:
            w = self.mf.slave_windows[window - 1] 
            if tab != -1:
                w.tabs[tab].frames[index].insert_visual(class_, *args, **kwargs)
            else:
                w.new_visual_frame(class_, *args, **kwargs)
    
    def add_slave(self, name):
        self.mf.add_slave(name)

    def closeEvent(self, event):
        for window in self.mf.slave_windows:
            window.close()
        super().closeEvent(event)

class MainFrame(pqtw.QFrame):
    def __init__(self, parent, core, fps):
        super().__init__(parent)
        self.core = core
        self.setAutoFillBackground(True)
        # self.setStyleSheet(STYLESHEET)
        layout = pqtw.QGridLayout()
        self.qtab = pqtw.QTabWidget(self)
        layout.addWidget(self.qtab, 0,0,0,0)
        self.setLayout(layout)
        self.qtab.currentChanged.connect(self.tab_changed)

        self.timer = pqtc.QTimer(self)
        self.timer.setInterval(fps)

        self.tabs = []
        self.slave_windows = []

        self.timer.timeout.connect(self.update)
        self.timer.start()

    def add_slave(self, name):
        window = pqtw.QMainWindow()
        # window.setAttribute(pqtc.Qt.WA_TranslucentBackground, True);
        self.slave_windows.append(window)
        window.frame = SlaveFrame(window, self)
        window.setWindowTitle(name)
        window.setCentralWidget(window.frame)
        window.show()
        
    def add_tab(self, name, buttons, layout):
        new_tab = VisualTab(self, self, buttons, layout)
        self.tabs.append(new_tab)
        self.qtab.addTab(new_tab, name)

    def tab_changed(self, tab):
        for frame in self.tabs[tab].frames:
            if len(frame.visuals) > 0 and frame.visuals[frame.index].frontend == "matplotlib":
                frame.visuals[frame.index].update_triggered()

    def update(self):
        def loop_updates():
            for tab in self.tabs:
                tab.update()
            for slave in self.slave_windows:
                slave.frame.update()
                
        if self.core._gui_reset_trigger:
            for tab in self.tabs:
                tab.reset()
            for slave in self.slave_windows:
                slave.frame.reset()
            self.core._gui_reset_trigger = False
        if self.core.framesync:
            self.timer.stop()
            self.core._sync_guiturn.wait()
            self.timer.start()
            loop_updates()
            self.core._sync_guiturn.clear()
            self.core._sync_expturn.set()
        else:
            loop_updates()

    def pause(self):
        paused = self.core.pause()
        if paused:
            self.timer.stop()
        else:
            self.timer.start()

    def reset(self, reseed=False):
        self.core.reset(reseed=reseed)


class SlaveFrame(pqtw.QFrame):
    def __init__(self, parent_window, mf):
        super().__init__(parent_window)
        # self.setStyleSheet(STYLESHEET)
        self.mf = mf
        self.layout = pqtw.QGridLayout()
        self.qtab = pqtw.QTabWidget(self)
        self.layout.addWidget(self.qtab, 0,0,0,0)
        self.setLayout(self.layout)
        self.qtab.currentChanged.connect(self.tab_changed)
        self.visual = None
        self.tabs = []

    def add_tab(self, name, buttons = False, layout = "square"):
        if self.visual is not None:
            self.visual.setParent(None)
            self.visual = None
        new_tab = VisualTab(self, self.mf, buttons, layout)
        self.tabs.append(new_tab)
        self.qtab.addTab(new_tab, name)

    def tab_changed(self, tab):
        for frame in self.tabs[tab].frames:
            if len(frame.visuals) > 0 and frame.visuals[frame.index].frontend == "matplotlib":
                frame.visuals[frame.index].update_triggered()

    def new_visual_frame(self, class_, *args, **kwargs):
        if self.qtab is not None:
            self.layout.removeWidget(self.qtab)
            self.qtab.setParent(None)
            self.qtab = None
        if self.visual is not None:
            self.visual.insert_visual(class_, *args, **kwargs)
        else:
            self.visual = VisualFrame(self, class_, *args, **kwargs)
            self.layout.addWidget(self.visual)

    def swap_visual(self, index):
        self.visual.swap_visual(index)
    
    def update(self):
        if self.visual is not None:
            self.visual.update()
        else:
            for tab in self.tabs:
                tab.update()

    def reset(self):
        if self.visual is not None:
            self.visual.reset() 
        else:
            for tab in self.tabs:
                tab.reset()

class VisualTab(pqtw.QWidget):
    def __init__(self, parent, mf, buttons, layout):
        super().__init__(parent)
        self.mf = mf
        self.buttons = buttons
        self.frames = []
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
        for frame in self.frames:
            frame.update()

    def reset(self):
        for frame in self.frames:
            frame.reset()

    def new_visual_frame(self, class_, *args, **kwargs):
        pos = kwargs.pop("pos", (0, 0, 1, 1))
        new_visual_frame = VisualFrame(self, class_, *args, **kwargs)
        self.frames.append(new_visual_frame)
        self.g_layout.addWidget(new_visual_frame, *pos)
        # self.adjustSize()

    def insert_button(self, label, function):
        new_button = pqtw.QPushButton(label, self)
        self.button_layout.addWidget(new_button, 0, self.button_pos, 1, 1)
        new_button.clicked.connect(function)
        self.button_pos += 1

    def layout_frames(self, layout):
        if layout == "square":
            self.new_visual_frame(None, pos = (0,0,6,6))
        elif layout == "pair":
            self.new_visual_frame(None, pos = (0,0,6,6))
            self.new_visual_frame(None, pos = (6,0,6,6))
        elif layout == "pairh":
            self.new_visual_frame(None, pos = (0,0,6,6))
            self.new_visual_frame(None, pos = (0,6,6,6))
        elif layout == "triple1":
            self.new_visual_frame(None, pos = (0,0,6,12))
            self.new_visual_frame(None, pos = (6,0,3,6))
            self.new_visual_frame(None, pos = (6,6,3,6))
        else:
            names = [   'square', 
                        'pair', 
                        'pairh', 
                        'triple1',
                    ]
            raise NameError("Valid layout names: {0}".format(names))


class VisualFrame(pqtw.QFrame):
    def __init__(self, parent, class_, *args, **kwargs):
        super(VisualFrame, self).__init__(parent)
        self.box = pqtw.QHBoxLayout(self)
     
        self.index = 0
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
        # self.adjustSize()

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
            self.box.addWidget(self.visuals[self.index].canvas)
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

    def add_tab(self, name = "tab", buttons = True, layout = None):
        if threading.current_thread().name == "cli":
            if layout is None:
                print("Must assign a standard layout from CLI")
            else:
                self._window.add_tab_signal.emit(name, buttons, layout)
        else:        
            self._window.mf.add_tab(name, buttons, layout)

    def add_slave(self, name = "Slave Window"):
        if threading.current_thread().name == "cli":
            self._window.add_slave_signal.emit(name)
        else:
            self._window.mf.add_slave(name)

    def insert_visual(self, tab, index, class_, *args, window = 0, **kwargs):
        if threading.current_thread().name == "cli":
            self._window.insert_visual_signal.emit(window, tab, index, class_, args, kwargs)
        else:
            if window == 0:
                self._window.mf.tabs[tab].frames[index].insert_visual(class_, *args, **kwargs)
            else:
                w = self._window.mf.slave_windows[window - 1].frame 
                if tab != -1:
                    w.tabs[tab].frames[index].insert_visual(class_, *args, **kwargs)
                else:
                    w.new_visual_frame(class_, *args, **kwargs)
        self._window.adjustSize()

    def swap_visual(self, tab, w_index, v_index, window = 0):
        if threading.current_thread().name == "cli":
            self._window.swap_visual_signal.emit(tab, w_index, v_index, window)
        else:    
            if window == 0:
                self._window.mf.tabs[tab].frames[w_index].swap_visual(v_index)
            else:
                w = self._window.mf.slave_windows[window - 1].frame 
                if tab != -1:
                    w.tabs[tab].frames[w_index].swap_visual(v_index)
                else:
                    w.swap_visual(v_index)

    def get_timer(self):
        return self._window.mf.timer

    def trigger_update(self):
        mf = self._window.mf
        mf.tab_changed(mf.qtab.currentIndex())

    def _begin(self):
        self._app.exec_()
