import pprint
from ortools.sat.python import cp_model

from services.Data import Data


def main() -> None:
    data = Data()
    num_semester = len(data.semesters)  # 1
    num_days = len(data.days)  # 5
    num_slots = len(data.timeslots)  # 10
    num_lecturers = len(data.lecturers)  # 9
    num_modules = len(data.modules)  # 15

    all_semesters = range(num_semester)
    all_days = range(num_days)
    all_timeslots = range(num_slots)
    all_lecturers = range(num_lecturers)
    all_modules = range(num_modules)


    # Creates the model.
    model = cp_model.CpModel()

    # Creates slot variables.
    # slots[(n, d, s)]: lecturer 'n' works slot 's' on day 'd'.
    bools = {}
    for s in all_semesters:
        for d in all_days:
            for t in all_timeslots:
                for m in all_modules:
                    for l in all_lecturers:
                        if (
                            data.lecturers[data.days[d]][l][t] == "1"
                            and data.lecturers["lecturer_id"][l] in data.modules["lecturer_id"]
                            and data.semesters[s] == data.modules["semester"][m]
                        ):
                            bools[(s, d, t, m, l)] = model.NewBoolVar(
                                f"course_s{s}_d{d}_t{t}_m{m}_l{l}"
                            )

    # Each slot is assigned to exactly one lecturer, module combo.
    for s in all_semesters:
        for d in all_days:
            for t in all_timeslots:
                combo = []
                for m in all_modules:
                    for l in all_lecturers:
                        if (s, d, t, m, l) in bools.keys():
                            combo.append(bools[(s, d, t, m, l)])
                model.AddAtMostOne(combo)

    # TODO: a lecturer cannot be scheduled for two modules at the same time

    # TODO: a module is placed exactly sws's times

    # TODO: lectures that have more than one lecturer are not handled yet

    # TODO: blockplacements not MVP worthy (felix)

    # Apply heuristic
    preffered_placement = []
    preffered_times = [
        [2, 2, 3, 3, 2, 2, 1, 1, 1, 1],
        [2, 3, 4, 4, 3, 3, 2, 2, 1, 1],
        [2, 3, 4, 4, 3, 3, 2, 2, 1, 1],
        [2, 3, 4, 4, 3, 3, 2, 2, 1, 1],
        [1, 2, 3, 3, 2, 2, 1, 1, 1, 1],
    ]
    for m in all_modules:
        for l in all_lecturers:
            for d in all_days:
                for t in all_timeslots:
                    for s in all_semesters:
                        try:
                            preffered_placement.append(preffered_times[d][t] * bools[(s, d, t, m, l)])
                        except KeyError: 
                            pass
    model.Maximize(sum(preffered_placement))

    # Creates the solver and solve.
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL:
        print("Solution:")
        for s in all_semesters:
            for d in all_days:
                print(data.days[d].capitalize())
                for t in all_timeslots:
                    for m in all_modules:
                        for l in all_lecturers:
                            try:
                                if solver.Value(bools[(s, d, t, m, l)]) == 1:
                                    print(
                                        " ",
                                        t,
                                        data.lecturers["lecturer_name"][l],
                                        data.modules["module_id"][m],
                                    )
                            except KeyError:
                                pass
                print()
        print(
            f"h = {solver.ObjectiveValue()}",
        )
    else:
        print("No optimal solution found !")

    # Statistics.
    print("\nStatistics")
    print(f"  - conflicts: {solver.NumConflicts()}")
    print(f"  - branches : {solver.NumBranches()}")
    print(f"  - wall time: {solver.WallTime()}s")
    # print(model.__dict__)


if __name__ == "__main__":
    main()
