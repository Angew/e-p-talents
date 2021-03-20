# Copyright (c) 2021 Petr Kmoch
#
# Distributed under the MIT license, see accompanying LICENSE file

import argparse
from collections import namedtuple
from enum import Enum
from itertools import count, islice, product
import sys
import xml.etree.ElementTree as ET


class Step(Enum):
    TALENT = "talent"
    ATTACK = "attack"
    DEFENSE = "defense"
    HEALTH = "health"
    HEAL = "heal"
    CRITICAL = "critical"
    MANA = "mana"

    @classmethod
    def from_text(cls, text):
        try:
            return [v for k, v in cls.__members__.items() if v.value == text][0]
        except Exception:
            raise ValueError(f"{text} is not a valid {cls.__name__} value")


class TalentCounter(dict):
    def __init__(self):
        super(TalentCounter, self).__init__({step: 0 for step in Step})

    def add(self, rhs):
        if isinstance(rhs, Step):
            self[rhs] += 1
        elif isinstance(rhs, TalentCounter):
            for k, v in rhs.items():
                self[k] += v
        else:
            raise TypeError("Bad type of rhs argument in add()")

    def __repr__(self):
        entries = [
            f"{step}: {count}" for step, count in self.items() if count > 0
        ]
        return "{" + ", ".join(entries) + "}"


class ClassTalents:
    @classmethod
    def from_xml(cls, xml):
        talents = cls(xml.get("name"))
        for step in xml.findall("*"):
            try:
                talents.count.add(Step.from_text(step.tag))
            except ValueError:
                if step.tag == "split":
                    split = []
                    for branch in step.findall("branch"):
                        b = TalentCounter()
                        for s in branch.findall("*"):
                            b.add(Step.from_text(s.tag))
                        split.append(b)
                    talents.branches.append(split)
        return talents

    def __init__(self, name):
        if not name:
            raise ValueError(f"{self.__class__.__name__} requires valid name")
        self.name = name
        self.count = TalentCounter()
        self.branches = []

    def count_path(self, path):
        if len(path) != len(self.branches):
            raise ValueError(
                f"Required path of length {len(self.branches)}, got {len(path)}"
            )
        result = TalentCounter()
        result.add(self.count)
        for split, where in zip(self.branches, path):
            result.add(split[int(where)])
        return result


class Data:
    @classmethod
    def from_files(cls, filenames):
        data = Data()
        for filename in filenames:
            try:
                data.read(filename)
            except Exception:
                raise
        if not data.classes:
            raise RuntimeError("No classes in files")
        return data

    def __init__(self):
        self.classes = {}

    def read(self, filename):
        xml = ET.parse(filename)
        for xml_cls in xml.getroot().findall("class"):
            cls = ClassTalents.from_xml(xml_cls)
            self.classes[cls.name] = cls


Goal = namedtuple("Goal", "cls, priorities")


step_map = {
    "a": Step.ATTACK,
    "c": Step.CRITICAL,
    "d": Step.DEFENSE,
    "h": Step.HEALTH,
    "l": Step.HEAL,
    "m": Step.MANA,
    "t": Step.TALENT,
}


def parse_priorities(string):
    return [step_map[p] for p in string]


def main(argv):
    parser = argparse.ArgumentParser(
        prog=argv[0],
        description="E&P talent evaluator",
    )
    parser.add_argument(
        "-i", "--input",
        help="Database file(s)",
        nargs="*",
        default=[],
    )
    parser.add_argument(
        "goal",
        help="Class and priorities, once or twice",
        nargs="+",
    )
    opt = parser.parse_args(argv[1:])

    data = Data.from_files(["classes.xml"] + opt.input)
    goals = [
        Goal(data.classes[n], parse_priorities(p))
        for n, p in zip(islice(opt.goal, 0, None, 2), islice(opt.goal, 1, None, 2))
    ]
    
    best_paths = list(product(range(2), repeat=7))
    results = {
        path: {g.cls.name: g.cls.count_path(path) for g in goals}
        for path in best_paths
    }
    for idx_priority in range(max((len(g.priorities) for g in goals))):
        for g in goals:
            try:
                prio = g.priorities[idx_priority]
            except IndexError:
                continue
            new_paths = []
            current_max = 0
            for path in best_paths:
                val = results[path][g.cls.name][prio]
                if val > current_max:
                    new_paths = [path]
                    current_max = val
                elif val == current_max:
                    new_paths.append(path)
            best_paths = new_paths
    for path in best_paths:
        print(f"{path}:")
        for g in goals:
            print(f"\t{g.cls.name}:", results[path][g.cls.name])


if __name__ == "__main__":
    main(sys.argv)
