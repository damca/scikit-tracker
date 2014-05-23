
# -*- coding: utf-8 -*-


from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function


from nose.tools import assert_raises
from nose.tools import assert_dict_equal
from numpy.testing import assert_array_equal
from numpy.testing import assert_array_almost_equal
from numpy.testing import assert_almost_equal


import numpy as np
import tempfile
import pandas as pd

from sktracker import data
from sktracker.trajectories import Trajectories


def test_attributes():

    trajs = data.brownian_trajs_df()
    trajs = Trajectories(trajs)

    assert_array_equal(trajs.t_stamps, np.array([0, 1, 2, 3, 4]))

    assert_array_equal(trajs.labels, np.array([0, 1, 2, 3, 4]))

    segments = {0: [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)],
                1: [(0, 1), (1, 1), (2, 1), (3, 1), (4, 1)],
                2: [(0, 2), (1, 2), (2, 2), (3, 2), (4, 2)],
                3: [(0, 3), (1, 3), (2, 3), (3, 3), (4, 3)],
                4: [(0, 4), (1, 4), (2, 4), (3, 4), (4, 4)]}
    assert_dict_equal(trajs.segment_idxs, segments)

    traj = np.array([[ -9.25386045,  11.34555088,  22.11820326,   3.        ,   0.        ],
                     [ 11.05321776,   3.23738477,   2.62790435,   2.        ,   1.        ],
                     [ 16.6824928 ,  14.602054  , -12.1218683 ,   4.        ,   2.        ],
                     [ 17.22410516,  14.8068125 , -11.87642753,   4.        ,   3.        ],
                     [  2.80222495, -13.13783042,   8.56406878,   0.        ,   4.        ]])
    t_stamp, traj_to_test = list(trajs.iter_segments)[0]
    assert_array_almost_equal(traj, traj_to_test)

    assert list(trajs.get_segments().keys()) == [0, 1, 2, 3, 4]


def test_structure():
    trajs = data.brownian_trajs_df()
    trajs = Trajectories(trajs)

    assert_raises(ValueError, trajs.check_trajs_df_structure, ['t_idx'])
    assert_raises(ValueError, trajs.check_trajs_df_structure, ['t_stamp', 'label'], ['dx'])

    trajs.check_trajs_df_structure(['t_stamp', 'label'], ['x', 'y', 'z'])


def test_copy():
    trajs = data.brownian_trajs_df()
    trajs = Trajectories(trajs)

    assert isinstance(trajs.copy(), Trajectories)

def test_empty():
    empty = Trajectories.empty_trajs(columns=['x', 'y'])

    assert empty.shape == (0, 2)
    assert empty.empty is True

def test_reverse():
    trajs = data.brownian_trajs_df()
    trajs = Trajectories(trajs)

    assert trajs.reverse().shape == (25, 5)

def test_write_hdf():

    trajs = data.brownian_trajs_df()
    trajs = Trajectories(trajs)
    tmp_store = tempfile.NamedTemporaryFile(suffix='h5')
    with pd.get_store(tmp_store.name) as store:
        store['trajs'] = trajs


def get_mean_dist():

    true_trajs = data.brownian_trajs_df()

    trajs = Trajectories(true_trajs)
    mean_dist = trajs.get_mean_distances()

    true_dist = np.array([1.58959148, 1.42974187,
                          1.97505829, 1.93212297, 1.30778342])

    assert_array_almost_equal(true_dist, mean_dist.values.flatten())


def test_interpolate():

    trajs = Trajectories(data.with_gaps_df())
    trajs.set_index('true_label', inplace=True, append=True)
    trajs.reset_index(level='label', drop=True, inplace=True)
    trajs.index.set_names(['t_stamp', 'label'], inplace=True)
    interpo = trajs.time_interpolate(time_step=0.1, s=1)
    dts = interpo.get_segments()[0].t.diff().dropna()
    # All time points should be equaly spaced
    assert_almost_equal(dts.min(), dts.max())

def test_all_speeds():

    trajs = data.brownian_trajs_df()
    trajs = Trajectories(trajs)
    speeds = trajs.all_speeds()

    real_speeds = [29.29149253,  42.24278092,   1.24544591,  28.5496605 ,
                 31.5956165 ,  21.93710968,  39.96189529,  30.506188  ,
                 23.63875175,   2.02299763,  25.16282357,  34.9177922 ,
                 29.54915698,   0.77486359,  23.92966393,  18.10192901,
                  1.4519421 ,  42.6697699 ,  35.80933981,  38.35867461,
                  2.00826474,  20.00524827,  28.63076735,  23.96234609,
                 20.22339956,  19.45251236,  29.61463181,  25.36724868,
                  1.61745084,  21.17778688,   1.00431235,  42.54397154,
                 35.15677816,  19.85153065,  39.07826864,  43.91553261,
                  1.14867379,  30.29739719,  29.36707721,  32.13200073,
                 36.47041249,  30.15276245,   1.131474  ,  24.3376009 ,
                 24.77755792,  39.50921192,  32.31300005,  23.67070283,
                 20.12833613,   0.6951622 ,   0.62889679,  19.35806068,
                 45.24644565,  39.42756814,  37.55238742,  43.4886719 ,
                 28.25417822,   2.40067016,  32.46583113,  31.23535934,
                 36.41432396,  24.7943914 ,  32.94421696,  23.2506553 ,
                  2.06057683,  20.47042796,   2.22746757,  30.79769909,
                 20.13682322,  24.742422  ,  39.65555878,  21.87756577,
                 33.5356576 ,   1.20844778,  23.46008422,  37.50610066,
                 46.73647432,  38.31748506,   2.14598242,  20.37801735,
                 19.87613565,  32.12389289,  25.36581069,  17.50636222,
                  2.04705   ,  32.53990188,   2.933702  ,  32.82776228,
                 43.24067854,  29.9153449 ,   2.43175831,  36.47559589,
                 20.77942458,  38.02339969,  21.63794875,  20.69995033,
                 35.15221208,   1.75205306,  36.63872024,  27.19684534]

    assert_almost_equal(speeds, real_speeds)