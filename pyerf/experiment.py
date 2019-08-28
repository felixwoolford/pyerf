import numpy


class Experiment:
    def __init__(self, core):
        self.sim = None

    def iterate(self):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError
    
    def initialize(self):
        raise NotImplementedError
