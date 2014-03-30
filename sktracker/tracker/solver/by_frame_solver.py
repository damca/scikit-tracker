import numpy as np

from ...utils import print_progress

from ..matrix import LinkBlock
from ..matrix import DiagBlock
from ..matrix import CostMatrix

from ..cost_function import AbstractLinkCostFunction
from ..cost_function import AbstractDiagCostFunction

from ..cost_function.brownian import BrownianCostFunction
from ..cost_function import DiagCostFunction

from . import AbstractSolver

__all__ = []


class ByFrameSolver(AbstractSolver):
    """

    Parameters
    ----------
    trajs : :class:`pandas.DataFrame`
    cost_functions : list of list
    """
    def __init__(self, trajs, cost_functions, coords=['x', 'y', 'z']):

        super().__init__(trajs)

        self.t_in = 0
        self.t_out = 0

        self.coords = coords

        self.trajs.check_trajs_df_structure(index=['t_stamp', 'label'],
                                            columns=['t'] + coords)

        self.link_cf = cost_functions['link']
        self.check_cost_function_type(self.link_cf, AbstractLinkCostFunction)

        self.birth_cf = cost_functions['birth']
        self.check_cost_function_type(self.birth_cf, AbstractDiagCostFunction)

        self.death_cf = cost_functions['death']
        self.check_cost_function_type(self.death_cf, AbstractDiagCostFunction)

        self.max_assigned_cost = self.death_cf.context['cost'] / 1.05

    @classmethod
    def for_brownian_motion(cls, trajs, max_speed, coords=['x', 'y', 'z']):
        """

        Parameters
        ----------
        trajs : :class:`pandas.DataFrame`
        max_speed : float
            Max objects velocity
        coords : list
        """

        guessed_cost = max_speed ** 2
        cost_functions = {'link': BrownianCostFunction({'max_speed': max_speed,
                                                        'coords': coords}),
                          'birth': DiagCostFunction({'cost': guessed_cost}),
                          'death': DiagCostFunction({'cost': guessed_cost})}

        return cls(trajs, cost_functions, coords=coords)

    @property
    def blocks_structure(self):
        return [[self.link_block.mat, self.death_block.mat],
                [self.birth_block.mat, None]]

    @property
    def pos_in(self):
        return self.trajs.loc[self.t_in]

    @property
    def pos_out(self):
        return self.trajs.loc[self.t_out]

    def track(self, progress_bar=False, progress_bar_out=None):
        """

        Returns
        -------
        self.trajs : :class:`pandas.DataFrame`
        progress_bar : bool
            Display progress bar
        progress_bar_out : OutStream
            For testing purpose only
        """

        old_labels = self.trajs.index.get_level_values('label').values
        self.trajs['new_label'] = old_labels.astype(np.float)
        ts_in = self.trajs.t_stamps[:-1]
        ts_out = self.trajs.t_stamps[1:]

        n = len(ts_in)
        for i, (t_in, t_out) in enumerate(zip(ts_in, ts_out)):
            if progress_bar:
                progress = i / n * 100
                message = "t_in : {} | t_out {}".format(t_in, t_out)
                print_progress(progress, message=message, out=progress_bar_out)

            self.one_frame(t_in, t_out)

        if progress_bar:
            print_progress(-1)

        self.relabel_trajs()
        return self.trajs

    def one_frame(self, t_in, t_out):
        """

        Parameters
        ----------
        t_in : int
        t_out : int
        """

        self.t_in = t_in
        self.t_out = t_out
        pos_in = self.pos_in
        pos_out = self.pos_out

        self.link_block = LinkBlock(pos_in, pos_out, self.link_cf)
        self.birth_block = DiagBlock(pos_out, self.birth_cf)
        self.death_block = DiagBlock(pos_in, self.death_cf)

        self.cm = CostMatrix(self.blocks_structure)
        self.cm.solve()
        self.assign()

    def assign(self):
        """
        """

        row_shapes, col_shapes = self.cm.get_shapes()
        last_in_link = row_shapes[0]
        last_out_link = col_shapes[0]

        new_labels_in = self.trajs.loc[self.t_in, 'new_label'].values
        new_labels_out = np.arange(last_out_link)

        for idx_out, idx_in in enumerate(self.cm.out_links[:last_out_link]):
            if idx_in >= last_in_link:
                # new segment
                new_label = self.trajs['new_label'].max() + 1.
            else:
                # assignment
                new_label = new_labels_in[idx_in]
                self._update_max_assign_cost(self.cm.mat[idx_in, idx_out])

            new_labels_out[idx_out] = new_label
            self.trajs.loc[self.t_out, 'new_label'] = new_labels_out
            # The line below looks much slower than the two lines above
            # self.trajs.loc[self.t_out, 'new_label'].iloc[idx_out] = new_label

    def _update_max_assign_cost(self, cost):
        if cost > self.max_assigned_cost:
            self.max_assigned_cost = cost

            self.birth_cf.context['cost'] = self.max_assigned_cost * 1.05
            self.death_cf.context['cost'] = self.max_assigned_cost * 1.05