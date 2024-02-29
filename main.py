# by Niklas Hohn & Julien Sauter

import pprint
import pandas as pd
from ortools.sat.python import cp_model

from ortools.sat.python.cp_model import IntVar

import utils.generate_lecturers_data as gld
import utils.generate_modules_data as gmd
from utils.table_printer import TablePrinter

# INFO: all for loops above contraint are consumed, and all for loops in constraint are chosen/reused (over what values do i want to run again and again?)

# TODO IMPORTANT: time_slots are currently treated as 60 minute windows, even though they are 45 min. This drastically changes how we have to check if sws per module are being taught. >= won't be enough because we don't want to overbook modules.

# TODO tidy up code, create classes and methods, OOP
# TODO for performance try to merge contraints into one for loop struct (save previous for loop values)
# TODO if necessary, add gender, etc. to lecturers for german spelling and other information
# TODO implement print function (or equivalent/analogous output) in different languages
# TODO MAYBE: Let courses define more accurately what they need in a room, instead of just lecture vs practice

# HEURISTIC for each module, Optimise: same room (same room -OR- constraint modules are always same room)
# HEURISTIC for each lecturer, Optimise: less days -OR- shorter periods -OR- more breaks
# HEURISTIC for each semester for each day, Optimise: same room for as long as possible
# HEURISTIC for each semester for each day, Optimise: lower walking distance (add Mensa as room for break time) (same building -OR- room_coordinates with manhattan/euclidean distance -OR- constraint courses have specific buildings)
# HEURISTIC for each module for each room, Optimise: just over half full rooms (normal distribution, slightly right-skewed)

def main():
    gld.generate_data()
    gmd.create_data()
    result_object = run_model()
    printer = TablePrinter(result_object)
    printer.print_semester_tables()


def run_model():
    # Read in data file
    lecturers= read_data_from("db/lecturers.csv")
    modules = read_data_from("db/modules.csv")
    rooms = read_data_from("db/rooms.csv")

    # Generate praktika
    # TODO What is this code doing? Can it be moved into a function? Does it just generate data or is it modifying data? @Julio
    for module_p in modules:
        if module_p["module_id"][0] == "p":
            for module_l in modules:
                if module_l["module_id"][0] == "l" and module_p["module_id"][1:] == module_l["module_id"][1:]:
                    numof_prak = (int(module_l["participants"]) // 20) + 1
                    remaining_participants = int(module_l["participants"])
                    for num in range(numof_prak):
                        module_p_copy = module_p.copy()
                        module_p_copy["module_id"] = module_p_copy["module_id"] + '_' + str(num+1)

                        participants = remaining_participants // numof_prak
                        module_p_copy["participants"] = str(participants)
                        remaining_participants -= participants
                        numof_prak -= 1
                        modules.append(module_p_copy)

                    modules.remove(module_p)

    # Create id dictionary
    lecturer_ids = [lecturer["lecturer_id"] for lecturer in lecturers]
    module_ids = [module["module_id"] for module in modules]
    room_ids = [room["room_id"] for room in rooms]

    semesters = list(set([module["semester"] for module in modules]))
    semesters.sort()
    days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    time_slots = range(len(lecturers[0][days[0]]))
    # time_slot_times = ["8:45-9:30","9:30-10:15","10:30-11:15","11:15-12:00","12:50-13:35","13:35-14:20","14:30-15:15","15:15-16:00","16:10-16:55","16:55-17:40","17:50-18:35","18:35-19:20","19:30-20:15","20:15-21:00"]

    # Link ids to int values


    data = {
        "lecturers": lecturers,
        "modules": modules,
        "semesters": semesters,
        "days": days,
        "time_slots": time_slots,
        "rooms": rooms,
    }

    data_idx = {
        "lecturers":{lecturer_id: num for num, lecturer_id in enumerate(lecturer_ids)},
        "modules": {module_id: num for num, module_id in enumerate(module_ids)},
        "semesters": {semester: num for num, semester in enumerate(semesters)},
        "days": {day: num for num, day in enumerate(days)},
        "rooms": {room_id: num for num, room_id in enumerate(room_ids)},
    }

    lecturer_idx = data_idx["lecturers"]
    module_idx = data_idx["modules"]
    semester_idx  = data_idx["semesters"]
    day_idx  = data_idx["days"]
    room_idx  = data_idx["rooms"]


    def generate_vars(model, data, data_idx):
        vars = {}
        for lecturer in data["lecturers"]:
            for module in data["modules"]:
                for semester in data["semesters"]:
                    for day in data["days"]:
                        for time_slot in data["time_slots"]:
                            for room in data["rooms"]:
                                vars[
                                    (
                                        data_idx["lecturers"][lecturer["lecturer_id"]],
                                        data_idx["modules"][module["module_id"]],
                                        data_idx["semesters"][semester],
                                        data_idx["days"][day],
                                        time_slot,
                                        data_idx["rooms"][room["room_id"]],
                                    )
                                ] = model.NewBoolVar(
                                    f'{lecturer["lecturer_id"]}_{module["module_id"]}_{semester}_{day}_{time_slot}_{room["room_id"]}'
                                )

        print("Variables: ", len(vars))
        return vars

    # Add course to module dictionary
    # TODO string slicing is kinda wanky :D regex?
    for module in modules:
        module["course"] = module["module_id"][1:3]

    # Create model
    model = cp_model.CpModel()
    timetable = generate_vars(model, data, data_idx)

    # Define the constraints
    for lecturer in lecturers:
        for module in modules:
            for semester in semesters:
                for day in days:
                    for time_slot, bit in enumerate(lecturer[day]):
                        for room in rooms:

                            # Implied for every lecturer for every time_slot that time_slot bit == "1" | lecturers only give lectures when they are free (bit == "1")
                            model.AddImplication(timetable[(lecturer_idx[lecturer["lecturer_id"]], module_idx[module["module_id"]], semester_idx[semester], day_idx[day], time_slot, room_idx[room["room_id"]])],
                                bit == "1"
                                )

                            # Implied for every module that lecturer["lecturer_id"] in module["lecturer_id"] | modules can only be taught by their corresponding lecturer
                            model.AddImplication(timetable[(lecturer_idx[lecturer["lecturer_id"]], module_idx[module["module_id"]], semester_idx[semester], day_idx[day], time_slot, room_idx[room["room_id"]])],
                                lecturer["lecturer_id"] in module["lecturer_id"]
                                )

                            # Implied for every module that semester == module["semester"] | modules linked to respective semesters
                            model.AddImplication(timetable[(lecturer_idx[lecturer["lecturer_id"]], module_idx[module["module_id"]], semester_idx[semester], day_idx[day], time_slot, room_idx[room["room_id"]])],
                                semester == module["semester"]
                                )

                            # Implied for every room that room["capacity"] >= module["participants"] | room has enough space for the module
                            model.AddImplication(timetable[(lecturer_idx[lecturer["lecturer_id"]], module_idx[module["module_id"]], semester_idx[semester], day_idx[day], time_slot, room_idx[room["room_id"]])],
                                room["capacity"] >= module["participants"]
                                )

                            # Implied for every room that module["module_id"][0] == room["room_type"] | room type fits to module type
                            model.AddImplication(timetable[(lecturer_idx[lecturer["lecturer_id"]], module_idx[module["module_id"]], semester_idx[semester], day_idx[day], time_slot, room_idx[room["room_id"]])],
                                module["module_id"][0] == room["room_type"]
                                )

    def calculate_session_blocks(leftover_sws:str):
        #return [1]
        session_blocks = []
        leftover_sws = int(leftover_sws)
        while leftover_sws > 0:
            if leftover_sws % 2 == 0:
                leftover_sws -= 2
                session_blocks.append(2)
            elif leftover_sws >= 3:
                leftover_sws -= 3
                session_blocks.append(3)
            elif leftover_sws == 1:
                leftover_sws -= 1
                session_blocks.append(1)

        return session_blocks

    # | All modules should be in blocks of consecutive time_slots if possible (if leftover_sws % 2 == 0: block_size = 2, elif leftover_sws >= 3: block_size = 3, elif leftover_sws == 1: block_size = 1 else: )
    for lecturer in lecturers:
        #print(lecturer["lecturer_id"])
        for module in modules:
            session_blocks = calculate_session_blocks(module["sws"])
            for block_size in session_blocks:
                for semester in semesters:
                    if semester == module["semester"]:
                        for day in days:
                            for time_slot, bit in range(time_slots):  # Adjust based on block size
                                if time_slot < len(lecturer[day]) - block_size + 1:
                                    for room in rooms:
                                        
                                        l = lecturer_ids_dic[lecturer["lecturer_id"]]
                                        m = module_ids_dic[module["module_id"]]
                                        s = semesters_dic[semester]
                                        d = days_dic[day]
                                        t = time_slot
                                        r = room_ids_dic[room["room_id"]]
                                        
                                        block_bool_vars:list[IntVar] = [timetable[(l, m, s, d, t+offset, r)] for offset in range(block_size)]

                                        for offset in range(1, block_size):
                                            if lecturer[day][time_slot+offset] == "0":
                                                for var in block_bool_vars:
                                                    model.Add(var == 0)  # If lecturer is not available, block cannot be scheduled
                                                                                
                                        model.Add(sum(block_bool_vars) == block_size).OnlyEnforceIf(block_bool_vars)

                                else:
                                    for offset in range(block_size):
                                        model.AddHint(timetable[(l, m, s, d, t, r)])

#region
    # # | All modules should be in blocks of consecutive time_slots if possible (if leftover_sws % 2 == 0: block_size = 2, elif leftover_sws >= 3: block_size = 3, elif leftover_sws == 1: block_size = 1 else: )
    # for lecturer in lecturers:
    #     #print(lecturer["lecturer_id"])
    #     for module in modules:
    #         session_blocks = calculate_session_blocks(module["sws"])
    #         for block_size in session_blocks:
    #             for semester in semesters:
    #                 if semester == module["semester"]:
    #                     for day in days:
    #                         for time_slot, bit in enumerate(lecturer[day][:len(time_slots) - block_size + 1]):  # Adjust based on block size
    #                             if time_slot < len(lecturer[day]) - block_size + 1:
    #                                 for room in rooms:
                                        
    #                                     l = lecturer_ids_dic[lecturer["lecturer_id"]]
    #                                     m = module_ids_dic[module["module_id"]]
    #                                     s = semesters_dic[semester]
    #                                     d = days_dic[day]
    #                                     t = time_slot
    #                                     r = room_ids_dic[room["room_id"]]
                                        
    #                                     block_bool_vars:list[IntVar] = [timetable[(l, m, s, d, t+offset, r)] for offset in range(block_size)]

    #                                     for offset in range(1, block_size):
    #                                         if lecturer[day][time_slot+offset] == "0":
    #                                     #        print(block_bool_vars)
    #                                             for var in block_bool_vars:
    #                                     #            print('not free')
    #                                                 model.Add(var == 0)  # If lecturer is not available, block cannot be scheduled
    #                                     #    print('free')
                                        
    #                                     #print(block_size)
    #                                     model_test = model.Add(sum(block_bool_vars) == block_size).OnlyEnforceIf(block_bool_vars)
    #                                     if model_test:
    #                                         ...
    #                                     #    print(model_test)
    #                                     #    print('model added')
    #                                     else:
    #                                         ...
    #                                     #    print('model not added')
    #                                     #model.Add(sum(block_bool_vars) < block_size).OnlyEnforceIf([var.Not() for var in block_bool_vars])
    #                                     #print()
    #                             else:
    #                                 for offset in range(block_size):
    #                                     model.AddHint(timetable[(l, m, s, d, t, r)])
#endregion                                        
#region
    # 5  = [3+2]          [[3+2][2+2+1][3+1+1][2+1+1+1][1+1+1+1+1]]
    # 10 = [2+2+2+2+2]

    # for module in modules:
    #     session_blocks = calculate_session_blocks(module["sws"])
    #     for block_size in session_blocks:
    #         if block_size == 2:
    #             #print(block_size)
    #             # slots = ((
    #             #     timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]])],
    #             #     timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot+1, room_ids_dic[room["room_id"]])]
    #             #     )
    #             #     for lecturer in lecturers
    #             #     for semester in semesters
    #             #     for day in days
    #             #     for time_slot in range(len(time_slots) - block_size + 1)
    #             #     for room in rooms
    #             # )
    #             #first_slot = slots[0]
    #             #second_slot = slots[1]

    #             model.AddBoolOr((first_slot, second_slot) for first_slot, second_slot in (
    #                 timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]])],
    #                 timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot+1, room_ids_dic[room["room_id"]])]

    #                 for lecturer in lecturers
    #                 for semester in semesters
    #                 for day in days
    #                 for time_slot in range(len(time_slots) - block_size + 1)
    #                 for room in rooms)
    #             ).OnlyEnforceIf([
    #                 not timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]])],
    #                 not timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot+1, room_ids_dic[room["room_id"]])]])
    #         elif block_size == 3:
    #             #print(block_size)
    #             model.Add(cp_model.LinearExpr.Sum([start_block, timetable[(l, m, s, d, t+1, r )], timetable[(l, m, s, d, t+2, r )]]) == 3)
    #             # model.AddBoolAnd(start_block, timetable[(l, m, s, d, t+1, r )], timetable[(l, m, s, d, t+2, r )])
    #             ...

#    for lecturer in lecturers:
#        for module in modules:
#            session_blocks = calculate_session_blocks(module["sws"])
#            for block_size in session_blocks:
#                for semester in semesters:
#                    for day in days:
#                        for time_slot in range(len(time_slots) - block_size + 1):  # Adjust based on block size
#                            for room in rooms:
#                                l = lecturer_ids_dic[lecturer["lecturer_id"]]
#                                m = module_ids_dic[module["module_id"]]
#                                s = semesters_dic[semester]
#                                d = days_dic[day]
#                                t = time_slot
#                                r = room_ids_dic[room["room_id"]]
#
#                                start_block = timetable[((l, m, s, d, t, r))]
#                                #test = [1, 1]
#                                #lst = [timetable[(l, m, s, d, t+offset, r )] for offset in range(block_size)]
#                                if block_size == 2:
#                                    #print(block_size)
#                                    model.Add(cp_model.LinearExpr.Sum(start_block, timetable[(l, m, s, d, t+1, r )]) == 2)
#                                elif block_size == 3:
#                                    #print(block_size)
#                                    model.Add(cp_model.LinearExpr.Sum(start_block, timetable[(l, m, s, d, t+1, r )], timetable[(l, m, s, d, t+2, r )]) == 3)
#                                    # model.AddBoolAnd(start_block, timetable[(l, m, s, d, t+1, r )], timetable[(l, m, s, d, t+2, r )])
#                                    ...


    # for offset in range(1, block_size):  # Start at 1 since t+offset where offset=0 is trivial
    #     for l, m, s, d, t, r in itertools.product(lecturers, modules, semesters, days, time_slots, rooms):
    #         if t + offset < len(time_slots):  # Ensure t+offset does not exceed the number of time slots available
    #             # Create an implication constraint
    #             model.AddBoolOr([timetable[(l, m, s, d, t, r)].Not(), timetable[(l, m, s, d, t+offset, r)]])
#endregion
#region
                                    # for offset in range(1, block_size):
                                    #     print(offset)
                                    #     model.AddBoolOr(timetable[((l, m, s, d, t, r))].Not(), timetable[(l, m, s, d, t+offset, r )])
                                    # elif block_size == 3:
                                    #     #print(block_size)
                                    #     model.Add(cp_model.LinearExpr.Sum(start_block, timetable[(l, m, s, d, t+1, r )], timetable[(l, m, s, d, t+2, r )]) == 3)
                                    #     # model.AddBoolAnd(start_block, timetable[(l, m, s, d, t+1, r )], timetable[(l, m, s, d, t+2, r )])
                                    #     ...
#endregion

    # At most one room per module per time_slot | two modules cannot be scheduled in the same room at the same time
    for day in days:
        for time_slot in time_slots:
            for room in rooms:
                model.AddAtMostOne(timetable[(lecturer_idx[lecturer["lecturer_id"]], module_idx[module["module_id"]], semester_idx[semester], day_idx[day], time_slot, room_idx[room["room_id"]])]
                for lecturer in lecturers
                for module in modules
                for semester in semesters
                )

    # At most one module per lecturer per time_slot | a lecturer cannot be scheduled for two modules at the same time
    for lecturer in lecturers:
        for day in days:
            for time_slot in time_slots:
                model.AddAtMostOne(timetable[(lecturer_idx[lecturer["lecturer_id"]], module_idx[module["module_id"]], semester_idx[semester], day_idx[day], time_slot, room_idx[room["room_id"]])]
                for module in modules
                for semester in semesters
                for room in rooms
                )

    # At most one module per semester per time_slot | two modules in the same semester cannot be scheduled at the same time
    for semester in semesters:
        for day in days:
            for time_slot in time_slots:
                model.AddAtMostOne(timetable[(lecturer_idx[lecturer["lecturer_id"]], module_idx[module["module_id"]], semester_idx[semester], day_idx[day], time_slot, room_idx[room["room_id"]])]
                for lecturer in lecturers
                for module in modules
                for room in rooms
                )

    # Sum( time_slots for module ) == module["sws"] | All sws have to be scheduled
    for module in modules:
        model.Add(cp_model.LinearExpr.Sum([timetable[(lecturer_idx[lecturer["lecturer_id"]], module_idx[module["module_id"]], semester_idx[semester], day_idx[day], time_slot, room_idx[room["room_id"]])]
            for lecturer in lecturers
            for semester in semesters
            for day in days
            for time_slot in time_slots
            for room in rooms
        ]) == int(module["sws"]))



    # Solve the model
    solution = {}
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    print(solver.SolutionInfo())
    print(
        f"Status:{solver.StatusName()}",
        f"Bools:{solver.NumBooleans()}",
        f"Branches:{solver.NumBranches()}",
        f"Conflicts:{solver.NumConflicts()}",
        sep="\n",
    )

    # Retrieve the solution
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:

        # Create available_rooms_dic to check how many rooms are free for each time_slot
        available_rooms_dic = {(day, time_slot): [room_id for room_id in room_ids]
                               for day in days
                               for time_slot in time_slots
                               }

        for semester in semesters:
            for day in days:
                for time_slot in time_slots:
                    for lecturer in lecturers:
                        for module in modules:
                            for room in rooms:

                                if solver.Value(timetable[(
                                        lecturer_idx[lecturer["lecturer_id"]], 
                                        module_idx[module["module_id"]],
                                        semester_idx[semester], 
                                        day_idx[day], 
                                        time_slot, 
                                        room_idx[room["room_id"]])]):

                                    available_rooms_dic[(day, time_slot)].remove(room["room_id"])
                                    solution.update(
                                        {
                                            semester: {
                                                day: {
                                                    time_slot: {
                                                        "lecturer": lecturer,
                                                        "module": module,
                                                        "room": room,
                                                    }
                                                }
                                            }
                                        }
                                    )


        print("RoomsAvailable: ", numof_available_rooms(available_rooms_dic, days, time_slots))
        return solution
    else:
        print(solver.ResponseStats())
        print("No feasible solution found.")
        return {}


def read_data_from(path) -> dict:
    return pd.read_csv(path, dtype=str).to_dict(orient="records")


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

if __name__ == "__main__":
    main()
