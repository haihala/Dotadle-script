#!/usr/bin/env python
from dataclasses import dataclass

import argparse
import json
import math


def main():
    args = parse_args()
    output = simulate(args.input_file)
    present(args.output_format, args.header, output)


def parse_args():
    parser = argparse.ArgumentParser(
        prog='Dotadle calculator',
        description='Calculates things about https://dotadle.net/'
    )

    parser.add_argument(
        'output_format',
        choices=['csv', 'basic', 'score', 'verbose', 'unambiguous', 'hardest'],
    )
    parser.add_argument('--header', action='store_true')
    parser.add_argument('--input_file', default='dotadle.json')

    return parser.parse_args()


def simulate(input_file):
    handle = open(input_file)
    cont = json.load(handle)
    output = []

    for guess in cont:
        plausibles = {}
        for answer in cont:
            if answer == guess:
                continue

            guess_info = GuessInformation(answer, guess)
            plausibles[answer['championName']] = [
                candidate['championName']
                for candidate in cont
                if guess_info.plausible(candidate) and candidate != guess
            ]

        output.append(Output(guess['championName'], plausibles))

    return output


@dataclass
class ListAttributeInformation:
    exact: bool
    partial: bool


class GuessInformation:
    def __init__(self, answer, guess):
        self.guess = guess
        self.simple_traits = {
            key: answer[key] == guess[key]
            for key in [
                'gender',
                'attribute',
                'rangeType',
                'complexity',
            ]
        }

        if guess['releaseYear'] == answer['releaseYear']:
            self.year_range = [guess['releaseYear']]
        elif guess['releaseYear'] > answer['releaseYear']:
            self.year_range = list(range(2004, guess['releaseYear']))
        else:
            self.year_range = list(range(guess['releaseYear']+1, 2025))

        self.list_traits = {
            key: ListAttributeInformation(
                exact=(set(answer[key]) == set(guess[key])),
                partial=(
                    len(set(answer[key]).intersection(set(guess[key]))) > 0)
            )
            for key in ['species', 'lane']
        }

    def plausible(self, hero):
        for key in [
                'gender',
                'attribute',
                'rangeType',
                'complexity',
        ]:
            if self.simple_traits[key]:
                # Only plausible if exact match
                if hero[key] != self.guess[key]:
                    return False
            else:
                # Only plausible if not a match
                if hero[key] == self.guess[key]:
                    return False

        if hero['releaseYear'] not in self.year_range:
            return False

        for key in ['species', 'lane']:
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


class Output:
    def __init__(self, hero, data):
        self.hero = hero
        self.data = data

        self.average_plausibles = sum(
            len(plausibles)
            for plausibles
            in data.values()
        ) / len(data)

        self.score = sum(
            1/len(plausibles)
            for answer, plausibles
            in data.items()
        )

        self.best_case = math.inf
        self.best_answers = []

        self.worst_case = 0
        self.worst_answers = []

        for answer, plausibles in data.items():
            lp = len(plausibles)

            if lp < self.best_case:
                self.best_case = lp
                self.best_answers = [answer]
            elif lp == self.best_case:
                self.best_answers.append(answer)

            if lp > self.worst_case:
                self.worst_case = lp
                self.worst_answers = [answer]
            elif lp == self.worst_case:
                self.worst_answers.append(answer)

    def present_basic(self):
        print(self.hero)
        print(f'Narrowest plausible pool: {self.best_case}')
        print(f'Narrowest plausible pool answers: {self.best_answers}')
        print(f'Widest plausible pool: {self.worst_case}')
        print(f'Widest plausible pool answers: {self.worst_answers}')
        print(f'Average plausibles: {self.average_plausibles}')
        print(f'Score: {self.score}')
        print()

    def present_verbose(self):
        print(self.hero)
        for pool in range(self.best_case, self.worst_case+1):
            heroes = [
                answer
                for answer, plausibles
                in self.data.items()
                if len(plausibles) == pool
            ]
            if heroes:
                out = ', '.join(heroes)
                print(f'{pool}: {out}')

        print(f'Average plausibles: {self.average_plausibles}')
        print(f'Score: {self.score}')
        print()

    def present_csv(self):
        line = [
            self.hero,
            str(self.best_case),
            ';'.join(self.best_answers),
            str(self.worst_case),
            ';'.join(self.worst_answers),
            str(self.average_plausibles),
            str(self.score),
        ]

        print(','.join(line))

    def present_unambiguous(self):
        unambiguous = {
            answer
            for answer, plausibles
            in self.data.items()
            if plausibles == [answer]
        }
        print(f'{self.hero}: ')
        print(', '.join(unambiguous))
        print()


def present(output_format, header, data):
    if header:
        present_header(output_format)

    present_data(output_format, data)


def present_header(output_format):
    match output_format:
        case 'basic':
            print('Hero name')
            print('Narrowest plausible pool: integer')
            print('Narrowest plausible pool answers: list of heroes')
            print('Widest plausible pool: integer')
            print('Widest plausible pool answers: list of heroes')
            print('Average plausibles: float')
            print('Score: sum of 1/plausibles for all answers, float')

        case 'verbose':
            print('Hero name')
            print('Narrowest plausible pool: integer')
            print('Narrowest plausible pool answers: list of heroes')
            print('Widest plausible pool: integer')
            print('Widest plausible pool answers: list of heroes')
            print('Average plausibles: float')
            print('Score: sum of 1/plausibles for all answers, float')

        case 'csv':
            print(
                ','.join([
                    'Hero',
                    'Best case plausible amount',
                    'Answers with best case plausibles',
                    'Worst case plausible amount',
                    'Answers with worst case plausibles',
                    'Average pool size',
                    'Score(sum of 1/pool size)',
                ]))

        case 'unambiguous':
            print('Guessed hero: ')
            print('Comma separated list of unambiguous answers')

        case 'score':
            print('Scores of heroes, bigger is better')

        case 'hardest':
            print('Average plausibles for each answer, bigger is harder')

    print()


def present_data(output_format, data):
    match output_format:
        case 'basic':
            for result in data:
                result.present_basic()

        case 'verbose':
            for result in data:
                result.present_verbose()

        case 'csv':
            for result in data:
                result.present_csv()

        case 'unambiguous':
            for result in data:
                result.present_unambiguous()

        case 'score':
            ordered = sorted(
                data,
                key=lambda output: -output.score
            )

            for output in ordered:
                print(f'{output.hero}: {output.score}')

        case 'hardest':
            answer_score = {}
            for result in data:
                for answer, plausibles in result.data.items():
                    if answer in answer_score:
                        answer_score[answer] += len(plausibles)
                    else:
                        answer_score[answer] = len(plausibles)

            ordered = sorted(
                answer_score.items(),
                key=lambda pair: pair[1]
            )

            for answer, total in ordered:
                print(f'{answer}: {total/len(answer_score)}')


if __name__ == '__main__':
    main()
