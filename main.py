import pandas as pd
from ortools.sat.python import cp_model

from generate_lecturer_data import create_data

#INFO: Remove sws_pu and participants_lu from modules.csv file and create new modules instead

def run_model():
    lecturers_df = pd.read_csv("db/lecturers.csv", dtype=str)
    modules_df = pd.read_csv("db/modules.csv", dtype=str)

    lecturers_data = lecturers_df.to_dict(orient="records")
    modules_data = modules_df.to_dict(orient="records")

    days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    module_ids = [dct["module_id"] for dct in modules_data]
    lecturer_ids = [dct["lecturer_id"] for dct in lecturers_data]
    semesters = list(set([dct["semester"] for dct in modules_data]))
    lecturers = lecturers_data
    modules = modules_data

    days_num = range(len(days))
    module_ids_num = range(len(module_ids))
    lecturer_ids_num = range(len(lecturer_ids))
    semesters_num = range(len(semesters))
    lecturers_num = range(len(lecturers_data))
    modules_num = range(len(modules_data))

    # Create model
    model = cp_model.CpModel()
    timetable = {}
    for lecturer in lecturers:
        for lecturer_id in lecturer_ids_num:
            for module_id in module_ids_num:
                for semester in semesters_num:
                    for day in days_num:
                        for time_slot, bit in enumerate(lecturer[days[day]]):
                            if bit == "1":
                                timetable[(lecturer_id, module_id, semester, day, time_slot)] = model.NewBoolVar(
                                    f"{lecturer_id}_{module_id}_{semester}_{day}_{time_slot}"
                                )

    # Define the constraints
    # Lecturers cannot be scheduled for two modules at the same time
    for lecturer in lecturers:
        for lecturer_id in lecturer_ids_num:
            for semester in semesters_num:
                for day in days_num:
                    for time_slot, bit in enumerate(lecturer[days[day]]):
                        if bit == "1":
                            model.AddAtMostOne(timetable[(lecturer_id, module_id, semester, day, time_slot)]
                                for module_id in module_ids_num
                            )

    # Only one module per semester per time_slot
    for lecturer in lecturers:
        for lecturer_id in lecturer_ids_num:
            for module_id in module_ids_num:
                for _, bit in enumerate(lecturer[days[day]]):
                    if bit == "1":
                        model.AddAtMostOne(timetable[(lecturer_id, module_id, semester, day, time_slot)]
                            for semester in semesters_num
                            for day in days_num
                            for time_slot in range(10)
                        )
    
    # All sws have to be taken
    for module in modules:
        for lecturer in lecturers:
            for lecturer_id in lecturer_ids_num:
                for module_id in module_ids_num:
                    for semester in semesters_num:
                        for _, bit in enumerate(lecturer[days[day]]):
                            if bit == "1":
                                model.Add(cp_model.LinearExpr.Sum([timetable[(lecturer_id, module_id, semester, day, time_slot)]
                                    for day in days_num
                                    for time_slot in range(10)
                                ]) == int(module["sws_lu"]) * 2 )



    # Solve the model
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    print(status)
    print(solver.StatusName())
    print(solver.NumBooleans(), solver.NumBranches(), solver.NumConflicts())
    # Retrieve the solution
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        for lecturer in lecturers:
            for lecturer_id in lecturer_ids_num:
                for module_id in module_ids_num:
                    for semester in semesters_num:
                        for day in days_num:
                            for time_slot, bit in enumerate(lecturer[days[day]]):
                                if solver.Value(timetable[(lecturer_id, module_id, semester, day, time_slot)]):
                                    print("Solved correctly with some value??!?!?")
        # for module in modules_data:
        #     lecturer_id = next((lecturer
        #             for lecturer in lecturers_data
        #             if lecturer["lecturer_id"] == module["lecturer_id"]
        #         ),
        #         None,
        #     )
        #                     if solver.Value(
        #                         timetable[(module["lecturer_id"], day, time_slot)]
        #                     ):
        #                         print(
        #                             f"Lecturer {lecturer_id['lecturer_name']} is teaching {module['module_name']} on {day} at time slot {time_slot}"
        #                         )
        print("ran")
        return
    else:
        print("No feasible solution found.")
        # create_data()
        # run_model()


run_model()
