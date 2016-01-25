#!/usr/bin/env python2
#   solve2d.py
#   (c) Daniel Bershatsky, 2016
#   See LICENSE for details

from __future__ import print_function
from sys import path
from nls import Problem, GaussianPumping, IterationIncreaseAnimation


def main():
    model = Problem().model(
        model = '2d',
        dx = 1.0e-1,
        dt = 1.0e-3,
        t0 = 0.0,
        u0 = 0.1,
        order = 5,
        num_nodes = 40,
        num_iters = 10000,
        pumping = GaussianPumping(power=3.0, variation=6.84931506849),
        original_params = {
            'R': 0.05,
            'gamma': 0.566,
            'g': 1.0e-3,
            'tilde_g': 0.011,
            'gamma_R': 10,
        },
        dimless_params = {
        })

    # Obtain steady state solution
    solution = model.solve()
    solution.report()


if __name__ == '__main__':
    main()