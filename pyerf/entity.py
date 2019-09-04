class Entity:
    def __init__(self):
        self.tracked_variables = {}

    def initialize(self):              
        raise NotImplementedError

    # generally should not be called directly
    def update_track_hist(self, i):
        for var, hist in self.tracked_variables.items():
            hist[0].append(i)
            hist[1].append(vars(self)[var])

    def track_variable(self, var):
        self.tracked_variables[var] = [[],[]]
        self.update_track_hist(0) # HACK

    def untrack_variable(self, var):
        del self.tracked_variables[var]
