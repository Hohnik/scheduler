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
    semesters.sort()
    lecturers = lecturers_data
    modules = modules_data
    time_slots = range(10)

    days_num = range(len(days))
    module_ids_num = range(len(module_ids))
    lecturer_ids_num = range(len(lecturer_ids))
    semesters_num = range(len(semesters))
    lecturers_num = range(len(lecturers_data))
    modules_num = range(len(modules_data))

    days_dic = {day: num for num, day in enumerate(days)}
    module_ids_dic = {module_id: num for num, module_id in enumerate(module_ids)}
    lecturer_ids_dic = {lecturer_id: num for num, lecturer_id in enumerate(lecturer_ids)}
    semesters_dic = {semester: num for num, semester in enumerate(semesters)}
    
    

    # Create model
    model = cp_model.CpModel()
    timetable = {}
    for lecturer in lecturers:
        for module in modules:
            for semester in semesters:
                for day in days:
                    for time_slot, bit in enumerate(lecturer[day]):
                        timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot)] = model.NewBoolVar(
                            f'{lecturer["lecturer_id"]}_{module["module_id"]}_{semester}_{day}_{time_slot}'
                        )

    # Define the constraints
    # Lecturers only give lectures when they are free (bit == '1')
    for lecturer in lecturers:
        for module in modules:
            if module["lecturer_id"] == lecturer["lecturer_id"]:
                for day in days:
                    for time_slot, bit in enumerate(lecturer[day]):
                        model.AddImplication(timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[module['semester']], days_dic[day], time_slot)], bit == '1')
        
    # A lecturer cannot be scheduled for two modules at the same time
    for lecturer in lecturers:
        for day in days:
            for time_slot in time_slots:
                    model.AddAtMostOne(timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot)]
                        for semester in semesters
                        for module in modules
                    )

    # Only one module per semester per time_slot
    for semester in semesters:
        for day in days:
            for time_slot in time_slots:
                model.AddAtMostOne(timetable[(lecturer_ids_dic[module["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot)]
                    for module in modules

                    )
    
    # All sws have to be taken
    for module in modules:
        model.Add(cp_model.LinearExpr.Sum([timetable[(lecturer_ids_dic[module["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[module['semester']], days_dic[day], time_slot)]
            for day in days
            for time_slot in time_slots
        ]) == int(module["sws_lu"])  )



    # Solve the model
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    print(solver.StatusName())
    print(solver.NumBooleans(), solver.NumBranches(), solver.NumConflicts())

    # Retrieve the solution
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        for semester in semesters:
            print(f'Semester {semester}:')
            for day in days:
                print(f'{day}:')
                for time_slot in time_slots:
                    for module in modules:
                        lecturer = next((lecturer
                                for lecturer in lecturers
                                if lecturer["lecturer_id"] == module["lecturer_id"]
                            ),
                            None,
                        )
                        
                        if solver.Value(
                            timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot)]
                        ):
                            print(
                                f"At time slot {time_slot} {module['module_id']} is being taught by Lecturer {lecturer['lecturer_name']}"
                            )
            print()

        print("solved")
        return
    else:
        print("No feasible solution found.")
        create_data()
        run_model()

#create_data()
run_model()
