from threading import Thread, Lock, Condition, Event
import time
import numpy as np

from .gui import GUI
from .interface import CLI


class Core:
    def __init__(self, experiment, **kwargs):
        self.title = kwargs.get("title", "Experiment")
        self._mode = kwargs.get("mode", "visual")
        mode_ops = ["visual", "optimal", "safe", "unsafe"]
        if self._mode not in mode_ops:
            print("mode should be in {}".format(mode_ops))
            self._mode = "safe"
        self.seed = kwargs.get("seed", np.random.randint(2**32))
        np.random.seed(self.seed)
        self._kill = False
        self._unsynced_wait = False
        self._unsynced_wait_ready = False

        self.experiment = experiment
        if self._mode != "optimal":
            self.interface = CLI(self)
        if self._mode in ["visual", "safe"]:
            self._initialize()
            self._is_reset = False
            self._paused = False
            self._pause_condition = Condition(Lock())
            self.framesync = kwargs.get("framesync", False)
            self._speed = 1 / kwargs.get("speed", 1000)
            self.time = time.time()
            # lock to ensure that write interactions only occur in between iterations
            self._iteration_lock = Lock()
        if self._mode in ["visual"]:
            self._sync_guiturn = Event()
            self._sync_guiturn.set()
            self._sync_expturn = Event()
            self._fps = 1000 // kwargs.get("fps", 60)
            self.gui = GUI(self, self._fps)
            self._gui_reset_trigger = False


    def _run_timed(self):
        while True:
            self._is_reset = False
            self._gui_reset_trigger = True
            # Condition is set false when reset is called, continuing the outer loop
            while not self._is_reset:
                if self.framesync or not self._sync_expturn.is_set():
                    self._sync_guiturn.set()
                    self._sync_expturn.wait()
                    if self.framesync:
                        self._sync_expturn.clear()

                # Handle pause from interfaces
                with self._pause_condition:
                    while self._paused:
                        self._pause_condition.wait()
                    with self._iteration_lock:
                        self.experiment._iterate()

                # If unsynced use own timer 
                if not self.framesync:
                    time_diff = time.time() - self.time
                    # If the code is running slower than the timer, don't force the wait
                    if time_diff < self._speed:
                        time.sleep(self._speed - time_diff)
                    self.time = time.time()
            if self._kill:
                return
            else: 
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
        assert self.experiment is not None
        if self._mode != "optimal":
            self.interface_thread = Thread(target=self.interface._run, name="cli", daemon=True)
            self.interface_thread.start()
        if self._mode == "visual":
            self.gui.show_windows()
            self.experiment_thread = Thread(target=self._run_timed, daemon=True)
            self.experiment_thread.start()
            # Start up the GUI app - end of the line for the main thread
            self.gui._begin()
        elif self._mode == "safe":
            self._run_timed()
            while not self._kill:
                time.sleep(1)
        else:
            self._run_untimed()
