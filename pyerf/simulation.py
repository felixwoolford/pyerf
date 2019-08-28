class Simulation:
    def __init__(self):
        self.tracked_variables = {}
        self.environment = None
        self.robots = []

    # This should be overridden for more complex sims
    def initialize(self):              
        self.initialize_robots()

    def initialize_robots(self):
        self.environment.initialize()
        for robot in self.robots:
            robot.initialize

    def update_track_hist(self):
        for var, hist in self.tracked_variables.items():
            hist.append(vars(self)[var])

    def track_variable(self, var):
        v = vars(self)[var]
        self.tracked_variables[v] = []

    def untrack_variable(self, var):
        del self.tracked_variables[vars(self)[var]]
