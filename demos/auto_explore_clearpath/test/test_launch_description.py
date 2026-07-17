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

from pathlib import Path
import runpy

from launch import LaunchDescription


def _load_launch(path: Path):
    exports = runpy.run_path(str(path))
    return exports['generate_launch_description']


def test_auto_explore_launch_description_construction():
    launch_file = Path(__file__).resolve().parents[1] / 'launch' / 'auto_explore.launch.py'
    generate = _load_launch(launch_file)
    ld = generate()
    assert isinstance(ld, LaunchDescription)


def test_auto_explore_stack_launch_description_construction():
    launch_file = Path(__file__).resolve().parents[1] / 'launch' / 'auto_explore_stack.launch.py'
    generate = _load_launch(launch_file)
    ld = generate()
    assert isinstance(ld, LaunchDescription)
