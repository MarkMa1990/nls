#   nls/model.py
#   This module define core abstractions that maps to problem and model definition.
#   (c) Daniel Bershatsky, 2016
#   See LICENSE for details

from __future__ import print_function

from pprint import pprint
from time import time
from datetime import datetime
from numpy import array, exp, arange, ones, zeros, meshgrid, mgrid, linspace
from scipy.io import loadmat, savemat
from matplotlib import animation
from matplotlib.pyplot import figure, plot, show, title, xlabel, ylabel, subplot, legend, xlim, ylim, contourf, hold

from .animation import *
from .native import *
from .pumping import *
from .solver import *


class Problem(object):
    """design pattern Factory.
    """
    
    def __init__(self):
        pass

    def model(self, *args, **kwargs):
        """
        Piority of Arguments: Arguments passed in `kwargs` has the most piority, 'param' key in `kwargs` has less
        piority than `kwargs` and dictionary arguments in `args` have the least piority. Other arguments are ignored.
        Argument List:
            model - set model type, default value 'default';
            dx - default value '1.0e-1';
            dt - default value '1.0e-3';
            t0 - default value '0.0';
            u0 - default value '1.0e-1';
            order - default value '5';
            pumping - default value ``;
            !original_params - default value `{}`;
            !dimless_params - default value `{}`;
        """
        if 'params' in kwargs:
            params = kwargs.pop('params')
            #kwargs = {**params, **kwargs}  # python 3

        kwargs['model'] == 'default' if 'model' not in kwargs else kwargs['model']

        if 'model' in kwargs and kwargs['model'] in ('1d', 'default'):
            return self.fabricateModel1D(*args, **kwargs)
        elif 'model' in kwargs and kwargs['model'] == '2d':
            return self.fabricateModel2D(*args, **kwargs)
        else:
            raise Exception('Unknown model passed!')

    def fabricateModel1D(*args, **kwargs):
        kwargs['dx'] = 1.0e-1 if 'dx' not in kwargs else kwargs['dx']
        kwargs['dt'] = 1.0e-3 if 'dt' not in kwargs else kwargs['dt']
        kwargs['t0'] = 0.0e+0 if 't0' not in kwargs else kwargs['t0']
        kwargs['u0'] = 1.0e-1 if 'u0' not in kwargs else kwargs['u0']
        kwargs['order'] = 5 if 'order' not in kwargs else kwargs['order']
        kwargs['pumping'] = GaussianPumping() if 'pumping' not in kwargs else kwargs['pumping']
        kwargs['num_nodes'] = 1000 if 'num_nodes' not in kwargs else kwargs['num_nodes']
        kwargs['num_iters'] = 100000 if 'num_iters' not in kwargs else kwargs['num_iters']

        if type(kwargs['u0']) in (int, float, complex):
            kwargs['u0'] = kwargs['u0'] * ones(kwargs['num_nodes']) 

        return Model1D(**kwargs)

    def fabricateModel2D(self, *args, **kwargs):
        kwargs['dx'] = 1.0e-1 if 'dx' not in kwargs else kwargs['dx']
        kwargs['dt'] = 1.0e-3 if 'dt' not in kwargs else kwargs['dt']
        kwargs['t0'] = 0.0e+0 if 't0' not in kwargs else kwargs['t0']
        kwargs['u0'] = 1.0e-1 if 'u0' not in kwargs else kwargs['u0']
        kwargs['order'] = 3 if 'order' not in kwargs else kwargs['order']
        kwargs['pumping'] = GaussianPumping() if 'pumping' not in kwargs else kwargs['pumping']
        kwargs['num_nodes'] = 40 if 'num_nodes' not in kwargs else kwargs['num_nodes']
        kwargs['num_iters'] = 1000 if 'num_iters' not in kwargs else kwargs['num_iters']

        if type(kwargs['u0']) in (int, float, complex):
            kwargs['u0'] = kwargs['u0'] * ones((kwargs['num_nodes'], kwargs['num_nodes'])) 

        return Model2D(**kwargs)


class AbstractModel(object):

    def __init__(self):
        pass

    def solve(self, num_iters=None):
        return self.solver(num_iters)

    def store(self, filename=None, label='', desc='', date=datetime.now()):
        """Store object to mat-file. TODO: determine format specification
        """
        filename = filename if filename else str(date).replace(' ', '_') + '.mat'

        matfile = {}
        matfile['desc'] = desc
        matfile['label'] = label
        matfile['originals'] = {}

        savemat(filename, matfile)

    def restore(self, filename):
        """Restore object from mat-file. TODO: determine format specification
        """
        matfile = loadmat(filename)

        self.desc = str(matfile['desc'][0]) if matfile['desc'].size else ''
        self.label = str(matfile['label'][0]) if matfile['label'].size else ''
        self.originals = {}

        return self


class Model1D(AbstractModel):
    """Default model that is NLS equation with reservoir in axe symmentic case.
    """

    def __init__(self, *args, **kwargs):
        pprint({
            'dt': kwargs['dt'],
            'dx': kwargs['dx'],
            'order': kwargs['order'],
            'num_nodes': kwargs['num_nodes'],
            'num_iters': kwargs['num_iters'],
            'pumping': kwargs['pumping'],
            'originals': kwargs['original_params'],
            })
        self.solution = Solution(kwargs['dt'], kwargs['dx'], kwargs['num_nodes'], kwargs['order'], kwargs['num_iters'],
                             kwargs['pumping'], kwargs['original_params'], kwargs['u0'])
        self.solver = Solver1D(self.solution)


class Model2D(AbstractModel):
    """Model that is NLS equation with reservoir on two dimensional grid.
    """

    def __init__(self, *args, **kwargs):
        pprint({
            'dt': kwargs['dt'],
            'dx': kwargs['dx'],
            'order': kwargs['order'],
            'num_nodes': kwargs['num_nodes'],
            'num_iters': kwargs['num_iters'],
            'pumping': kwargs['pumping'],
            'originals': kwargs['original_params'],
            })
        self.solution = Solution(kwargs['dt'], kwargs['dx'], kwargs['num_nodes'], kwargs['order'], kwargs['num_iters'],
                             kwargs['pumping'], kwargs['original_params'], kwargs['u0'])
        self.solver = Solver2D(self.solution)


class Solution(object):
    """Object that represents solution of a given model. Also it contains all model parameters and has ability to store
    and to load solution. TODO: improve design.
    """

    t0 = 1.0e+0 # seconds

    def __init__(self, dt, dx, num_nodes, order, num_iters, pumping, originals, init_solution):
        self.dt = dt
        self.dx = dx
        self.order = order
        self.num_nodes = num_nodes
        self.num_iters = num_iters
        self.pumping = pumping
        self.init_sol = init_solution
        self.solution = None
        self.originals = originals
        self.coeffs = zeros(23)
        self.elapsed_time = 0.0

        # NLS equation coeficients
        self.coeffs[0] = 1.0  # \partial_t
        self.coeffs[1] = 1.0  # \nabla^2
        self.coeffs[2] = originals['R'] / (4.0 * originals['tilde_g'])  # 
        self.coeffs[3] = originals['gamma'] * Solution.t0 / 2  # linear damping
        self.coeffs[4] = 1.0  # nonlinearity
        self.coeffs[5] = 1.0  # interaction to reservoir

        # Reservoir equation coefficients
        self.coeffs[10] = 0.0  # \parital_t
        self.coeffs[11] = 2.0 * originals['tilde_g'] * Solution.t0 / originals['gamma_R']  # pumping coefficient
        self.coeffs[12] = 1.0  # damping
        self.coeffs[13] = originals['R'] / (originals['gamma_R'] * originals['g'])  # interaction term
        self.coeffs[14] = 0.0  # diffusive term

    def getTimeStep(self):
        return self.dt

    def getSpatialStep(self):
        return self.dx

    def getApproximationOrder(self):
        return self.order

    def getNumberOfNodes(self):
        return self.num_nodes

    def getNumberOfIterations(self):
        return self.num_iters

    def getPumping(self):
        if self.num_nodes ** 2 == len(self.init_sol):
            right = self.num_nodes * self.dx / 2
            left = -right
            x = linspace(left, right, self.num_nodes)
            grid = meshgrid(x, x)
            return self.pumping(*grid).reshape(self.num_nodes ** 2)
        else:
            right = self.num_nodes * self.dx
            left = 0.0
            x = linspace(left, right, self.num_nodes)
            grid = meshgrid(x)
            return self.pumping(*grid)

    def getCoefficients(self):
        return self.coeffs

    def getInitialSolution(self):
        return self.init_sol

    def getSolution(self):
        return self.solution

    def getElapsedTime(self):
        return self.elapsed_time

    def setNumberOfIterations(self, num_iters):
        self.num_iters = num_iters

    def setPumping(self, pumping):
        self.pumping = pumping

    def setInitialSolution(self, solution):
        self.init_sol = solution

    def setSolution(self, solution):
        self.solution = solution

    def setElapsedTime(self, seconds):
        self.elapsed_time = seconds

    def visualize(self):
        x = arange(0.0, self.dx * self.num_nodes, self.dx)
        p = self.pumping(x)  # pumping profile
        u = (self.solution.conj() * self.solution).real  # density profile
        n = self.coeffs[11] *  p / (self.coeffs[12] + self.coeffs[13] * u)

        def rect_plot(subplot_number, value, label, name, labelx, labely, xmax=20):
            subplot(2, 3, subplot_number)
            hold(False)
            plot(x, value, label=label)
            xlim((0, xmax))
            legend(loc='best')
            title(name)
            xlabel(labelx)
            ylabel(labely)

        rect_plot(1, p, 'pumping', 'Pumping profile.', 'r', 'p')
        rect_plot(2, u, 'density', 'Density distribution of BEC.', 'r', 'u')
        rect_plot(3, n, 'reservoir', 'Density distribution of reservoir.', 'r', 'n')

        def polar_plot(subplot_number, value, xmax=20):
            hold(False)
            subplot(2, 3, subplot_number, polar=True)
            theta = arange(0, 2 * 3.14 + 0.1, 0.1)
            contourf(theta, x, array([value for _ in theta]).T)
            ylim((0, xmax))

        polar_plot(4, p)
        polar_plot(5, u)
        polar_plot(6, n)

    def show(self):
        show()

    def store(self, filename=None, label='', desc='', date=datetime.now()):
        """Store object to mat-file. TODO: determine format specification
        """
        filename = filename if filename else str(date).replace(' ', '_') + '.mat'

        matfile = {}
        matfile['desc'] = desc
        matfile['dimlesses'] = self.coeffs
        matfile['elapsed_time'] = self.elapsed_time
        matfile['label'] = label
        matfile['originals'] = self.originals
        matfile['pumping'] = self.getPumping()
        matfile['solution'] = self.solution

        savemat(filename, matfile)

    def restore(self, filename):
        """Restore object from mat-file. TODO: determine format specification
        """
        matfile = loadmat(filename)

        self.desc = str(matfile['desc'][0]) if matfile['desc'].size else ''
        self.coeffs = matfile['dimlesses'].T
        self.elapsed_time = matfile['elapsed_time']
        self.label = str(matfile['label'][0]) if matfile['label'].size else ''
        self.originals = {}
        self.solution = matfile['solution'].T

        return self

    def report(self):
        message = 'Elapsed in {0} seconds with {1} iteration on {2} grid nodes.'
        print(message.format(self.elapsed_time, self.num_iters, self.num_nodes))