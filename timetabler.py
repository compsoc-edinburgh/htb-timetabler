import argparse
import enum

class Timetable:
    def __str__(self):
        pass

class Problem:
    # Constraints: 
    # - Every submission needs a timeslot for its track
    # - Each team needs non-overlapping timeslots
    def solve_timetable(self) -> Timetable:
        pass

def parse(content: str) -> Problem:
    pass

def readfile(filename: str) -> str:
    with open(filename, "r") as f:
        return f.read()

def main():
    parser = argparse.ArgumentParser(description='HTB XII Timetabler')
    parser.add_argument("-f", "--filename")
    args = parser.parse_args()
    if args.filename:
        content = readfile(args.filename)
        problem = parse(content)
        timetable = problem.solve_timetable()
        print(timetable)



if __name__ == '__main__':
    main()
