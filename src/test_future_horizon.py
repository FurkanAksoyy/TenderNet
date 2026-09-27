"""Regression checks for first strictly-future wins; run with python -B src/test_future_horizon.py."""
from types import SimpleNamespace
import numpy as np
import pandas as pd
from revision_d import extra_feats, Sim


def main():
    # A nearby follow-up followed by a distant win must NOT count as late formation.
    # A same-day award is neither historical nor strictly future.
    dates = {0: np.array([100, 222, 2720]), 1: np.array([500]), 2: np.array([100, 600])}
    H = SimpleNamespace(fm={(f, 0): d for f, d in dates.items()},
                        fkm={(f, 0, 0): d for f, d in dates.items()}, fdays=dates)
    P = {'day': np.array([100]), 'mkt': np.array([0]), 'buyer': np.array([0])}
    C = pd.DataFrame({'contract': [0, 0, 0], 'firm': [0, 1, 2]})
    out = extra_feats(P, H, C, lags=(0, 365))
    assert out.fut_gt365.tolist() == [0, 1, 1]
    assert out.fut_le365.tolist() == [1, 0, 0]
    assert out.fut_gt0.tolist() == [1, 1, 1]
    # Verify the simulation assembly uses the same horizon rule.
    sim = Sim.__new__(Sim)
    sim.P = {'day': np.array([100]), 'bm': np.array([0])}
    sim.firms = np.array([0, 1, 2]); sim.con = np.zeros(3, dtype=int)
    sim.bu = np.zeros(3, dtype=int); sim.sl = {0: (0, 3)}; sim.el_idx = np.array([0])
    hist = {0: [(int(d), f) for f, dd in dates.items() for d in dd]}
    from revision_d import OTH
    got, _ = sim._assemble(np.array([0]), hist, np.zeros((3, len(OTH))), (365,))
    assert got.fut_gt365.tolist() == [0, 1, 1]
    assert got.fut_le365.tolist() == [1, 0, 0]
    print('PASS: first future win, near+far follow-ups, same-day exclusion, simulation parity')


if __name__ == '__main__':
    main()
