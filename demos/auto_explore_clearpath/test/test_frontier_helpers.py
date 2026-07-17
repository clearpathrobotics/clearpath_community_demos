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

import math

from auto_explore_clearpath.frontier_explorer import FrontierExplorer


def test_yaw_to_quaternion_identity():
    q = FrontierExplorer._yaw_to_quaternion(0.0)
    assert q.x == 0.0
    assert q.y == 0.0
    assert abs(q.z) < 1e-9
    assert abs(q.w - 1.0) < 1e-9


def test_yaw_to_quaternion_pi_over_2():
    q = FrontierExplorer._yaw_to_quaternion(math.pi / 2.0)
    assert q.x == 0.0
    assert q.y == 0.0
    assert abs(q.z - math.sqrt(2.0) / 2.0) < 1e-6
    assert abs(q.w - math.sqrt(2.0) / 2.0) < 1e-6


def test_is_safe_from_obstacles_positive():
    data = [0] * 25
    assert FrontierExplorer._is_safe_from_obstacles(data, 5, 5, 2, 2, 1)


def test_is_safe_from_obstacles_negative():
    data = [0] * 25
    data[2 * 5 + 2] = 100
    assert not FrontierExplorer._is_safe_from_obstacles(data, 5, 5, 2, 2, 1)
