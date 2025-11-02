# HackTheBurgh Timetabler

Basic Usage:
```sh
python3 timetabler.py -d [buidl_export.csv] -t [tracks.csv]
python3 timetabler.py --verify -d [buidl_export.csv] -t [tracks.csv] # Finds non-compliant team submissions
```

## Usage guide

1. Login to DoraHacks, go to the [dashboard](https://dashboard.dorahacks.io/hackathon/hacktheburgh), then to the BUIDLs tab, select all, then export with all fields default selected.
2. Configure the tracks in a file called `tracks.csv`, which should have the names of each of the tracks (to match the track names in DoraHacks), along with the number of timeslots for that track (it's recommended you keep the same number of slots in every track, but that's configurable)
3. Run the script with `python3 timetabler.py -d buidl_export.csv -t tracks.csv --verify`
4. Check for any messages. It will warn you about any similar team names (which may mean two submissions with slightly different spellings of the name) and any teams which should be manually reviewed to ensure that the same team hasn't submitted twice when they shouldn't be (it does automatically remove optiver submissions so it won't warn you about optiver + something else). If it says it's unsatisfiable, you may need to increase the number of timeslots.
5. It will then output a csv for every tracks timetable in the `output/` folder, which can then be imported manually into google sheets if needed.

## Notes

**Timeslots are assumed to be globally sized and running concurrently. i.e. the first timeslot in Track A would run concurrently to the first timeslot in track B and end at the same time.**

The general way this works is by building each track as a list of variables, and using the z3 SAT solver to solve for a satisfiable solution.

You can consider each track like a list of integers, with the shape given in the config file. For instance:
- Track0: `[t00, t00, t02]`
- Track1: `[t10, t11]`
- Track2: `[t20, t21, t22]`

Each of these variables represents a Unique ID of the project presenting. We can then apply the following constraints to build a valid timetable:
- The same team should not be scheduled at the same time on two tracks. For instance, `Track0[0] != Track1[0] and Track1[0] != Track2[0] and Track0[0] != Track2[0]`, and similarly for indexes `1` and `2` (with some bounds checking in this case).
- Every submission should have a timeslot for its track. For instance, `Track0[0] == uid or Track0[1] == uid or Track0[2] == uid`.
- Every timeslot should be unique (i.e. combined with the above means each submission should have EXACTLY ONE timeslot). For instance `Track0[0] != Track0[1] and Track0[1] != Track0[2] and Track0[0] != Track0[2]`, with similar bounds checking as the first constraint.

Once solving this with z3, we can recorrelate the unique IDs with their submission and generate a nice schedule.
