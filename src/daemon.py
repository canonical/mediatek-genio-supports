#
# Copyright (C) 2025 Canonical Ltd
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import os
from pathlib import Path
from typing import List, Union


class Daemon:
    name: str
    hw_model: str
    ld_library_path: List[Union[Path, str]]
    path: List[Union[Path, str]]

    def __init__(self, daemon_name: str, hw: str):
        self.name = daemon_name
        self.hw_model = hw
        
        if self.hw_model is None:
            raise RuntimeError("Unsupported hardware")
        base_path = Path(os.environ["SNAP"])
        self.ld_library_path = [
            base_path / self.name / "lib",
            base_path / self.name / "lib" / self.hw_model,
        ]
        if "LD_LIBRARY_PATH" in os.environ:
            self.ld_library_path.extend(os.environ["LD_LIBRARY_PATH"].split(":"))

        self.path = [
            base_path / self.name / "bin",
            base_path / self.name / "bin" / self.hw_model,
        ]

        self.entry_path = None
        for p in self.path:
            entry_path = p.joinpath(self.name)
            if entry_path.is_file():
                self.entry_path = entry_path
                break
        else:
            raise RuntimeError(
                f"No entry path found for ${self.name} daemon. Path searched: \n{"\n".join([str(p) for p in self.path])}"
            )

        if "PATH" in os.environ:
            self.path.extend(os.environ["PATH"].split(":"))

    def run(self):
        new_env = os.environ.copy()
        new_env["LD_LIBRARY_PATH"] = ":".join([str(p) for p in self.ld_library_path])
        new_env["PATH"] = ":".join([str(p) for p in self.path])
        os.execve(self.entry_path, [self.name], new_env)
