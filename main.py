import pandas as pd
from ortools.sat.python import cp_model

from generate_lecturer_data import create_data

#INFO: Remove sws_pu and participants_lu from modules.csv file and create new modules instead

def run_model():
    lecturers_df = pd.read_csv("db/lecturers.csv", dtype=str)
    modules_df = pd.read_csv("db/modules.csv", dtype=str)
    rooms_df = pd.read_csv("db/rooms.csv", dtype=str)

    lecturers_data = lecturers_df.to_dict(orient="records")
    modules_data = modules_df.to_dict(orient="records")
    rooms_data = rooms_df.to_dict(orient="records")

    lecturers = lecturers_data
    modules = modules_data
    rooms = rooms_data
    
    lecturer_ids = [dct["lecturer_id"] for dct in lecturers_data]
    module_ids = [dct["module_id"] for dct in modules_data]
    room_ids = [dct["room_id"] for dct in rooms_data]
    
    semesters = list(set([dct["semester"] for dct in modules_data]))
    semesters.sort()
    days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    time_slots = range(10)

    lecturers_num = range(len(lecturers_data))
    modules_num = range(len(modules_data))
    lecturer_ids_num = range(len(lecturer_ids))
    module_ids_num = range(len(module_ids))
    semesters_num = range(len(semesters))
    days_num = range(len(days))

    lecturer_ids_dic = {lecturer_id: num for num, lecturer_id in enumerate(lecturer_ids)}
    module_ids_dic = {module_id: num for num, module_id in enumerate(module_ids)}
    room_ids_dic = {room_id: num for num, room_id in enumerate(room_ids)}
    semesters_dic = {semester: num for num, semester in enumerate(semesters)}
    days_dic = {day: num for num, day in enumerate(days)}
    
    
    

    # Create model
    model = cp_model.CpModel()
    timetable = {}
    for lecturer in lecturers:
        for module in modules:
            for semester in semesters:
                for day in days:
                    for time_slot, bit in enumerate(lecturer[day]):
                        for room in rooms:
                            timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]])] = model.NewBoolVar(
                                f'{lecturer["lecturer_id"]}_{module["module_id"]}_{semester}_{day}_{time_slot}'
                            )

    # Define the constraints
    # Lecturers only give lectures when they are free (bit == '1')
    for lecturer in lecturers:
        for module in modules:
            if module["lecturer_id"] == lecturer["lecturer_id"]:
                for day in days:
                    for time_slot, bit in enumerate(lecturer[day]):
                        model.AddImplication(timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[module["semester"]], days_dic[day], time_slot, room_ids_dic[room["room_id"]])], bit == "1")
        
    # A lecturer cannot be scheduled for two modules at the same time
    for lecturer in lecturers:
        for day in days:
            for time_slot in time_slots:
                model.AddAtMostOne(timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]])]
                    for module in modules
                )

    # Only one module per semester per time_slot
    for semester in semesters:
        for day in days:
            for time_slot in time_slots:
                model.AddAtMostOne(timetable[(lecturer_ids_dic[module["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]])]
                    for module in modules

                )
    
    # All sws have to be taken
    for module in modules:
        model.Add(cp_model.LinearExpr.Sum([timetable[(lecturer_ids_dic[module["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[module["semester"]], days_dic[day], time_slot, room_ids_dic[room["room_id"]])]
            for day in days
            for time_slot in time_slots
        ]) == int(module["sws_lu"])  )

#    # A room cannot be scheduled for two modules at the same time
#    for day in days:
#       for time_slot in time_slots:
#            for room in rooms:
#                model.AddAtMostOne(timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]])]
#                for module in modules
#                )
#
#    # A module cannot be scheduled for two rooms at the same time
#    for day in days:
#        for time_slot in time_slots:
#            for module in modules:
#                model.AddAtMostOne(timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[module["semester"]], days_dic[day], time_slot, room_ids_dic[room["room_id"]])]
#                    for room in rooms
#                )


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
                        for room in rooms:
                            lecturer = next((lecturer
                                    for lecturer in lecturers
                                    if lecturer["lecturer_id"] == module["lecturer_id"]
                                ),
                                None,
                            )
                            
                            if solver.Value(
                                timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]])]
                            ):
                                print(
                                    f'At time slot {time_slot} {module["module_id"]} is being taught in room {room["room_id"]} by Lecturer {lecturer["lecturer_name"]}'
                                )
            print()

        print("solved")
        print(solver.StatusName())
        print(solver.NumBooleans(), solver.NumBranches(), solver.NumConflicts())
        print(room_ids_dic)
        return
    else:
        print("No feasible solution found.")
        create_data()
        run_model()

create_data()
run_model()
