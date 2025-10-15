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
from typing import List
from .daemon import Daemon


def detect_hardware(candidates: List[str]):
    with open("/proc/device-tree/compatible", "rb") as f:
        compatible_list = set([s.decode("ASCII") for s in f.read().split(b"\0")])

    for comp in compatible_list:
        for cand in candidates:
            if comp == f"mediatek,{cand}":
                return cand
    return None



def run_daemon(args, name, hw_variants):
    hw = detect_hardware(hw_variants)
    if args.check:
        if hw is None:
            sys.exit(1)
        else:
            sys.exit(0)

    if hw is None:
        raise RuntimeError("This daemon is not applicable for this device")

    return Daemon(name, hw).run()

def parse_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    mdpd_parser = subparsers.add_parser("mdpd")
    mdpd_parser.add_argument("--check", type=bool, help="Check if this daemon is applicable on this device and exit.")
    mdpd_parser.set_defaults(func=lambda args: run_daemon(args, "mdpd", ["mt8365"]))

    vpud_parser = subparsers.add_parser("vpud")
    vpud_parser.add_argument("--check", type=bool, help="Check if this daemon is applicable on this device and exit.")
    vpud_parser.set_defaults(func=lambda args: run_daemon(args, "vpud", ["mt8365", "mt8188", "mt8395"]))

    hardware_probe_parser = subparsers.add_parser("probe")
    hardware_probe_parser.set_defaults(func=lambda: print(detect_hardware()))

    return parser.parse_args()


def main():
    args = parse_args()
    args.func(args)


main()
