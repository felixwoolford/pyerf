from threading import Thread, Lock, Condition, Event
import time

import numpy as np

from .gui import GUI
from .interface import CLI


class Core:
    def __init__(self, experiment, **kwargs):
        self.title = kwargs.get("title", "Experiment")
        self._mode = kwargs.get("mode", "visual")
        self.seed = kwargs.get("seed", np.random.randint(2**32))
        np.random.seed(self.seed)
        self._kill = False

        self.experiment = experiment
        self._initialize()
        self.interface = CLI(self)
        if self._mode == "visual":
            self._is_reset = False
            self._paused = False
            self.framesync = kwargs.get("framesync", True)
            self._pause_condition = Condition(Lock())
            self._sync_guiturn = Event()
            self._sync_guiturn.set()
            self._sync_expturn = Event()
            self._speed = 1 / kwargs.get("speed", 1000)
            self._fps = 1000 // kwargs.get("fps", 60)
            self.gui = GUI(self, self._fps)
            self._gui_reset_trigger = False

        # lock to ensure that write interactions only occur in between iterations
        self._iteration_lock = Lock()

    def _run_timed(self):
        while True:
            if self._kill:
                return
            self._is_reset = False
            self._gui_reset_trigger = True
            # Condition is set false when reset is called, continuing the outer loop
            while not self._is_reset:
                if self.framesync:
                    # Ensure condition is cleared even if framesync cancelled
                    clearsync = True
                    self._sync_expturn.wait()
                else:
                    clearsync = False
                # Handle pause from interfaces
                with self._pause_condition:
                    while self._paused:
                        self._pause_condition.wait()
                    with self._iteration_lock:
                        self.experiment._iterate()

                if clearsync:
                    self._sync_expturn.clear()
                    self._sync_guiturn.set()
                # If unsynced use own timer 
                else:
                    time.sleep(self._speed)
            self._initialize()

    def _run_untimed(self):
        self.experiment.run()

    def _initialize(self):
        np.random.seed(self.seed)
        self.experiment._initialize()

    def reset(self, reseed=False):
        if reseed:
            self.seed = np.random.randint(2**32)
        # Causes continuation of outer loop of _run_timed
        self._is_reset = True

    def speed(self, speed):
        self._speed = 1/speed

    def pause(self):
        if not self._paused:
            self._paused = True
            self._pause_condition.acquire()
        else:
            self._paused = False
            self._pause_condition.notify()
            self._pause_condition.release()
        return self._paused

    def run(self):
        assert self.experiment != None
        if self._mode != "optimal":
            self.interface_thread = Thread(target=self.interface._run, name="cli", daemon=True)
            self.interface_thread.start()
        if self._mode == "visual":
            self.gui.show_windows()
            self.experiment_thread = Thread(target=self._run_timed, daemon=True)
            self.experiment_thread.start()
            # Start up the GUI app - end of the line for the main thread
            self.gui._begin()
        else:
            self._run_untimed()
