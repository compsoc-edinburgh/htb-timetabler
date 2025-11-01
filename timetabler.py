import argparse
import enum
import pandas

from z3 import *

class Timetable:
    def __str__(self):
        pass

class Problem:
    def __init__(self, df: pandas.DataFrame):
        pass

    # Teams can only submit one BUIDL (though can submit to multiple tracks)
    # The only exception is people can submit a seperate submission to optiver
    # This will return any teams who have non-compliant submissions.
    def detect_bad_submissions(self) -> [str]:
        pass

    # Constraints: 
    # - Every submission needs a unique timeslot for its track
    # - Each team needs non-overlapping timeslots
    def solve_timetable(self) -> Timetable:
        pass

def main():
    parser = argparse.ArgumentParser(description='HTB XII Timetabler')
    parser.add_argument("-v", "--verify", action="store_true")
    parser.add_argument("-f", "--filename")
    args = parser.parse_args()
    if args.filename:
        df = pandas.read_csv(args.filename)
        problem = Problem(df)
        timetable = problem.solve_timetable()
        print(timetable)
    if args.filename and args.verify:
        print(problem.detect_bad_submissions())


if __name__ == '__main__':
    main()
