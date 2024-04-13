import pprint
from ortools.sat.python import cp_model

from services.Constraint import Constraint
from services.Data import Data


def main() -> None:
    data = Data()
    all_semesters = range(len(data.semesters)) # 1
    all_days = range(len(data.days)) # 5
    all_timeslots = range(len(data.timeslots)) # 10
    all_lecturers = range(len(data.lecturers)) # 9
    all_modules = range(len(data.modules)) # 15
    all_blocks = range(len(data.blocks)) # ???

    # Creates the model.
    model = cp_model.CpModel()
    
    #Create variables
    bools = {}
    for s in all_semesters:
        for d in all_days:
            for t in all_timeslots:
                for m in all_modules:
                    for l in all_lecturers:
                        if (
                            data.lecturers[data.days[d]][l][t] == "1"
                            and data.lecturers["lecturer_id"][l] == data.modules["lecturer_id"][m]
                            and data.semesters[s] == data.modules["semester"][m]
                        ):
                            bools[(s, d, t, m, l)] = model.NewBoolVar(
                                f"course_s{s}_d{d}_t{t}_m{m}_l{l}"
                            )

    constraint = Constraint(bools, model, data)
    constraint.oneModulePerTimeslot()
    constraint.correctSWS()
    constraint.oneModulePerLecturerPerTimeslot()

    # TODO: implement constraint_consecutive_timeslots

    # TODO: lectures that have more than one lecturer are not handled yet (Not MVP worthy)
    
    # TODO: implement create_practice_module function (not MVP worthy)

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
    print(f"  - bools: {solver.NumBooleans()}")
    print(f"  - conflicts: {solver.NumConflicts()}")
    print(f"  - branches : {solver.NumBranches()}")
    print(f"  - wall time: {solver.WallTime()}s")
    # print(model.__dict__)


if __name__ == "__main__":
    main()
    # data = Data()
