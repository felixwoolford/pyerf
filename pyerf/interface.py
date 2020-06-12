import os
from IPython import terminal
import asyncio

class CLI:
    def __init__(self, core):
        self.core = core
    
    # set var in between experiment iterations, should make behaviour more predictable
    def safe_set(self, target, var, val):
        with self.core._iteration_lock:
            vars(target)[var] = val
    
    # call function in between experiment iterations, should make behaviour more predictable
    def safe(self, func):
        with self.core._iteration_lock:
            func()

    def _run(self):
        i = self
        c = self.core
        if c._mode == "visual":
            g = self.core.gui
            p = g.pause
            r = g.reset
        e = self.core.experiment

        asyncio.set_event_loop(asyncio.new_event_loop())
        terminal.embed.embed()

    def q(self):
        if self.core._mode == "visual":
            self.core.gui.quit()
        self.core._kill = True
        self.core.reset()
        os._exit(1)
