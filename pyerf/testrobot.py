from vispy import scene, color
import numpy as np
from dashnet.network import Bundle as Bundle

import core
import experiment
import entity
import simulation
import visuals


class SensorimotorOptions:
    def __init__(self):

        self.SENSES = {"ORANGE": 0, "PURPLE": 1, "BLACK": 2, "WHITE": 3}

        self.ACTIONS = {
            "MZ": lambda x: False,
            "ML": lambda x: x._move(np.array([-1, 0])),
            "MF": lambda x: x._move(np.array([0, 1])),
            "MR": lambda x: x._move(np.array([1, 0])),
            "MB": lambda x: x._move(np.array([0, -1])),
            # 'TL': lambda x: x._turn(-np.pi/2), ## These intuitively feel backwards to me but they are right
            # 'TR': lambda x: x._turn(np.pi/2),
        }
        self.ACTION_KEYS = list(self.ACTIONS.keys())

        self.COLOURS = {
            0: (255 / 255, 117 / 255, 26 / 255),
            1: (172 / 255, 57 / 255, 172 / 255),
            2: (40 / 255, 40 / 255, 40 / 255),
            3: (1, 1, 1),  # (255/255,209/255,26/255),
            "MZ": (255 / 255, 255 / 255, 255 / 255),
            "MF": (255 / 255, 209 / 255, 26 / 255),
            "ML": (0 / 255, 209 / 255, 0 / 255),
            "MR": (255 / 255, 0 / 255, 0 / 255),
            "MB": (0 / 255, 0 / 255, 226 / 255),
            "TL": (235 / 255, 97 / 255, 6 / 255),
            "TR": (152 / 255, 37 / 255, 142 / 255),
        }


class Parameters:
    def __init__(self, raw: np.ndarray = None):

        ## Bundle params
        self.iw_depth = 3
        self.edge_decay_open = 0.03  # 0.08
        self.edge_decay_closed = 0.01
        self.edge_reinforcement = 3.0
        self.base_vote = 1.0
        self.start_weight = 5.0
        self.p_req = 0.0


class Arena(entity.Entity):
    def __init__(self, n=8, r=3):
        super().__init__()
        self.size = n * r
        self.grid = np.random.randint(0, 1, (self.size, self.size)).astype(np.float64)
        self.n = n
        self.r = r


class Robot(entity.Entity):
    def __init__(self, world, pos=np.array([3, 3]), bearing=0, hist=None):
        super().__init__()
        self.SO = SensorimotorOptions()
        self.params = Parameters()
        self.bundle = Bundle(self.SO, self.params)

        self.hist = hist
        self.iter = 0
        self.world = world

        self.s_word = 1

        self.forward_sensor = np.array([0, 1])
        self.bearing = bearing
        self.partner = None
        self.bcos = int(np.cos(bearing))
        self.bsin = int(np.sin(bearing))

        self.pos = pos
        self.bonus_grid = np.stack(
            np.meshgrid(
                np.arange(0, self.world.size, self.world.n),
                np.arange(0, self.world.size, self.world.n),
            ),
            2,
        ).reshape(self.world.r ** 2, 2)
        self.bonus_pos = self.bonus_grid + self.pos

        self.sense()

        self.pos_hist = [np.copy(self.pos)]
        self.s_hist = [np.copy(self.s_)]

        self.prev_act = None

    def iterate_part1(self):
        if self.hist == None:
            act = self.bundle.acquire_act()

            if (
                self.prev_act == "ML"
                and act == "MR"
                or self.prev_act == "MR"
                and act == "ML"
                or self.prev_act == "MU"
                and act == "MD"
                or self.prev_act == "MD"
                and act == "MU"
            ):

                act = "MZ"

            self.take_action(act)
            self.prev_act = act
            return act
        else:
            self.pos = self.hist[self.iter]

    def iterate_part2(self, act):
        if act != None:
            self.sense()
            self.pos_hist.append(np.copy(self.pos))
            self.s_hist.append(np.copy(self.s_))
            result_state = (act, (self.s_, self.s_word))
            self.bundle.iterate(act, result_state)

    def circular_distance(self, a, b, w=None):
        if w == None:
            w = np.array([self.world.size - 2, self.world.size - 2])
        return np.absolute(a - b) % w

    def sense(self):
        # if self.partner != None and np.all(self.partner.pos == self.pos+self.adjust_vector_by_bearing(self.forward_sensor)):
        if (
            self.partner != None
            and np.linalg.norm(self.circular_distance(self.partner.pos, self.pos)) < 2
        ):
            self.s_ = 1
        # elif self.partner != None and np.linalg.norm(self.circular_distance(self.partner.pos,self.pos)) < 3:
        #     self.s_ = 2
        # elif self.partner != None and np.linalg.norm(self.circular_distance(self.partner.pos,self.pos)) < 4.5:
        #     self.s_ = 3
        else:
            self.s_ = 0

    def take_action(self, action):
        self.SO.ACTIONS[action](self)

    def adjust_vector_by_bearing(self, vec):
        x2 = vec[0] * self.bcos - vec[1] * self.bsin
        y2 = vec[0] * self.bsin + vec[1] * self.bcos
        return np.array([x2, y2])

    def _move(self, motion):
        proposed_pos = (self.pos + self.adjust_vector_by_bearing(motion)) % self.world.n

        # if np.any(proposed_pos != self.partner.pos):
        self.pos = proposed_pos

        self.bonus_pos = self.bonus_grid + self.pos

    def _turn(self, d):
        self.bearing = (self.bearing + d) % (np.pi * 2)
        self.bcos = int(np.cos(self.bearing))
        self.bsin = int(np.sin(self.bearing))


class Model(simulation.Simulation):
    def __init__(self):
        super().__init__(tracking = True)
        self.arena = Arena()
        self.environment = self.arena
        self.robot = Robot(self.arena)
        self.robot2 = Robot(self.arena)
        self.robot.partner = self.robot2
        self.robot2.partner = self.robot
        self.robots.append(self.robot)
        self.robot.track_variable("s_")

    def iterate(self):
        act1 = self.robot.iterate_part1()
        act2 = self.robot2.iterate_part1()
        self.robot2.iterate_part2(act2)
        self.robot.iterate_part2(act1)

    def set_word(self, word):
        self.robot.s_word = word
        self.robot2.s_word = word

    def initialize(self, pos=None):
        # self.robot.untrack_variable("s_")
        self.__init__()


class Exp(experiment.Experiment):
    def __init__(self):
        super().__init__()
        self.simulation = Model()
        self.i = 0

    def iterate(self):
        self.simulation.iterate()
        # print("fast")

    def initialize(self):
        self.simulation.initialize()

import time 
class Viz(visuals.BaseVispy):
    def __init__(self, widget, sim, bg=(1,1,1,0)):
        super().__init__(widget)
        self.t = time.time()
        self.sim = sim
        self.view.camera.set_range((0, self.sim.arena.size), (0, self.sim.arena.size))
        self.view.camera.aspect = 1
        self.cm = color.Colormap(
            [
                self.sim.robot.SO.COLOURS[self.sim.robot.SO.SENSES["ORANGE"]],
                self.sim.robot.SO.COLOURS[self.sim.robot.SO.SENSES["PURPLE"]],
                self.sim.robot.SO.COLOURS[self.sim.robot.SO.SENSES["BLACK"]],
            ],
            # (0.0,0.33,0.50,0.66,1.0),
        )

        self.robot_marker = scene.Markers(
            pos=self.sim.robot.bonus_pos + 0.5,
            face_color=self.sim.robot.SO.COLOURS[3],
            symbol="square",
            parent=self.view.scene,
        )
        self.robot2_marker = scene.Markers(
            pos=self.sim.robot2.bonus_pos + 0.5,
            face_color="r",
            symbol="square",
            parent=self.view.scene,
        )

        self.grid = scene.visuals.Image(
            self.sim.arena.grid.T,
            interpolation="nearest",
            cmap=self.cm,
            parent=self.view.scene,
            method="subdivide",
        )

    def iterate(self):
        # print(time.time()-self.t)
        self.t = time.time()

        r1f = self.sim.robot.adjust_vector_by_bearing(np.array([0.0, 0.5]))
        r2f = self.sim.robot2.adjust_vector_by_bearing(np.array([0.0, 0.5]))

        self.robot_marker.set_data(
            pos=self.sim.robot.bonus_pos + 0.5,
            face_color=self.sim.robot.SO.COLOURS[3],
            size=1,
            scaling=True,
            symbol="square",
        )
        self.robot2_marker.set_data(
            pos=self.sim.robot2.bonus_pos + 0.5,
            face_color="r",
            size=1,
            scaling=True,
            symbol="square",
        )

        self.grid.set_data(self.sim.arena.grid.T)
        # self.canvas.update()
        # print("hi")
        # self.canvas.render()

    def reset(self):
        self.iterate()

class Plt(visuals.BaseTS):
    def __init__(self, *args, figsize = (800,800), **kwargs):
        super(Plt, self).__init__(figsize=figsize, **kwargs)
        # a = np.linspace(0,1,1000)
        # self.ax.plot(a,a)

    # def iterate(self):
        # self.ax.

c = core.Core(Exp(), fps=10, speed=60, full_size=600)
# c.gui.add_visual_frame("sim", Viz, c.experiment.simulation, size = (c.full_size,c.full_size), pos = (0,0,6,6))
c.gui.add_tab("sim")
v = [(lambda x: x.robots[0], c.experiment.simulation, "s_")]
c.gui.add_visual_frame(0, Plt, vars_ = v, size = (c.full_size, c.full_size), pos = (0,0,6,6))
c.gui.add_visual_frame(0, Viz, c.experiment.simulation, size = (c.full_size,c.half_size), pos = (0,6,3,6))
c.gui.add_visual_frame(0, Viz, c.experiment.simulation, size = (c.full_size,c.half_size), pos = (3,6,3,6))
c.gui.add_visual_frame(0, Viz, c.experiment.simulation, size =
        (c.twothird_size,c.half_size), pos = (6,0,3,4))
c.gui.add_visual_frame(0, Viz, c.experiment.simulation, size =
        (c.third_size,c.half_size), pos = (6,4,3,2))
c.gui.add_visual_frame(0, Viz, c.experiment.simulation, size =
        (c.full_size,c.half_size), pos = (6,6,3,6))
c.gui.insert_visual(0, 0, Viz, c.experiment.simulation, bg='r')
c.gui.swap_visual(0, 0,0)
# c.gui.swap_visual(0,0,1)
c.gui.add_tab("dd", buttons=True, layout="triple1")
c.gui.insert_visual(1, 0, Viz, c.experiment.simulation, bg='r')
c.gui.insert_visual(1, 1, Viz, c.experiment.simulation, bg='r')
c.gui.add_tab("dd2", buttons=True, layout="longpair")
c.gui.insert_visual(2, 0, Viz, c.experiment.simulation, bg='r')
c.gui.insert_visual(2, 1, Viz, c.experiment.simulation, bg='r')
c.experiment.class1 = Plt
c.run()
