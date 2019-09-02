import IPython


class CLI:
    def __init__(self, core):
        self.core = core
    
    def safe_set(self, target, var, val):
        with self.core.iteration_lock:
            vars(target)[var] = val
        
    def safe(self, func):
        with self.core.iteration_lock:
            func()

    def speed(self, speed):
        self.core.speed = 1/speed

    def run(self):
        i = self
        c = self.core
        g = self.core.gui
        e = self.core.experiment

        IPython.terminal.embed.embed()
