# Copyright 2026 Rockwell Automation Technologies, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from auto_explore_clearpath.frontiers import COSTMAP_BLOCKED, Grid, select_frontier
import numpy as np
import pytest

RESOLUTION = 0.1
ROBOT = (2.0, 3.0)
NEAR_X = 0.55  # frontier column beside the unknown strip on the left
FAR_X = 5.45  # frontier column beside the unknown strip on the right


def two_frontier_map() -> Grid:
    """Free 6 m x 6 m room with unknown strips at both ends, the left one nearer the robot."""
    data = np.zeros((60, 60), dtype=np.int8)
    data[:, :5] = -1
    data[:, 55:] = -1
    return Grid(data, 0.0, 0.0, RESOLUTION)


def test_prefers_nearer_frontier():
    goal = select_frontier(two_frontier_map(), ROBOT)

    assert goal is not None
    assert goal[0] == pytest.approx(NEAR_X)
    assert goal[1] == pytest.approx(ROBOT[1], abs=RESOLUTION)


@pytest.mark.parametrize(
    ('near_cost', 'limits'),
    [
        (COSTMAP_BLOCKED, {}),  # robot footprint cannot reach the near frontier
        (70, {'max_goal_cost': 50}),  # near frontier sits in the inflation band beside a wall
    ],
)
def test_skips_frontier_above_costmap_limit(near_cost, limits):
    costmap = np.zeros((60, 60), dtype=np.int8)
    costmap[:, 4:7] = near_cost

    goal = select_frontier(
        two_frontier_map(),
        ROBOT,
        costmap=Grid(costmap, 0.0, 0.0, RESOLUTION),
        **limits,
    )

    assert goal is not None
    assert goal[0] == pytest.approx(FAR_X)
