import argparse
import pandas
import logging
import itertools

from z3 import *

logger = logging.getLogger(__name__)

class Timetable:
    def __init__(self, tracks):
        self.tracks = tracks
    def __str__(self):
        msg = ""
        for name, track in self.tracks:
            msg += name
            for sub in track:
                msg += "\n - " + str(sub)
            msg += "\n"
        return msg

class Submission:
    def __init__(self, bid, name, track, contact):
        self.bid = bid
        self.name = name
        self.track = track
        self.contact = contact
    def __str__(self):
        return "Name: " + self.name + " BUIDL ID: " + str(self.bid) + " Contact: " + self.contact

class Problem:
    def __init__(self, df: pandas.DataFrame, track_shapes=[("HackTheBurgh Challenge", 5), ("G-Research Challenge", 3), ("Huawei Challenge", 6)]):
        self.submissions = []
        for i, row in df.iterrows():
            tracks = row["Track"][1:-1].split(", ")
            for track in tracks:
                #print(row)
                submission = Submission(row["BUIDL ID"], row["BUIDL name"], track, row["Discord handle:"])
                self.submissions.append(submission)
        logger.debug([str(s) for s in self.submissions])
        self.track_shapes = track_shapes

    def detect_bad_submissions(self) -> [str]:
        """
        Teams can only submit one BUIDL (though can submit to multiple tracks)
        The only exception is people can submit a seperate submission to optiver
        This will return any teams who have non-compliant submissions.
        """
        pass

    def z3_solve(self) -> tuple[list[list[Int]], Model]:
        """
        Constraints:
          - Every submission needs a timeslot for its track
          - Every timeslot needs to be unique in its track (i.e. a submission gets EXACTLY ONE timeslots per track)
          - Each team needs non-overlapping timeslots
        """
        s = Solver()

        track_bins = []
        for track_name, track_size in self.track_shapes:
            track_bin = [Int(f"{track_name}_{i}") for i in range(track_size)]
            track_bins.append(track_bin)
        logger.debug(track_bins)

        # Non-overlapping timeslot constraint
        for i in range(max([s[1] for s in self.track_shapes])): # from 0 to the largest index
            combs = itertools.pairwise([track_bin[i] for track_bin in track_bins if i < len(track_bin)])
            for comb1, comb2 in combs:
                s.add(comb1 != comb2)
        logger.debug(s)

        # Each submission gets one timeslot
        for sub in self.submissions:
            for i, (track_name, track_size) in enumerate(self.track_shapes):
                if track_name == sub.track:
                    break
                if i == len(self.track_shapes)-1:
                    raise Exception(f"Unknown track found in data: {sub.track}, please specify track shape.")
            track_bin = track_bins[i]
            s.add(Or([v == sub.bid for v in track_bin]))
        logger.debug(s)
                
        # Timeslots are unique per track
        for track_bin in track_bins:
            s.add(Distinct([v for v in track_bin]))
        
        if s.check() == sat:
            return track_bins, s.model()
        else:
            return None

    def solve_timetable(self) -> Timetable:
        try:
            track_bins, solve = self.z3_solve()
            logger.debug(solve)
            tracks = [[solve[v] for v in track_bin] for track_bin in track_bins]
            for i, track in enumerate(tracks):
                for j, bid in enumerate(track):
                    for sub in self.submissions+[None]:
                        if not sub or bid == sub.bid:
                            track[j] = sub
                            break
                tracks[i] = (self.track_shapes[i][0], track)
            logger.debug(tracks)
            return Timetable(tracks)
        except TypeError:
            logging.error("Unsatisfiable problem!")

def main():
    parser = argparse.ArgumentParser(description='HTB XII Timetabler')
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("-v", "--verify", action="store_true")
    parser.add_argument("-f", "--filename")
    args = parser.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)
    if args.filename:
        df = pandas.read_csv(args.filename)
        problem = Problem(df)
        timetable = problem.solve_timetable()
        print(timetable)
    if args.filename and args.verify:
        print(problem.detect_bad_submissions())


if __name__ == '__main__':
    main()
