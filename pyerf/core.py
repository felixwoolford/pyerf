from threading import Thread, Lock, Condition
import time

import numpy as np

import gui
import controller
import robot
import environment
import cli

class Core(Thread):
    def __init__(self, title="Experiment", mode = 'visual', speed = 1000, fps = 60,):
        super().__init__()
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
            self.pause_cond = Condition(Lock())
            self.speed = 1/speed 
            self.fps = 1000/fps
            self.gui = gui.GUI(fps) #TODO one day be nice to have an option for others
              
        #lock to ensure that write interactions only occur in between iterations      
        #TODO this will have to be acquired before any rpyc stuff or else deadlocks?
        self.iteration_lock = Lock()

    def run_timed(self):
        self._initialize()
        while self.running:
            with self.pause_cond:
                while self.paused:
                    self.pause_cond.wait()
                self.iteration_lock.acquire()
                self.experiment.iterate()    
                self.iteration_lock.release()
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
            self.pause_cond.acquire()
        else:
            self.paused = False
            self.pause_cond.notify()
            self.pause_cond.release()

    def run(self):
        assert self.experiment != None
        if self.mode == 'visual':
            assert self.interface != None
            while True:
                self.run_timed()
        else:
            self.run_untimed()
            
