class Experiment:
    def __init__(self, ):
        self.sim = None

    def iterate(self):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError
    
    def initialize(self):
        raise NotImplementedError
