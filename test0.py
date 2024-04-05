from ortools.sat.python import cp_model

from Data import Data


def main() -> None:
    # This program tries to find an optimal assignment of lecturers to slots
    # (3 slots per day, for 7 days), subject to some constraints (see below).
    # Each lecturer can request to be assigned to specific slots.
    # The optimal assignment maximizes the number of fulfilled slot requests.
    data = Data()
    num_lecturers = len(data.lecturers)  # 9
    num_slots = len(data.time_slots)  # 10
    num_days = len(data.days)  # 5
    num_modules = len(data.modules)  # ?
    num_semester = len(data.semesters)  # ?

    all_lecturers = range(num_lecturers)
    all_timeslots = range(num_slots)
    all_days = range(num_days)
    all_modules = range(num_modules)
    all_semesters = range(num_semester)

    slot_requests = [
        [
            list(map(int, lecturer["monday"])),
            list(map(int, lecturer["tuesday"])),
            list(map(int, lecturer["wednesday"])),
            list(map(int, lecturer["thursday"])),
            list(map(int, lecturer["friday"])),
        ]
        for lecturer in data.lecturers
    ]
    # slot_requests = [
    #     [[one bit for each lecturer], [], [], [], [], [], [], [], [], []], -> Monday
    #     [[1, 0, 0, 1, 1, 0, 0, 0, 1], [], [], [], [], [], [], [], [], []], -> Tuesday
    #     [[1, 0, 0, 1, 1, 0, 0, 0, 1], [], [], [], [], [], [], [], [], []], -> Wednesday
    #     [[1, 0, 0, 1, 1, 0, 0, 0, 1], [], [], [], [], [], [], [], [], []], -> Thursday
    #     [[1, 0, 0, 1, 1, 0, 0, 0, 1], [], [], [], [], [], [], [], [], []], -> Friday
    # ]
    preffered_times = [
        [1, 1, 2, 2, 1, 1, 0, 0, 0, 0],
        [1, 2, 3, 3, 2, 2, 1, 1, 0, 0],
        [1, 2, 3, 3, 2, 2, 1, 1, 0, 0],
        [1, 2, 3, 3, 2, 2, 1, 1, 0, 0],
        [0, 1, 2, 2, 1, 1, 0, 0, 0, 0],
    ]

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
                            slot_requests[l][d][t]
                            and data.lecturers[l]["lecturer_id"] in data.modules[m]["lecturer_id"]
                            and data.semesters[s] == data.modules[m]["semester"]
                        ):
                            bools[(s, d, t, m, l)] = model.NewBoolVar(
                                f"course_s{s}_d{d}_t{t}_m{m}_l{l}"
                            )

    # Each slot is assigned to exactly one lecturer, module combo.
    for s in all_semesters:
        for d in all_days:
            for t in all_timeslots:
                try:
                    model.AddAtMostOne([
                        bools[(s, d, t, m, l)] for l in all_lecturers for m in all_modules
                    ])
                except KeyError:
                    pass

    preffered_placement = []
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
    # pprint.pprint()
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL:
        print("Solution:")
        for s in all_semesters:
            for d in all_days:
                print(data.days[d][:3].capitalize())
                for t in all_timeslots:
                    for m in all_modules:
                        for l in all_lecturers:
                            try:
                                if solver.Value(bools[(s, d, t, m, l)]) == 1:
                                    print(
                                        t,
                                        data.lecturers[l]["lecturer_name"],
                                        data.modules[m]["module_id"],
                                    )
                            except KeyError:
                                pass
                print()
        print(
            f"Number of slot requests met = {solver.ObjectiveValue()}",
        )
    else:
        print("No optimal solution found !")

    # Statistics.
    print("\nStatistics")
    print(f"  - conflicts: {solver.NumConflicts()}")
    print(f"  - branches : {solver.NumBranches()}")
    print(f"  - wall time: {solver.WallTime()}s")


if __name__ == "__main__":
    main()
