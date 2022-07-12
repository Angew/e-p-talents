# Copyright (c) 2022 Petr Kmoch
#
# Distributed under the MIT license, see accompanying LICENSE file

import argparse
from collections import namedtuple
import math
import random
import sys
import xml.etree.ElementTree as ET


class Tier:
    @classmethod
    def from_xml(cls, xml):
        tier = cls(xml.get("name"))
        for ascension in xml.findall("ascension"):
            tier.ascensions.append(int(ascension.text))
        return tier

    def __init__(self, name):
        if not name:
            raise ValueError(f"{self.__class__.__name__} requires valid name")
        self.rarity = int(name)
        self.ascensions = []


class Data:
    @classmethod
    def from_files(cls, filenames):
        data = Data()
        for filename in filenames:
            try:
                data.read(filename)
            except Exception:
                raise
        if not data.tiers:
            raise RuntimeError("No tiers in files")
        return data

    def __init__(self):
        self.tiers = {}

    def read(self, filename):
        xml = ET.parse(filename)
        for xml_tier in xml.getroot().findall("tier"):
            tier = Tier.from_xml(xml_tier)
            self.tiers[tier.rarity] = tier


Step = namedtuple("Step", "xp, chance")

steps = {
    1: Step(180, 2),
    2: Step(468, 4),
}


def compute(ascensions, steps, num_runs, step):
    successes = 0

    for run in range(num_runs):
        asc = ascensions[:]
        level = 1
        while asc:
            do_steps = min(steps, math.ceil(asc[0] / step.xp))
            if random.randrange(100) < do_steps*step.chance:
                level += 1
            if level == 8:
                successes += 1
                break
            asc[0] -= do_steps*step.xp
            if asc[0] <= 0:
                del asc[0]

    print("Steps:", steps, " Odds of maxing:", successes/num_runs*100)


def main(argv):
    parser = argparse.ArgumentParser(
        prog=argv[0],
        description="E&P training evaluator",
    )
    parser.add_argument(
        "-i", "--input",
        help="Database file(s)",
        nargs="*",
        default=[],
    )
    parser.add_argument(
        "-n", "--runs",
        help="Number of runs to simulate",
        type=int,
        default=1000,
    )
    parser.add_argument(
        "goal",
        help="Rarity to evaluate",
        type=int,
        choices=(3, 4, 5),
    )
    parser.add_argument(
        "source",
        help="Rarity to train with",
        type=int,
        choices=(1, 2),
        default=2,
    )
    opt = parser.parse_args(argv[1:])

    data = Data.from_files(["training.xml"] + opt.input)
    goal = opt.goal
    num_runs = opt.runs
    step = steps[opt.source]

    random.seed(0)
    compute(ascensions=data.tiers[goal].ascensions, steps=1, num_runs=num_runs, step=step)
    compute(ascensions=data.tiers[goal].ascensions, steps=10, num_runs=num_runs, step=step)


if __name__ == "__main__":
    main(sys.argv)
