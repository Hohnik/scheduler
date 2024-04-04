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

    all_lecturers = range(num_lecturers)
    all_slots = range(num_slots)
    all_days = range(num_days)
    all_modules = range(num_modules)
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
    for d in all_days:
        for s in all_slots:
            for m in all_modules:
                for l in all_lecturers:
                    bools[(d, s, m, l)] = model.NewBoolVar(
                        f"module_m{m}_l{l}_d{d}_s{s}"
                    )

    # Each slot is assigned to exactly one lecturer, module combo.
    for d in all_days:
        for s in all_slots:
            model.AddExactlyOne(
                bools[(d, s, m, l)] for l in all_lecturers for m in all_modules
            )

    # Try to distribute the slots evenly, so that each lecturer works
    # min_slots_per_lecturer slots. If this is not possible, because the total
    # number of slots is not divisible by the number of lecturers, some lecturers will
    # be assigned one more slot.
    # min_slots_per_lecturer = (num_slots * num_days) // num_lecturers
    # if num_slots * num_days % num_lecturers == 0:
    #     max_slots_per_lecturer = min_slots_per_lecturer
    # else:
    #     max_slots_per_lecturer = min_slots_per_lecturer + 1
    # for n in all_lecturers:
    #     num_slots_worked = 0
    #     for d in all_days:
    #         for s in all_slots:
    #             num_slots_worked += slots[(n, d, s)]
    #     model.Add(min_slots_per_lecturer <= num_slots_worked)
    #     model.Add(num_slots_worked <= max_slots_per_lecturer)

    model.Maximize(
        sum(
            preffered_times[d][s] * bools[(d, s, m, l)]
            for m in all_modules
            for l in all_lecturers
            for d in all_days
            for s in all_slots
        )
    )

    pprint.pprint()
    # Creates the solver and solve.
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL:
        print("Solution:")
        for d in all_days:
            print(data.days[d][:3].capitalize())
            for m in all_modules:
                for s in all_slots:
                    for l in all_lecturers:
                        if solver.Value(bools[(d, s, m, l)]) == 1:
                            print(
                                s,
                                data.lecturers[l]["lecturer_name"],
                                data.modules[m]["module_id"],
                            )
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
