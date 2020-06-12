class Simulation:
    def __init__(self, environment = None, tracking = False):
        self.tracked_variables = {}
        self.environment = environment
        self.robots = []
        self.i = 0
        self.tracking = tracking

    # This should be overridden for more complex sims
    def initialize(self):
        self.i = 0
        self.initialize_entities()

    def initialize_entities(self):
        if self.environment is not None:
            self.environment.initialize()
        for robot in self.robots:
            robot.initialize()

    def update_track_hist(self, i):
        if self.environment is not None:
            self.environment.update_track_hist(i)
        for robot in self.robots:
            robot.update_track_hist(i)
        for var, hist in self.tracked_variables.items():
            hist[0].append(i)
            hist[1].append(vars(self)[var])

    def track_variable(self, var):
        v = vars(self)[var]
        self.tracked_variables[v] = [[],[]]

    def untrack_variable(self, var):
        del self.tracked_variables[vars(self)[var]]

    # iterate generic background stuff
    def _iterate_bookkeeping(self):
        if self.tracking:
            self.i += 1
            self.update_track_hist(self.i)
