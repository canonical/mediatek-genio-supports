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
import subprocess
from typing import List
from pathlib import Path

SNAP_NAME = os.environ.get("SNAP_NAME", "mediatek-genio-supports")

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


def get_component_name(daemon_name: str, hw: str) -> str:
    return f"{daemon_name}-{hw}"


def get_component_path(component_name: str) -> Path:
    # Under snap runtime, components are mounted at:
    # /snap/<snap_name>/components/<snap_revision>/<component_name>
    snap_path = Path(os.environ.get("SNAP", ""))
    rev = snap_path.name
    comp_path = snap_path.parent / "components" / rev / component_name
    return comp_path


def check_daemon(name: str):
    hw = detect_hardware(ALL_DAEMONS[name])
    if hw is None:
        sys.exit(1)

    comp_name = get_component_name(name, hw)
    comp_path = get_component_path(comp_name)
    if not comp_path.is_dir():
        sys.exit(1)

    sys.exit(0)


def ensure_components():
    """Detect current hardware and install required components via snapctl install."""
    installed_any = False
    for daemon_name, candidates in ALL_DAEMONS.items():
        hw = detect_hardware(candidates)
        if hw is not None:
            comp_name = get_component_name(daemon_name, hw)
            comp_path = get_component_path(comp_name)
            if not comp_path.is_dir():
                print(f"Installing component: +{comp_name}")
                subprocess.run(["snapctl", "install", f"+{comp_name}"], check=True)
                installed_any = True
            else:
                print(f"Component +{comp_name} already installed")
    return installed_any


def run_daemon(name: str):
    hw = detect_hardware(ALL_DAEMONS[name])

    if hw is None:
        print("This daemon is not applicable for this device", file=sys.stderr)
        sys.exit(1)

    comp_name = get_component_name(name, hw)
    comp_path = get_component_path(comp_name)

    if not comp_path.is_dir():
        print(
            f"Component {comp_name} is not installed for {name} daemon. Path searched: {comp_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    ld_library_path = [
        comp_path / "lib",
    ]
    if "LD_LIBRARY_PATH" in os.environ:
        ld_library_path.extend(os.environ["LD_LIBRARY_PATH"].split(":"))

    path = [
        comp_path / "bin",
    ]

    entry_path = (comp_path / "bin" / name)
    if not entry_path.is_file():
        raise RuntimeError(
            f"No entry path found for {name} daemon. Path searched: {entry_path}"
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
        help="Check if this daemon is applicable and its component is installed on this device and exit.",
    )
    parser.add_argument(
        "--ensure-components",
        action="store_true",
        help="Detect hardware and install required components via snapctl.",
    )
    parser.add_argument("daemon", choices=list(ALL_DAEMONS.keys()), nargs="?", help="The daemon to run.")

    return parser.parse_args()


def main():
    args = parse_args()
    if args.ensure_components:
        ensure_components()
        return

    if not args.daemon:
        print("Error: daemon argument is required unless --ensure-components is given", file=sys.stderr)
        sys.exit(1)

    if args.check:
        check_daemon(args.daemon)
        return

    run_daemon(args.daemon)


if __name__ == "__main__":
    main()
