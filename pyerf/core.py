# implement interface!
# might be nice to just set up something so that vispy isn't assumed
# implement data tab
# switch the tab hlayout to a grid so that i can have fun layouts
from threading import Thread, Lock, Condition, Event
import time

import numpy as np

import gui
# import controller
# import robot
# import environment
# import cli

class Core:
    def __init__(self, title="Experiment", mode = 'visual', speed = 1000, fps = 60,
            framesync = True):
        self.title = title
        self.mode = mode
        self.visual_size = 800 #TODO
        self.seed = np.random.randint(2**32)
        np.random.seed(self.seed)

        self.experiment = None
        self.interface = None #TODO this should be standard
        if self.mode == 'visual':
            self.running = False
            self.paused = False
            self.framesync = framesync
            self.pause_condition = Condition(Lock())
            self.sync_guiturn = Event()
            self.sync_guiturn.set()
            self.sync_expturn = Event()
            self.speed = 1/speed 
            self.fps = 1000//fps

            self.gui = gui.GUI(self, self.fps) 
        #lock to ensure that write interactions only occur in between iterations      
        #TODO this will have to be acquired before any rpyc stuff or else deadlocks?
        self.iteration_lock = Lock()

    def run_timed(self):
        while True:
            self._initialize()
            self.running = True
            while self.running:
                if self.framesync:
                    self.sync_expturn.wait()
                with self.pause_condition:
                    while self.paused:
                        self.pause_condition.wait()
                    self.iteration_lock.acquire()
                    self.experiment.iterate()    
                    self.iteration_lock.release()               
                if self.framesync:
                    self.sync_expturn.clear()
                    self.sync_guiturn.set()
                else:    
                    time.sleep(self.speed)



    def run_untimed(self):
        self._initialize()
        self.experiment.run()
        
    def _initialize(self):
        np.random.seed(self.seed)
        self.experiment.initialize()
            
    def pause(self):
        if not self.paused:
            self.paused = True
            self.pause_condition.acquire()
        else:
            self.paused = False
            self.pause_condition.notify()
            self.pause_condition.release()

    def run(self):
        assert self.experiment != None
        # assert self.interface != None
        # self.interface_thread = Thread(target=self.interface.run, daemon=True)
        # self.interface_thread.start()
        if self.mode == 'visual':
            self.experiment_thread = Thread(target=self.run_timed, daemon=True)
            self.experiment_thread.start()
            self.gui.begin()
        else:
            self.run_untimed()
            
