class Experiment:
    def __init__(self, simulation = None):
        self.simulation = simulation

    def _iterate(self):
        self.iterate()
        self.simulation._iterate_bookkeeping()

    def _initialize(self):
        self.initialize()
    
    # if called directly, consider implementing elements from _iterate
    def iterate(self):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError
    
    def initialize(self):
        raise NotImplementedError
