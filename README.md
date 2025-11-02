# HackTheBurgh Timetabler

Usage:
```sh
python3 timetabler.py -d [buidl_export.csv] -t [tracks.csv]
python3 timetabler.py --verify -d [buidl_export.csv] -t [tracks.csv] # Finds non-compliant team submissions
```

## Notes

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
