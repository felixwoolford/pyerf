class Robot:
    def __init__(self):
        self.tracked_variables = {}

    def initialize(self):              
        raise NotImplementedError

    def update_track_hist(self):
        for var, hist in self.tracked_variables.items():
            hist.append(vars(self)[var])

    def track_variable(self, var):
        v = vars(self)[var]
        self.tracked_variables[v] = []

    def untrack_variable(self, var):
        del self.tracked_variables[vars(self)[var]]
