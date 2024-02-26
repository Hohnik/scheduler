# by Niklas Hohn & Julien Sauter

import pprint
import pandas as pd
from ortools.sat.python import cp_model

from utils.generate_lecturer_data import create_data

#INFO: all for loops above contraint are consumed, and all for loops in constraint are chosen/reused

#TODO: remove sws_pu and participants_lu from modules.csv file and create new modules instead
#TODO: for performance try to merge contraints into one for loop struct (save previous for loop values)
#TODO: if necessary, add gender, etc. to lecturers for german spelling and other information

#HEURISTIC: for each lecturer, Optimise: less days -OR- shorter periods -OR- more breaks
#HEURISTIC: for each semester for each day, Optimise: same room for as long as possible
#HEURISTIC: for each semester for each day, Optimise: lower walking distance (add Mensa as room for break time) (same building -OR- room_coordinates with manhattan/euclidean distance)

def run_model():
    lecturers_df = pd.read_csv("db/lecturers.csv", dtype=str)
    modules_df = pd.read_csv("db/modules_no_p.csv", dtype=str)
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
                    for time_slot in time_slots:
                        for room in rooms:
                            timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]])] = model.NewBoolVar(
                                f'{lecturer["lecturer_id"]}_{module["module_id"]}_{semester}_{day}_{time_slot}'
                            )

    print(len(timetable))

    # Define the constraints
    # Implied that lecturers only give lectures if time_slot bit == "1" | Lecturers only give lectures when they are free (bit == "1")
    for lecturer in lecturers:
        for module in modules:
            for semester in semesters:
                for day in days:
                    for time_slot, bit in enumerate(lecturer[day]):
                        for room in rooms:
                            model.AddImplication(timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]])],
                                bit == "1"
                                )

    # Implied for every module that module["lecturer_id"] == lecturer["lecturer_id"]
    for lecturer in lecturers:
        for module in modules:
            for semester in semesters:
                for day in days:
                    for time_slot in time_slots:
                        for room in rooms:
                            model.AddImplication(timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]])],
                                module["lecturer_id"] == lecturer["lecturer_id"]
                                )

    # Implied for every module that semester == module["semester"]
    for lecturer in lecturers:
        for module in modules:
            for semester in semesters:
                for day in days:
                    for time_slot in time_slots:
                        for room in rooms:
                            model.AddImplication(timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]])],
                                semester == module["semester"]
                                )

    # At most one room per module per time_slot | Every room and time_slot only gets one module
    for day in days:
        for time_slot in time_slots:
            for room in rooms:
                model.AddAtMostOne(timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]])]
                for lecturer in lecturers
                for module in modules
                for semester in semesters
                )

    # At most one module per lecturer per time_slot | A lecturer cannot be scheduled for two modules at the same time
    for lecturer in lecturers:
        for day in days:
            for time_slot in time_slots:
                model.AddAtMostOne(timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]])]
                for module in modules
                for semester in semesters
                for room in rooms
                )

    # At most one module per semester per time_slot
    for semester in semesters:
        for day in days:
            for time_slot in time_slots:
                model.AddAtMostOne(timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]])]
                for lecturer in lecturers
                for module in modules
                for room in rooms
                )
    
    # Sum( time_slots for module ) == module["sws"] | All sws have to be taken
    for module in modules:
        model.Add(cp_model.LinearExpr.Sum([timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]])]
            for lecturer in lecturers
            for semester in semesters
            for day in days
            for time_slot in time_slots
            for room in rooms
        ]) == int(module["sws"]) * 2)



    # Solve the model
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    print( f"Status:{solver.StatusName()}",f"Bools:{solver.NumBooleans()}", f"Branches:{solver.NumBranches()}", f"Conflicts:{solver.NumConflicts()}", sep="\n", end="\n\n")
    solution = {}
    # Retrieve the solution
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        available_rooms_dic = {(day, time_slot): [room_id for room_id in room_ids]
                               for day in days
                               for time_slot in time_slots
                               }
        for semester in semesters:
            solution.update({semester:{}})
            print(f'Semester {semester}:')
            for day in days:
                print(f'{day}:')
                solution[semester].update({day:{}})
                for time_slot in time_slots:
                    solution[semester][day].update({time_slot:[]})
                    for lecturer in lecturers:
                        for module in modules:
                            for room in rooms:
                                
                                if solver.Value(timetable[(
                                        lecturer_ids_dic[lecturer["lecturer_id"]], 
                                        module_ids_dic[module["module_id"]],
                                        semesters_dic[semester], 
                                        days_dic[day], 
                                        time_slot, 
                                        room_ids_dic[room["room_id"]])]):

                                    available_rooms_dic[(day, time_slot)].remove(room["room_id"])
                                    solution[semester][day][time_slot].append([module["module_id"], lecturer["lecturer_id"]])
                                    print(
                                        #f'At time slot {time_slot} {module["module_id"]} is being taught in room {room["room_id"]} by Lecturer {lecturer["lecturer_name"]}'
                                        f'An Zeitpunkt {time_slot} wird {module["module_id"]} unterrichtet in Raum {room["room_id"]} von Professor {lecturer["lecturer_name"]}'
                                    )
                    
            print()
        
        pprint.pprint(solution)

        print(numof_available_rooms(available_rooms_dic, days, time_slots))
        return
    else:
        print("No feasible solution found.")
        create_data()
        run_model()


# number of available rooms per time_slot
def numof_available_rooms(available_rooms_dic, days, time_slots):
    numof_available_rooms_lst = [len(available_rooms_dic[(day, time_slot)]) for day in days for time_slot in time_slots]
    n_a_r_l_dic = {}
    for elem in numof_available_rooms_lst:
        if elem in n_a_r_l_dic:
            n_a_r_l_dic[elem] += 1
        else:
            n_a_r_l_dic[elem] = 1
    return n_a_r_l_dic
    

create_data()
run_model()
