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
import argparse
import sys
import os
from typing import List
from pathlib import Path

SNAP_NAME = os.environ["SNAP_NAME"]

ALL_DAEMONS = {
    "mdpd": ["mt8365"],
    "vpud": ["mt8365", "mt8188", "mt8391", "mt8395"],
}

def hardware_list():
    with open("/proc/device-tree/compatible", "rb") as f:
        return set([s.decode("ASCII") for s in f.read().split(b"\0") if s != b""])


def detect_hardware(candidates: List[str]):
    if candidates is None:
        return None
    try:
        all_hw = hardware_list()
    except PermissionError:
        print(
            "Insufficient permissions to detect hardware models. Please run this command to fix this problem:",
            file=sys.stderr,
        )
        print(f"sudo snap connect {SNAP_NAME}:hardware-observe", file=sys.stderr)
        sys.exit(1)

    for comp in all_hw:
        for cand in candidates:
            if comp == f"mediatek,{cand}":
                return cand
    return None


def print_hardware():
    print(hardware_list())

def check_daemon(name):
    hw = detect_hardware(ALL_DAEMONS[name])
    if hw is None:
        sys.exit(1)
    else:
        sys.exit(0)

def run_daemon(name):
    hw = detect_hardware(ALL_DAEMONS[name])

    if hw is None:
        print("This daemon is not applicable for this device", file=sys.stderr)
        sys.exit(1)

    base_path = Path(os.environ["SNAP"])
    ld_library_path = [
        base_path / name / "lib",
        base_path / name / "lib" / hw,
    ]
    if "LD_LIBRARY_PATH" in os.environ:
        ld_library_path.extend(os.environ["LD_LIBRARY_PATH"].split(":"))

    path = [
        base_path / name / "bin",
        base_path / name / "bin" / hw,
    ]

    entry_path = None
    for p in path:
        entry_path = p.joinpath(name)
        if entry_path.is_file():
            entry_path = entry_path
            break
    else:
        raise RuntimeError(
            f"No entry path found for {name} daemon. Path searched: \n{"\n".join([str(p) for p in path])}"
        )

    if "PATH" in os.environ:
        path.extend(os.environ["PATH"].split(":"))

    new_env = os.environ.copy()
    new_env["LD_LIBRARY_PATH"] = ":".join([str(p) for p in ld_library_path])
    new_env["PATH"] = ":".join([str(p) for p in path])
    os.execve(entry_path, [name], new_env)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if this daemon is applicable on this device and exit.",
    )
    parser.add_argument("daemon", choices=list(ALL_DAEMONS.keys()), nargs=1, help="The daemon to run.")
    
    return parser.parse_args()


def main():
    args = parse_args()
    if args.check:
        check_daemon(args.daemon[0])
        return
    run_daemon(args.daemon[0])


main()
