class Experiment:
    def __init__(self, simulation = None, trial_length = -1):
        self.simulation = simulation
        self.trial_length = trial_length
    
    def _iterate(self):
        self.iterate()
        self.simulation._iterate_bookkeeping()

    def _initialize(self):
        self.initialize()
    
    # if overridden and called directly, consider implementing elements from _iterate
    def iterate(self):
        self.simulation.iterate()

    def run(self):
        for _ in range(self.trial_length):
            self.iterate()

    def initialize(self):
        self.simulation.__init__()
