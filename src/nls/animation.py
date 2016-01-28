#   nls/animation.py
#   This module define routines and type to record evolution of solution and store it into file.
#   (c) Daniel Bershatsky, 2016
#   See LICENSE for details

from __future__ import print_function
from time import time
from matplotlib import animation
from matplotlib.pyplot import figure
from .pumping import GaussianPumping


class AbstractAnimation(object):
    """Animation base class that contains common method of initialization and rendering video.
    """

    def __init__(self, model, frames, step=1):
        self.elapsed_time = 0.0
        self.model = model
        self.frames = frames
        self.step = step
        self.writer = animation.writers['ffmpeg'](fps=15, metadata={'title': 'Exciton-polariton condensation.'})

    def getElapsedTime(self):
        return self.elapsed_time

    def render(self, filename):
        self.elapsed_time = -time()
        dpi = 100
        fig = figure(figsize=(16, 9), dpi=dpi)
        with self.writer.saving(fig, filename, dpi):
            pass
        self.elapsed_time += time()

    def report(self):
        message = 'Elapsed in {0} seconds with {1} frames and {2} step.'
        print(message.format(self.elapsed_time, self.frames, self.step))


class IterationIncreaseAnimation(AbstractAnimation):
    """This class represents object that provide ability to render video that frames draw solution profile in different
    number of iteration which is increasing.
    """

    def __init__(self, model, frames, step=1):
        super(IterationIncreaseAnimation, self).__init__(model, frames, step)

    def animate(self, filename):
        self.elapsed_time = -time()
        dpi = 100
        fig = figure(figsize=(16, 9), dpi=dpi)
        with self.writer.saving(fig, filename, dpi):
            for i in xrange(self.frames + 1):
                solution = self.model.solve(self.step)  # Fix references entanglement
                solution.setInitialSolution(solution.getSolution())
                solution.visualize()
                self.writer.grab_frame()
        self.elapsed_time += time()


class PumpingRadiusIncreaseAnimation(AbstractAnimation):
    """This class implements animation scenario that shows solution profile with different radius of pumping profile.
    In this case spacial pumping profile is gaussian.
    """

    def __init__(self, model, frames, step=1):
        super(PumpingRadiusIncreaseAnimation, self).__init__(model, frames, step)

    def animate(self, filename):
        self.elapsed_time = -time()
        dpi = 100
        fig = figure(figsize=(16, 9), dpi=dpi)
        with self.writer.saving(fig, filename, dpi):
            for i in xrange(self.frames + 1):
                origin = i * self.step
                pumping = GaussianPumping(power=3.0, x0=+origin, variation=6.84931506849) \
                       + GaussianPumping(power=3.0, x0=-origin, variation=6.84931506849)
                self.model.solution.setPumping(pumping)
                solution = self.model.solve()  # Fix references entanglement
                solution.setInitialSolution(solution.getSolution())
                solution.visualize()
                self.writer.grab_frame()
        self.elapsed_time += time()


class PumpingPowerIncreaseAnimation(AbstractAnimation):
    """Funcational animation that is implemented by object of this type is increasing pumping power as time increase.
    Pumping model of a problem should provide ability to set pumping power.
    """

    def __init__(self, model, frames, step=0.1):
        super(PumpingPowerIncreaseAnimation, self).__init__(model, frames, step)

    def animate(self, filename):
        self.elapsed_time = -time()
        dpi = 100
        fig = figure(figsize=(16, 9), dpi=dpi)
        with self.writer.saving(fig, filename, dpi):
            for i in xrange(self.frames + 1):
                self.model.solution.pumping.power = i * self.step
                solution = self.model.solve()  # Fix references entanglement
                solution.visualize()
                self.writer.grab_frame()
        self.elapsed_time += time()