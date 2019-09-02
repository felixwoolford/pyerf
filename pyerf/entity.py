class Entity:
    def __init__(self):
        self.tracked_variables = {}

    def initialize(self):              
        raise NotImplementedError

    # generally should not be called directly, unless from an overriding method with eg. a filter
    def update_track_hist(self, i):
        for var, hist in self.tracked_variables.items():
            hist[0].append(i)
            hist[1].append(vars(self)[var])

    def track_variable(self, var):
        v = vars(self)[var]
        self.tracked_variables[v] = [[],[]]

    def untrack_variable(self, var):
        del self.tracked_variables[vars(self)[var]]
