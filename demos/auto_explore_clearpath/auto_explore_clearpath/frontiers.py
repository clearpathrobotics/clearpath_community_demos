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

"""Frontier goal selection on occupancy grids, independent of ROS."""

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np

UNKNOWN = -1
OCCUPIED_THRESHOLD = 50
# Nav2 publishes its costmap on a 0-100 scale: inscribed-obstacle cells are 99, lethal ones 100
COSTMAP_BLOCKED = 99
# Metres of distance one extra unknown neighbour is worth when ranking frontiers
UNKNOWN_NEIGHBOR_BONUS_M = 0.1


@dataclass(frozen=True)
class Grid:
    """Occupancy grid values (rows are y) with the world position of cell (0, 0)."""

    data: np.ndarray
    origin_x: float
    origin_y: float
    resolution: float

    def cell_centers(self, rows: np.ndarray, cols: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        return (
            self.origin_x + (cols + 0.5) * self.resolution,
            self.origin_y + (rows + 0.5) * self.resolution,
        )

    def values_at(self, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
        """Return grid values at world points, or UNKNOWN for points outside the grid."""
        cols = np.floor((xs - self.origin_x) / self.resolution).astype(int)
        rows = np.floor((ys - self.origin_y) / self.resolution).astype(int)
        height, width = self.data.shape
        inside = (rows >= 0) & (rows < height) & (cols >= 0) & (cols < width)
        values = np.full(xs.shape, UNKNOWN, dtype=self.data.dtype)
        values[inside] = self.data[rows[inside], cols[inside]]
        return values


def _window_sum(mask: np.ndarray, radius: int) -> np.ndarray:
    """Count true cells in the (2 * radius + 1) square around each cell; outside counts as 0."""
    size = 2 * radius + 1
    padded = np.pad(mask.astype(np.int32), radius)
    integral = np.pad(padded.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    return (
        integral[size:, size:]
        - integral[:-size, size:]
        - integral[size:, :-size]
        + integral[:-size, :-size]
    )


def select_frontier(
    grid: Grid,
    robot_xy: tuple[float, float],
    *,
    min_unknown_neighbors: int = 1,
    clearance_cells: int = 3,
    min_distance_m: float = 1.0,
    max_distance_m: float = 20.0,
    visited: Iterable[tuple[float, float]] = (),
    revisit_distance_m: float = 1.0,
    costmap: Grid | None = None,
    max_goal_cost: int = COSTMAP_BLOCKED - 1,
) -> tuple[float, float] | None:
    """
    Return the world position of the best frontier cell, or None.

    A frontier is a free cell, not on the grid border, that touches unknown space and has no
    occupied cell within clearance_cells. Cells whose Nav2 costmap cost is above max_goal_cost
    are skipped: by default only inscribed and lethal cells, which the robot's footprint cannot
    reach, while lower limits also keep goals out of the inflation band beside walls. The
    nearest frontier wins, with a small bonus for bordering more unknown space.
    """
    data = grid.data
    occupied = data > OCCUPIED_THRESHOLD
    unknown_neighbors = _window_sum(data == UNKNOWN, 1)

    candidates = (data == 0) & (unknown_neighbors >= min_unknown_neighbors)
    candidates &= _window_sum(occupied, max(1, clearance_cells)) == 0
    candidates[[0, -1], :] = False
    candidates[:, [0, -1]] = False

    rows, cols = np.nonzero(candidates)
    xs, ys = grid.cell_centers(rows, cols)
    dist = np.hypot(xs - robot_xy[0], ys - robot_xy[1])
    keep = (dist >= min_distance_m) & (dist <= max_distance_m)
    for vx, vy in visited:
        keep &= np.hypot(xs - vx, ys - vy) >= revisit_distance_m
    if costmap is not None:
        keep &= costmap.values_at(xs, ys) <= max_goal_cost
    if not keep.any():
        return None

    score = dist[keep] - UNKNOWN_NEIGHBOR_BONUS_M * unknown_neighbors[rows[keep], cols[keep]]
    best = int(np.argmin(score))
    return float(xs[keep][best]), float(ys[keep][best])


def goal_timeout_sec(distance_m: float, minimum_sec: float, per_meter_sec: float) -> float:
    """Return how long to allow for a goal, scaled by its straight-line distance."""
    return max(minimum_sec, per_meter_sec * distance_m)
