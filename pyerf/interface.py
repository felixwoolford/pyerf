import IPython


class CLI:
    def __init__(self, core):
        self.core = core
    
    # set word in between experiment iterations, should make behaviour more predictable
    def safe_set(self, target, var, val):
        with self.core.iteration_lock:
            vars(target)[var] = val
    
    # call function in between experiment iterations, should make behaviour more predictable
    def safe(self, func):
        with self.core.iteration_lock:
            func()

    def _run(self):
        i = self
        c = self.core
        g = self.core.gui
        e = self.core.experiment

        IPython.terminal.embed.embed()