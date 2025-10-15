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
from .daemon import Daemon

SNAP_NAME = os.environ["SNAP_NAME"]

def hardware_list():
    with open("/proc/device-tree/compatible", "rb") as f:
        return set([s.decode("ASCII") for s in f.read().split(b"\0") if s != b''])


def detect_hardware(candidates: List[str]):
    try:
        all_hw = hardware_list()
    except PermissionError:
        print("Insufficient permissions to detect hardware models. Please run this command to fix this problem:", file=sys.stderr)
        print(f"sudo snap connect {SNAP_NAME}:hardware-observe", file=sys.stderr)
        sys.exit(1)

    for comp in all_hw:
        for cand in candidates:
            if comp == f"mediatek,{cand}":
                return cand
    return None


def print_hardware():
    print(hardware_list())


def run_daemon(args, name, hw_variants):
    hw = detect_hardware(hw_variants)
    if args.check:
        if hw is None:
            sys.exit(1)
        else:
            sys.exit(0)

    if hw is None:
        print("This daemon is not applicable for this device", file=sys.stderr)
        sys.exit(1)

    return Daemon(name, hw).run()


def parse_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    mdpd_parser = subparsers.add_parser("mdpd")
    mdpd_parser.add_argument(
        "--check",
        action='store_true',
        help="Check if this daemon is applicable on this device and exit.",
    )
    mdpd_parser.set_defaults(func=lambda args: run_daemon(args, "mdpd", ["mt8365"]))

    vpud_parser = subparsers.add_parser("vpud")
    vpud_parser.add_argument(
        "--check",
        action='store_true',
        help="Check if this daemon is applicable on this device and exit.",
    )
    vpud_parser.set_defaults(
        func=lambda args: run_daemon(args, "vpud", ["mt8365", "mt8188", "mt8395"])
    )

    hardware_probe_parser = subparsers.add_parser("probe")
    hardware_probe_parser.set_defaults(func=lambda _: print_hardware())

    return parser.parse_args()


def main():
    args = parse_args()
    args.func(args)


main()
