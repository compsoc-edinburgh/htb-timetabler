import argparse
import logging
import itertools
import os

import pandas

from z3 import *
from Levenshtein import distance # for computing string similarity only

logger = logging.getLogger(__name__)

def sanitize(val, safe="qwertyuiopasdfghjklzxcvbnm1234567890!@#$%^&*()./+=-:;|[]{}"):
    return "".join([c for c in val in c in safe])

class Timetable:
    def __init__(self, tracks):
        self.tracks = tracks
    def as_csv(self):
        for name, track in self.tracks:
            name = name.replace(" ", "_")
            try: 
                os.mkdir("output/", )
            except FileExistsError:
                pass
            with open(f"output/{name}.csv", "w") as f:
                msg = ""
                msg += ",".join(["Timeslot Number", "BUIDL ID", "BUIDL Link", "Team Name", "Discord Contact"])
                for i, sub in enumerate(track):
                    msg += "\n" + ",".join([str(i), str(sub.bid) if sub else "",sub.buidl_link if sub else "", str(sub.name).replace("\n", " ") if sub else "", str(sub.contact).replace("\n", " ") if sub else ""])
                logging.debug(msg)
                f.write(msg)
    def __str__(self):
        msg = ""
        for name, track in self.tracks:
            msg += name
            for sub in track:
                msg += "\n - " + str(sub)
            msg += "\n"
        return msg

class Submission:
    def __init__(self, uid, name, track, contact, bid, buidl_link):
        self.bid = bid
        self.uid = uid
        self.name = name
        self.track = track
        self.contact = contact
        self.buidl_link = buidl_link
    def __str__(self):
        return "Name: " + self.name + " BUIDL ID: " + str(self.bid) + " Contact: " + str(self.contact)

class BadPerfectHash:
    def __init__(self):
        self.state = []
    def get_id(self, val):
        try:
            return self.state.index(val)
        except ValueError:
            self.state.append(val)
            return len(self.state)-1

class Problem:
    def __init__(self, df: pandas.DataFrame, track_shapes=[("HackTheBurgh Challenge", 12), ("G-Research Challenge", 12), ("Huawei Challenge", 12)]):
        self.df = df
        self.submissions = []
        hasher = BadPerfectHash()
        for i, row in df.iterrows():
            tracks = row["Track"].replace('"', "").split(", ")
            for track in tracks:
                submission = Submission(hasher.get_id(row['Team Name:']), row["Team Name:"], track, row["Discord handle:"], row["BUIDL ID"], str(row["BUIDL profile"]))
                self.submissions.append(submission)
        logger.debug([str(s) for s in self.submissions])
        self.track_shapes = track_shapes

    def detect_bad_submissions(self):
        """
        Checks:
        - Finds any duplicate team names in submissions (after removing optiver track submissions)
        - Searches for perceptually similar team names 
        """

        # Detecting direct duplicate team submissions
        logger.debug(self.df)
        submitted_team_names = set([])
        for i, row in self.df.iterrows():
            team_name = str(row['Team Name:'])
            if row["Track"] == 'Optiver Challenge':
                continue
            if team_name not in submitted_team_names:
                submitted_team_names.add(team_name)
            else:
                logger.error(f"Duplicate submission for team \"{team_name}\" detected.")
        
        # Detecting perceptual similarity in team names
        team_names = [str(t) for t in list(set(self.df['Team Name:']))]
        logger.debug(team_names)
        for team1, team2 in itertools.combinations(team_names, 2):
            logger.debug("Comparing %s and %s", team1, team2)
            d = distance(team1, team2)
            logger.debug("Distance is %s", str(d))
            if d < 5:
                logger.warning("Perceptually similar team names detected: %s and %s --- are these the same team?", team1, team2)


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
            combs = itertools.combinations([track_bin[i] for track_bin in track_bins if i < len(track_bin)], 2)
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
            s.add(Or([v == sub.uid for v in track_bin]))
        logger.debug(s)
                
        # Timeslots are unique per track
        for track_bin in track_bins:
            s.add(Distinct([v for v in track_bin]))
        
        if s.check() == sat:
            return track_bins, s.model()
        else:
            return None

    def catch_dumb_errors(self):
        """
        Detects common "dumb errors" and presents with useful error messages.
        """
        track_counts = []
        for track_name, num_slots in self.track_shapes:
            num_track_submissions = len([sub for sub in self.submissions if sub.track == track_name]) 
            if num_track_submissions > num_slots:
                logger.error(f"Impossible problem found: the number of submissions for {track_name} ({num_track_submissions}) > the number of slots {num_slots}")

    def solve_timetable(self) -> Timetable:
        sol = self.z3_solve()
        if not sol:
            logger.error("Unsatisfiable problem, please try adjusting constraints. Try increasing the number of slots.")

        track_bins, solve = sol

        logger.debug(solve)

        # Extract z3 solution into a list of tuples like (track_name, timetabled submissions (or None) in order)
        tracks = [[solve[v] for v in track_bin] for track_bin in track_bins]
        for i, track in enumerate(tracks):
            track_name = self.track_shapes[i][0]
            for j, uid in enumerate(track):
                for sub in self.submissions+[None]:
                    if not sub or (uid == sub.uid and track_name == sub.track):
                        track[j] = sub
                        break
            tracks[i] = (track_name, track)
        logger.debug(tracks)

        # Return parsed solution in a Timetable object
        return Timetable(tracks)

def timetable(track_config, dorahack_export, do_verify=False):
    # Parse track config
    conf_df = pandas.read_csv(track_config)
    tracks = [(row['name'], row['size']) for _, row in conf_df.iterrows()]
    logging.debug(tracks)

    # Parse dorahack export
    df = pandas.read_csv(dorahack_export)
    problem = Problem(df, track_shapes=tracks)
    problem.catch_dumb_errors()
    
    # Verify submissions are actually valid if asked to
    if do_verify:
        problem.detect_bad_submissions()

    # Attempt to solve for a timetable
    timetable = problem.solve_timetable()
    if timetable:
        timetable.as_csv()


def main():
    parser = argparse.ArgumentParser(description='HTB XII Timetabler')
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("-v", "--verify", action="store_true")
    parser.add_argument("-d", "--dorahack_export", help="buidl_export.csv from the DoraHacks portal.")
    parser.add_argument("-t", "--track_config", help="csv formatted configuration for each track")
    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    if args.dorahack_export and args.track_config:
        timetable(args.track_config, args.dorahack_export, do_verify=args.verify)
    else:
        logger.error("Both DoraHack Export and Track Config are required.")


if __name__ == '__main__':
    main()
