#!/usr/bin/env python
from dataclasses import dataclass
import json
import sys

if len(sys.argv) == 1:
    print("Please provide output mode. One of:")
    print("verbose - human readable output")
    print("csv - csv")
    print("csv-nohead - csv without heading row")
    print("scores - All heroes sorted by their scores")
    exit()

output_mode = sys.argv[1]

handle = open("dotadle.json")
cont = json.load(handle)


@dataclass
class ListAttributeData:
    exact: bool
    partial: bool


class Data:
    def __init__(self, answer, guess):
        self.guess = guess
        self.simple_traits = {
            key: answer[key] == guess[key]
            for key in [
                "gender",
                "attribute",
                "rangeType",
                "complexity",
            ]
        }

        if guess["releaseYear"] == answer["releaseYear"]:
            self.year_range = [guess["releaseYear"]]
        elif guess["releaseYear"] > answer["releaseYear"]:
            self.year_range = list(range(2004, guess["releaseYear"]))
        else:
            self.year_range = list(range(guess["releaseYear"]+1, 2025))

        self.list_traits = {
            key: ListAttributeData(
                exact=(set(answer[key]) == set(guess[key])),
                partial=(
                    len(set(answer[key]).intersection(set(guess[key]))) > 0)
            )
            for key in ["species", "lane"]
        }

    def plausible(self, hero):
        for key in [
                "gender",
                "attribute",
                "rangeType",
                "complexity",
        ]:
            if self.simple_traits[key]:
                # Only plausible if exact match
                if hero[key] != self.guess[key]:
                    return False
            else:
                # Only plausible if not a match
                if hero[key] == self.guess[key]:
                    return False

        if hero["releaseYear"] not in self.year_range:
            return False

        for key in ["species", "lane"]:
            lad = self.list_traits[key]
            if lad.exact:
                # Must match exactly
                if hero[key] != self.guess[key]:
                    return False
            elif lad.partial:
                # Must overlap
                if len(set(hero[key]).intersection(self.guess[key])) == 0:
                    return False

        return True


if output_mode == "verbose":
    print(f"Total heroes {len(cont)}")
elif output_mode == "csv":
    print(
        ",".join([
            "Hero",
            "Best case pool size",
            "Best case hero",
            "Best case pool",
            "Worst case pool size",
            "Worst case hero",
            "Worst case pool",
            "Average pool size",
            "Score(sum of 1/pool size)",
        ]))
elif output_mode == "unambiguous":
    print("Guessed hero: ")
    print("Comma separated list of unambiguous answers")
    print()


scores = {}

for guess in cont:
    pools = {}
    for answer in cont:
        if answer == guess:
            continue

        data = Data(answer, guess)
        plausibles = [
            candidate["championName"]
            for candidate in cont
            if data.plausible(candidate) and candidate != guess
        ]

        pools[answer["championName"]] = plausibles

    best_case = None
    worst_case = None
    sum_case = 0
    score = 0

    for key, plausibles in pools.items():
        value = len(plausibles)
        if best_case is None or value < len(best_case[1]):
            best_case = (key, plausibles)

        if worst_case is None or value > len(worst_case[1]):
            worst_case = (key, plausibles)
        sum_case += value
        score += 1/value

    scores[guess["championName"]] = score

    if output_mode == "verbose":
        print(guess["championName"])
        print(f"Best: {len(best_case[1])} ({best_case[0]})", best_case[1])
        print(f"Worst: {len(worst_case[1])} ({worst_case[0]}", worst_case[1])
        print(f"Average: {sum_case/len(cont)}")
        print(f"Score: {score}")
        print()

    if output_mode.startswith("csv"):
        line = [
            guess["championName"],
            best_case[0],
            str(len(best_case[1])),
            ";".join(best_case[1]),
            worst_case[0],
            str(len(worst_case[1])),
            ";".join(worst_case[1]),
            str(sum_case/len(cont)),
            str(score),
        ]

        print(",".join(line))

    if output_mode == "unambiguous":
        unambiguous = [hero for hero,
                       plausibles in pools.items() if len(plausibles) == 1]

        print(f'{guess["championName"]}: ')
        print(", ".join(unambiguous))
        print()

if output_mode == "score":
    print("Scores of heroes, bigger is better")
    ordered = sorted(
        [(key, value) for key, value in scores.items()],
        key=lambda pair: pair[1]
    )

    for (hero, score) in ordered:
        print(f"{hero}: {score}")
