import pprint
from sys import modules
from ortools.sat.python import cp_model

from services.Constraint import Constraint
from services.Data import Data
from services.Printer import Printer


def main() -> None:
    data = Data()
    all_semesters = range(len(data.semesters))  # 1
    all_days = range(len(data.days))  # 5
    all_timeslots = range(len(data.timeslots))  # 10
    all_lecturers = range(len(data.lecturers))  # 9
    all_modules = range(len(data.modules))  # 15

    # Creates the model.
    model = cp_model.CpModel()

    # Create variables
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

    for m in all_modules:
        blocks = calc_blocksizes(int(data.modules["sws"][m]))
        for bidx, b in enumerate(blocks):
            if b == 2:
                for d in all_days:
                    for t in all_timeslots:
                        if t < 9:
                            bools[(m, bidx, d, t)] = model.NewBoolVar(
                                f"course_m{m}_b{b}_d{d}_ts{t}_te{t+1}"
                            )

    constraint = Constraint(bools, model, data)
    constraint.one_module_per_timeslot()
    constraint.correct_sws()
    constraint.one_module_per_lecturer_per_timeslot()
    constraint.consecutive_timeslots()

    # TODO: implement constraint_consecutive_timeslots
    # Wenn 2er-block: stunde vorher nicht mahte --impliziert--> nächste und übernächste stunde ist mathe
    # Hier muss noch gecheckt werden ob wir in einen overflow laufen würden

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
    solution = {}

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        # print("Solution:")
        for s in all_semesters:
            # print(data.semesters[s].capitalize())
            solution.update({data.semesters[s]: {}})
            for d in all_days:
                solution[data.semesters[s]].update({data.days[d]: {}})
                # print(" ", data.days[d].capitalize())
                for t in all_timeslots:
                    # solution[data.semesters[s]][data.days[d]].update({data.timeslots[t]: {}})
                    solution[data.semesters[s]][data.days[d]][t] = {}
                    for m in all_modules:
                        for l in all_lecturers:
                            try:
                                if solver.Value(bools[(s, d, t, m, l)]) == 1:
                                    # print(
                                    #     " ",
                                    #     " ",
                                    #     t,
                                    #     data.lecturers["lecturer_name"][l],
                                    #     data.modules["module_id"][m],
                                    #     # data.modules["module_name"][m],
                                    # )
                                    solution[data.semesters[s]][data.days[d]][t] = {
                                                    "lecturer": data.lecturers["lecturer_name"][l],
                                                    "module": data.modules["module_id"][m]
                                    }

                            except KeyError:
                                pass
                # print()
        print(
            f"h = {solver.ObjectiveValue()}",
        )
        Printer
        printer = Printer()
        printer.set_solution(solution)
        printer.print_lecturer_tables()



    else:
        print("No optimal solution found !")
        print(solver.StatusName())

    # Statistics.
    print("\nStatistics")
    print(f" - bools: {solver.NumBooleans()}")
    print(f" - conflicts: {solver.NumConflicts()}")
    print(f" - branches: {solver.NumBranches()}")
    print(f" - wall time: {solver.WallTime()}s")
    # print(model.__dict__)

def calc_blocksizes(sws: int, blocks=[]) -> list:
    """
    Calculate the best possible combination of blocks.
    """
    if not sws:
        return blocks

    if sws % 2 == 0:
        return calc_blocksizes(sws-2, blocks + [2])

    if sws >= 3:
        return calc_blocksizes(sws-3, blocks + [3])

    if sws == 1:
        return calc_blocksizes(sws-1, blocks + [1])


if __name__ == "__main__":
    main()
    # data = Data()
