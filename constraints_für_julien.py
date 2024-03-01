    # Read in data file
import pprint
import pandas as pd
from ortools.sat.python import cp_model

from ortools.sat.python.cp_model import IntVar

import utils.generate_lecturers_data as gld
import utils.generate_modules_data as gmd
from utils.table_printer import TablePrinter
from utils.util import *

lecturers= read_data_from("db/lecturers.csv")
modules = read_data_from("db/modules.csv")
rooms = read_data_from("db/rooms.csv")

# Generate praktika
# TODO What is this code doing? Can it be moved into a function? Does it just generate data or is it modifying data? @Julio
# def generate_praktika(modules):
for module in modules:
    if module["module_id"][0] == "p":
        module_p = module
        for module in modules:
            if module["module_id"][0] == "l":
                module_l = module
                if module_p["module_id"][1:] == module_l["module_id"][1:]:
                    numof_prak = (int(module_l["participants"]) // int(module_p["max_participants"])) + 1 # 20 is an arbitrary max number of participants for each praktika
                    remaining_participants = int(module_l["participants"])
                    for module_p_num in range(numof_prak):
                        module_p_copy = module_p.copy()
                        module_p_copy["module_id"] = module_p_copy["module_id"] + '_' + str(module_p_num+1)

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
days = generate_days(lecturers)

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

data_idx:dict[str, dict[str, int]] = {
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

# Add course to module dictionary
# TODO string slicing is kinda wanky :D regex?
for module in modules:
    module["course"] = module["module_id"][1:3]

# Create available_rooms_dic to check how many rooms are free for each time_slot
available_rooms_dic = {(day, time_slot): [room_id for room_id in room_ids]
    for day in days
    for time_slot in time_slots
    }

# Create model
model = cp_model.CpModel()
timetable = generate_vars(model, data, data_idx)


# | All modules should be in blocks of consecutive time_slots if possible (if leftover_sws % 2 == 0: block_size = 2, elif leftover_sws >= 3: block_size = 3, elif leftover_sws == 1: block_size = 1 else: )
for lecturer in lecturers:
    #print(lecturer["lecturer_id"])
    for module in modules:
        session_blocks = calculate_session_blocks(module["sws"])
        for block_size in session_blocks:
            for semester in semesters:
                if semester == module["semester"]:
                    for day in days:
                        for time_slot, bit in enumerate(time_slots):  # Adjust based on block size
                            if time_slot < len(lecturer[day]) - block_size + 1:
                                for room in rooms:
                                    
                                    l = lecturer_idx[lecturer["lecturer_id"]]
                                    m = module_idx[module["module_id"]]
                                    s = semester_idx[semester]
                                    d = day_idx[day]
                                    t = time_slot
                                    r = room_idx[room["room_id"]]
                                    
                                    block_bool_vars:list[IntVar] = [timetable[(l, m, s, d, t+offset, r)] for offset in range(block_size)]

                                    for offset in range(1, block_size):
                                        if lecturer[day][time_slot+offset] == "0":
                                            for var in block_bool_vars:
                                                model.Add(var == 0)  # If lecturer is not available, block cannot be scheduled
                                                                            
                                    model.Add(sum(block_bool_vars) == block_size).OnlyEnforceIf(block_bool_vars)

                            else:
                                for offset in range(block_size):
                                    model.AddHint(timetable[(l, m, s, d, t, r)], True)


# | All modules should be in blocks of consecutive time_slots if possible (if leftover_sws % 2 == 0: block_size = 2, elif leftover_sws >= 3: block_size = 3, elif leftover_sws == 1: block_size = 1 else: )
for lecturer in lecturers:
    #print(lecturer["lecturer_id"])
    for module in modules:
        session_blocks = calculate_session_blocks(module["sws"])
        for block_size in session_blocks:
            for semester in semesters:
                if semester == module["semester"]:
                    for day in days:
                        for time_slot, bit in enumerate(lecturer[day][:len(time_slots) - block_size + 1]):  # Adjust based on block size
                            if time_slot < len(lecturer[day]) - block_size + 1:
                                for room in rooms:
                                    
                                    l = lecturer_idx[lecturer["lecturer_id"]]
                                    m = module_idx[module["module_id"]]
                                    s = semesters_dic[semester]
                                    d = days_dic[day]
                                    t = time_slot
                                    r = room_idx[room["room_id"]]
                                    
                                    block_bool_vars:list[IntVar] = [timetable[(l, m, s, d, t+offset, r)] for offset in range(block_size)]

                                    for offset in range(1, block_size):
                                        if lecturer[day][time_slot+offset] == "0":
                                    #        print(block_bool_vars)
                                            for var in block_bool_vars:
                                    #            print('not free')
                                                model.Add(var == 0)  # If lecturer is not available, block cannot be scheduled
                                    #    print('free')
                                    
                                    #print(block_size)
                                    model_test = model.Add(sum(block_bool_vars) == block_size).OnlyEnforceIf(block_bool_vars)
                                    if model_test:
                                        ...
                                    #    print(model_test)
                                    #    print('model added')
                                    else:
                                        ...
                                    #    print('model not added')
                                    #model.Add(sum(block_bool_vars) < block_size).OnlyEnforceIf([var.Not() for var in block_bool_vars])
                                    #print()
                            else:
                                for offset in range(block_size):
                                    model.AddHint(timetable[(l, m, s, d, t, r)])
                                        

5  = [3+2]          [[3+2][2+2+1][3+1+1][2+1+1+1][1+1+1+1+1]]
10 = [2+2+2+2+2]

for module in modules:
    session_blocks = calculate_session_blocks(module["sws"])
    for block_size in session_blocks:
        if block_size == 2:
            #print(block_size)
            # slots = ((
            #     timetable[(lecturer_idx[lecturer["lecturer_id"]], module_idx[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_idx[room["room_id"]])],
            #     timetable[(lecturer_idx[lecturer["lecturer_id"]], module_idx[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot+1, room_idx[room["room_id"]])]
            #     )
            #     for lecturer in lecturers
            #     for semester in semesters
            #     for day in days
            #     for time_slot in range(len(time_slots) - block_size + 1)
            #     for room in rooms
            # )
            #first_slot = slots[0]
            #second_slot = slots[1]

            model.AddBoolOr((first_slot, second_slot) for first_slot, second_slot in (
                timetable[(lecturer_idx[lecturer["lecturer_id"]], module_idx[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_idx[room["room_id"]])],
                timetable[(lecturer_idx[lecturer["lecturer_id"]], module_idx[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot+1, room_idx[room["room_id"]])]

                for lecturer in lecturers
                for semester in semesters
                for day in days
                for time_slot in range(len(time_slots) - block_size + 1)
                for room in rooms)
            ).OnlyEnforceIf([
                not timetable[(lecturer_idx[lecturer["lecturer_id"]], module_idx[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_idx[room["room_id"]])],
                not timetable[(lecturer_idx[lecturer["lecturer_id"]], module_idx[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot+1, room_idx[room["room_id"]])]])
        elif block_size == 3:
            #print(block_size)
            model.Add(cp_model.LinearExpr.Sum([start_block, timetable[(l, m, s, d, t+1, r )], timetable[(l, m, s, d, t+2, r )]]) == 3)
            # model.AddBoolAnd(start_block, timetable[(l, m, s, d, t+1, r )], timetable[(l, m, s, d, t+2, r )])
            ...

for lecturer in lecturers:
    for module in modules:
        session_blocks = calculate_session_blocks(module["sws"])
        for block_size in session_blocks:
            for semester in semesters:
                for day in days:
                    for time_slot in range(len(time_slots) - block_size + 1):  # Adjust based on block size
                        for room in rooms:
                            l = lecturer_idx[lecturer["lecturer_id"]]
                            m = module_idx[module["module_id"]]
                            s = semesters_dic[semester]
                            d = days_dic[day]
                            t = time_slot
                            r = room_idx[room["room_id"]]

                            start_block = timetable[((l, m, s, d, t, p, r))]
                            #test = [1, 1]
                            #lst = [timetable[(l, m, s, d, t+offset, r )] for offset in range(block_size)]
                            if block_size == 2:
                                #print(block_size)
                                model.Add(cp_model.LinearExpr.Sum(start_block, timetable[(l, m, s, d, t+1, r )]) == 2)
                            elif block_size == 3:
                                #print(block_size)
                                model.Add(cp_model.LinearExpr.Sum(start_block, timetable[(l, m, s, d, t+1, r )], timetable[(l, m, s, d, t+2, r )]) == 3)
                                # model.AddBoolAnd(start_block, timetable[(l, m, s, d, t+1, r )], timetable[(l, m, s, d, t+2, r )])
                                ...


for offset in range(1, block_size):  # Start at 1 since t+offset where offset=0 is trivial
    for l, m, s, d, t, r in itertools.product(lecturers, modules, semesters, days, time_slots, rooms):
        if t + offset < len(time_slots):  # Ensure t+offset does not exceed the number of time slots available
            # Create an implication constraint
            model.AddBoolOr([timetable[(l, m, s, d, t, r)].Not(), timetable[(l, m, s, d, t+offset, r)]])


                                for offset in range(1, block_size):
                                    print(offset)
                                    model.AddBoolOr(timetable[((l, m, s, d, t, r))].Not(), timetable[(l, m, s, d, t+offset, r )])
                                elif block_size == 3:
                                    #print(block_size)
                                    model.Add(cp_model.LinearExpr.Sum(start_block, timetable[(l, m, s, d, t+1, r )], timetable[(l, m, s, d, t+2, r )]) == 3)
                                    # model.AddBoolAnd(start_block, timetable[(l, m, s, d, t+1, r )], timetable[(l, m, s, d, t+2, r )])
                                    ...

# by Niklas Hohn & Julien Sauter

import pprint
import itertools

import pandas as pd

from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import IntVar

import utils.generate_lecturers_data as gld
import utils.generate_modules_data as gmd
from utils.table_printer import TablePrinter

# INFO: all for loops above contraint are consumed, and all for loops in constraint are chosen/reused

# TODO IMPORTANT: time_slots are currently treated as 60 minute windows, even though they are 45 min. This drastically changes how we have to check if sws per module are being taught. >= won't be enough because we don't want to overbook modules.

# TODO tidy up code, create classes and methods, OOP
# TODO for performance try to merge contraints into one for loop struct (save previous for loop values)
# TODO if necessary, add gender, etc. to lecturers for german spelling and other information
# TODO implement print function (or equivalent/analogous output) in different languages
# TODO MAYBE: Let modules define more accurately what they need in a room, instead of just lecture vs practice

# HEURISTIC for each module, Optimise: same room (same room -OR- constraint modules are always same room)
# HEURISTIC for each lecturer, Optimise: less days -OR- shorter periods -OR- more breaks
# HEURISTIC for each semester for each day, Optimise: same room for as long as possible
# HEURISTIC for each semester for each day, Optimise: lower walking distance (add Mensa as room for break time) (same building -OR- room_coordinates with manhattan/euclidean distance -OR- constraint courses (WiPsy) have specific buildings)
# HEURISTIC for each module for each room, Optimise: just over half full rooms (normal distribution, slightly right-skewed)

def main():
    gld.generate_data()
    gmd.create_data()
    result_object = run_model()
    printer = TablePrinter(result_object)
    printer.print_tables()


def run_model():
    
    # Read in data file
    lecturers_df = pd.read_csv("db/lecturers.csv", dtype=str)
    modules_df = pd.read_csv("db/modules.csv", dtype=str)
    rooms_df = pd.read_csv("db/rooms.csv", dtype=str)

    # Pandas data frame to list of dictionaries
    lecturers_data = lecturers_df.to_dict(orient="records")
    modules_data = modules_df.to_dict(orient="records")
    rooms_data = rooms_df.to_dict(orient="records")

    # Better names
    lecturers = lecturers_data
    modules = modules_data
    rooms = rooms_data
    
    # Generate praktika
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
    
    # Create other data sources
    semesters = list(set([module["semester"] for module in modules]))
    semesters.sort()
    days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    time_slots = range(len(lecturers[0][days[0]]))

    time_slot_times = ["8:45-9:30","9:30-10:15","10:30-11:15","11:15-12:00","12:50-13:35","13:35-14:20","14:30-15:15","15:15-16:00","16:10-16:55","16:55-17:40","17:50-18:35","18:35-19:20","19:30-20:15","20:15-21:00"]

    # Create id list
    lecturer_ids = [lecturer["lecturer_id"] for lecturer in lecturers]
    module_ids = [module["module_id"] for module in modules]
    room_ids = [room["room_id"] for room in rooms]
    
    # Link ids to int values
    lecturer_ids_dic = {lecturer_id: num for num, lecturer_id in enumerate(lecturer_ids)}
    module_ids_dic = {module_id: num for num, module_id in enumerate(module_ids)}
    room_ids_dic = {room_id: num for num, room_id in enumerate(room_ids)}
    semesters_dic = {semester: num for num, semester in enumerate(semesters)}
    days_dic = {day: num for num, day in enumerate(days)}
    days_uniform_dic = {day: day[:3] for day in days}
    time_slot_times_dic = {time_slot_time:time_slot for time_slot, time_slot_time in zip(time_slots, time_slot_times) if time_slot < len(time_slots)}

    # Add course to module dictionary
    for module in modules:
        module["course"] = module["module_id"][1:3]
    
    # Generate lecturer["skip_time_slots"] dictionary for each lecturer for faster access
    for lecturer in lecturers:
        lecturer["skip_time_slots"] = {(day, time_slot): bit == "0" for day in days for time_slot, bit in enumerate(time_slots)}

    # Calculate module["session_blocks"] list for each module
    for module in modules:
        module["session_blocks"] = calculate_session_blocks(module["sws"])
        module["block_sizes_dic"] = {}

    # Create model
    model = cp_model.CpModel()
    timetable = {}
    for module in modules:
        for lecturer in lecturers:
            for semester in semesters:
                for day in days:
                    for time_slot in time_slots:
                        for room in rooms:
                            for block_size in block_sizes_lst:
                                timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, block_size, room_ids_dic[room["room_id"]]
                                    )] = model.NewBoolVar(f'{lecturer["lecturer_id"]}_{module["module_id"]}_{semester}_{day}_{time_slot}_{block_size}_{room["room_id"]}')

    # Define the constraints (Implications)
    for module in modules:
        for lecturer in lecturers:
            for semester in semesters:
                for day in days:
                    for time_slot, bit in enumerate(lecturer[day]):
                        for room in rooms:
                            for block_size in block_sizes_lst:
                            
                                # Implied for every lecturer for every time_slot that time_slot bit == "1" | lecturers only give lectures when they are free (bit == "1")
                                model.AddImplication(timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, block_size, room_ids_dic[room["room_id"]])],
                                    bit == "1"
                                    )

                                # Implied for every module that lecturer["lecturer_id"] in module["lecturer_id"] | modules can only be taught by their corresponding lecturer
                                model.AddImplication(timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, block_size, room_ids_dic[room["room_id"]])],
                                    lecturer["lecturer_id"] in module["lecturer_id"]
                                    )
                            
                                # Implied for every module that semester == module["semester"] | modules linked to respective semesters
                                model.AddImplication(timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, block_size, room_ids_dic[room["room_id"]])],
                                    semester == module["semester"]
                                    )

                                # Implied for every room that room["capacity"] >= module["participants"] | room has enough space for the module
                                model.AddImplication(timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, block_size, room_ids_dic[room["room_id"]])],
                                    room["capacity"] >= module["participants"]
                                    )

                                # Implied for every room that module["module_id"][0] == room["room_type"] | room type fits to module type
                                model.AddImplication(timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, block_size, room_ids_dic[room["room_id"]])],
                                    module["module_id"][0] == room["room_type"]
                                    )

    time_slot_combinations = list(itertools.product(days, time_slots[:-1]))
    #print(time_slot_combinations)

    # for module in modules:
    #     if module["session_blocks"] > 1:
    #         for lecturer in lecturers:
    #             for semester in semesters:
    #                 model.Add(cp_model.LinearExpr.Sum([timetable[key_1], timetable[key_2]]) == 2).OnlyEnforceIf(temp_var)
    
    for module in modules:
        for lecturer in lecturers:
            for semester in semesters:
                for block_size in block_sizes_dic:
                    combination_vars = []
                    for day in days:
                        for time_slot in time_slots[:len(time_slots) - block_size + 1]:
                            for room in rooms:                    
                                
                                # Create a temporary variable representing this specific combination being true
                                #temp_var = model.NewBoolVar(f'{lecturer["lecturer_id"]}_{module["module_id"]}_{semester}_{time_slot}_{time_slot+1}_{room["room_id"]}')
                                # Link the temp variable to the timetable entries
                                key_1 = (lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, block_size, room_ids_dic[room["room_id"]])
                                key_2 = (lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot+1, block_size, room_ids_dic[room["room_id"]])
                                key_3 = (lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot+2, block_size, room_ids_dic[room["room_id"]])
                                if block_size == 1:
                                    model.Add(cp_model.LinearExpr.Sum([timetable[key_1]]) == 1).OnlyEnforceIf(block_size == 1)
                                elif block_size == 2:
                                    model.Add(cp_model.LinearExpr.Sum([timetable[key_1], timetable[key_2]]) == 2).OnlyEnforceIf(block_size == 2)
                                elif block_size == 3:
                                    model.Add(cp_model.LinearExpr.Sum([timetable[key_1], timetable[key_2], timetable[key_3]]) == 3).OnlyEnforceIf(block_size == 3)
                                #model.AddBoolAnd([timetable[key_1].Not(), timetable[key_2].Not()]).OnlyEnforceIf(temp_var.Not())
                                combination_vars.append((day, time_slot))
                                ...
                            # Ensure at most one of the combination variables can be true
                    model.AddInverse([timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, block_size, room_ids_dic[room["room_id"]])]
                        for day, time_slot in combination_vars])

#region
    # for module in modules:
    #     for lecturer in lecturers:
    #         for semester in semesters:
    #             for room in rooms:
    #                 session_blocks = calculate_session_blocks(module["sws"])
    #                 for block_size in session_blocks:
    #                     for day in days:
    #                         for time_slot in time_slots[:-1]:
    #                             combination_vars = []
    #                             # Create a temporary variable representing this specific combination being true
    #                             temp_var = model.NewBoolVar(f'{lecturer["lecturer_id"]}_{module["module_id"]}_{semester}_{time_slot}_{time_slot+1}_{room["room_id"]}')
    #                             # Link the temp variable to the timetable entries
    #                             key_1 = (lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]])
    #                             key_2 = (lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot+1, room_ids_dic[room["room_id"]])
    #                             model.Add(cp_model.LinearExpr.Sum([timetable[key_1], timetable[key_2]]) == 2).OnlyEnforceIf(temp_var)
    #                             #model.AddBoolAnd([timetable[key_1].Not(), timetable[key_2].Not()]).OnlyEnforceIf(temp_var.Not())
    #                             combination_vars.append(temp_var)
    #                             ...
    #                         # Ensure at most one of the combination variables can be true
    #                     model.AddExactlyOne(combination_vars)

    #for module in modules:

    # | All modules should be in blocks of consecutive time_slots if possible (if leftover_sws % 2 == 0: block_size = 2, elif leftover_sws >= 3: block_size = 3, elif leftover_sws == 1: block_size = 1 else: )
    for module in modules:
        for lecturer in lecturers:
            # lecturer implied, if statement allowed
            if lecturer["lecturer_id"] in module["lecturer_id"]:
                for semester in semesters:
                    # semester implied, if statement allowed
                    if semester == module["semester"]:
                        session_blocks = calculate_session_blocks(module["sws"])
                        for block_size in session_blocks:
                            for day in days:
                                skip_time_slots = 0
                                for time_slot, bit in enumerate(lecturer[day]):

                                    # check this first so that skip_time_slots doesn't get messed up, might have to check logic
                                    if skip_time_slots > 0:
                                        skip_time_slots -= 1
                                        #print("skipping", day, time_slot)
                                        lecturer["skip_time_slots"][(day, time_slot)] = True
                                        continue
                                    if lecturer["skip_time_slots"][(day, time_slot)]:
                                        continue
                                    
                                    # bit implied, if statement allowed
                                    if bit == "1":
                                        # enough time_slots available for block_size
                                        if time_slot < (len(lecturer[day]) - block_size + 1):
                                            
                                            
                                            l = lecturer_ids_dic[lecturer["lecturer_id"]]
                                            m = module_ids_dic[module["module_id"]]
                                            s = semesters_dic[semester]
                                            d = days_dic[day]
                                            t = time_slot
                                            
                                            block_bool_vars:list[IntVar] = [timetable[(l, m, s, d, t+offset, block_size, room_ids_dic[room["room_id"]])] #TODO block_size
                                                for offset in range(block_size)
                                                for room in rooms
                                                ]
                                            #print(block_bool_vars)
                                            #print(len(block_bool_vars))
                                            block_bool_vars_counter:int = block_size
                                            for offset in range(1, block_size):
                                                if lecturer[day][time_slot+offset] == "0":
                                                    for var in block_bool_vars[(len(rooms)*offset)-1:(len(rooms)*offset+1)-1]:
                                                        model.Add(var == 0) # If lecturer is not available during any time of block, block cannot be scheduled
                                                    block_bool_vars_counter -= 1
                                            
                                            # skip as many time_slots as possible to save resources
                                            #print(block_bool_vars_counter)
                                            if block_size > 1:
                                                skip_time_slots = block_size
                                                
                                                for keep_steps in range(block_bool_vars_counter): # == block_size - (time_slot bits equal to 0)
                                                    skip_time_slots -= 1
                                                if skip_time_slots > 0:
                                                    #print("didn't arrive at Implication", day, time_slot)
                                                    continue
                                            
                                            #print("arrived at Implication", day, time_slot)
                                            if block_size <= 2:
                                                model.AddAtMostOne(timetable[((lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]]))] #TODO block_size
                                                    for day in days
                                                    for time_slot in time_slots[:len(time_slots)-1]
                                                    for room in rooms
                                                    )
                                                model.AddAtMostOne(timetable[((lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot+1, room_ids_dic[room["room_id"]]))] #TODO block_size
                                                    for day in days
                                                    for time_slot in time_slots[:len(time_slots)-1]
                                                    for room in rooms
                                                )
                                                ...
                                                    
                                            if block_size == 3:
                                                model.Add(timetable[((lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]]))] == 1) #TODO block_size
                                                model.Add(timetable[((lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot+1, room_ids_dic[room["room_id"]]))] == 1) #TODO block_size
                                                model.Add(timetable[((lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot+2, room_ids_dic[room["room_id"]]))] == 1) #TODO block_size
                                                
                                                # AddImplication(time_slot, logical_and(sum(time_slot+1)==1, sum(time_slot+2)==1)) # implies block_size == 3
#endregion
#region
                                                    # model.AddImplication(timetable[((lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]]))], #TODO block_size
                                                    #     sum([timetable[((lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot+1, room_ids_dic[room["room_id"]]))], #TODO block_size
                                                    #         ]) == (block_size - 2)
                                                    # )
                                                    # model.AddImplication(timetable[((lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]]))], #TODO block_size
                                                    #     sum([timetable[((lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot+1, room_ids_dic[room["room_id"]]))], #TODO block_size
                                                    #         timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot+2, room_ids_dic[room["room_id"]])] #TODO block_size
                                                    #         ]) == (block_size - 1)
                                                    # )
                                                
                                        #     model.Add(sum(block_bool_vars) == block_size).OnlyEnforceIf(block_bool_vars)

                                        # else:
                                        #     for offset in range(block_size):
                                        #         model.AddHint(timetable[(l, m, s, d, t, r)])

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
    #             #     timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, block_size, room_ids_dic[room["room_id"]])],
    #             #     timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot+1, room_ids_dic[room["room_id"]])] #TODO block_size
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
    #                 timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, block_size, room_ids_dic[room["room_id"]])],
    #                 timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot+1, room_ids_dic[room["room_id"]])] #TODO block_size
                
    #                 for lecturer in lecturers
    #                 for semester in semesters
    #                 for day in days
    #                 for time_slot in range(len(time_slots) - block_size + 1)
    #                 for room in rooms)
    #             ).OnlyEnforceIf([
    #                 not timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, block_size, room_ids_dic[room["room_id"]])],
    #                 not timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot+1, room_ids_dic[room["room_id"]])]]) #TODO block_size
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
                model.AddAtMostOne(timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, block_size, room_ids_dic[room["room_id"]])]
                for module in modules
                for lecturer in lecturers
                for semester in semesters
                )

    # At most one module per lecturer per time_slot | a lecturer cannot be scheduled for two modules at the same time
    for lecturer in lecturers:
        for day in days:
            for time_slot in time_slots:
                model.AddAtMostOne(timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, block_size, room_ids_dic[room["room_id"]])]
                for module in modules
                for semester in semesters
                for room in rooms
                )

    # At most one module per semester per time_slot | two modules in the same semester cannot be scheduled at the same time
    for semester in semesters:
        for day in days:
            for time_slot in time_slots:
                model.AddAtMostOne(timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, block_size, room_ids_dic[room["room_id"]])]
                for module in modules
                for lecturer in lecturers
                for room in rooms
                )
    
    # Sum( time_slots for module ) == module["sws"] | All sws have to be scheduled
    for module in modules:
        model.Add(cp_model.LinearExpr.Sum([timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, block_size, room_ids_dic[room["room_id"]])]
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
    print( f'Status:{solver.StatusName()}',f'Bools:{solver.NumBooleans()}', f'Branches:{solver.NumBranches()}', f'Conflicts:{solver.NumConflicts()}', sep='\n', end='\n\n')


    # Retrieve the solution
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        
        # Create available_rooms_dic to check how many rooms are free for each time_slot
        available_rooms_dic = {(day, time_slot): [room_id for room_id in room_ids]
            for day in days
            for time_slot in time_slots
            }
        
        for semester in semesters:
            print()
            solution.update({semester:{}})
            print(f'Semester {semester}:')
            for day in days:
                print(f'{day}:')
                solution[semester].update({day:{}})
                for time_slot in time_slots:
                    solution[semester][day].update({time_slot:{}}) # @niklas Why not another dictionary with keys as id's from the variables from the for loops below and values as the variable itself (timeslot:{lecturer_id: lecturer, module_id: module, room_id: room})?
                    for module in modules:
                        for lecturer in lecturers:
                            for room in rooms:
                                
                                if solver.Value(timetable[(
                                        lecturer_ids_dic[lecturer["lecturer_id"]], 
                                        module_ids_dic[module["module_id"]],
                                        semesters_dic[semester], 
                                        days_dic[day], 
                                        time_slot, 
                                        room_ids_dic[room["room_id"]])]):
                                    
                                    module_id_nicer = module["module_id"][1:] + module["module_id"][0]
                                    
                                    available_rooms_dic[(day, time_slot)].remove(room["room_id"])
                                    solution[semester][day][time_slot].update({
                                        "lecturer": lecturer,
                                        "module": module,
                                        "room": room
                                        })
                                    
                                    
                                    print(
                                        f'{time_slot} {module_id_nicer:7} {room["room_id"]} ({module["module_id"][0]}={room["room_type"]}) ({module["participants"]}/{room["capacity"]}) {lecturer["lecturer_name"]}'
                                        #f'At time slot {time_slot} {module_id_nicer} is being taught in room {room["room_id"]} ({module["module_id"][0]}={room["room_type"]}) ({module["participants"]}/{room["capacity"]}) by Lecturer {lecturer["lecturer_name"]}'
                                        #f'An Zeitpunkt {time_slot} wird {module_id_nicer} unterrichtet in Raum {room["room_id"]} ({module["participants"]}/{room["capacity"]}) von Professor {lecturer["lecturer_name"]}'
                                    )
                    
        print(numof_available_rooms(available_rooms_dic, days, time_slots))
        
        # print([(module["module_id"], module["participants"]) for module in modules])
        for semester in semesters:
            for day in days:
                solution[semester][days_uniform_dic[day]] = solution[semester][day]
        for semester in semesters:
            for day in days:
                del solution[semester][day]

        #pprint.pprint(solution)
        #print(type(solution))
        if type(solution) == None:
            return
        return solution
    else:
        #print(solver.ResponseStats())
        print("No feasible solution found.")
        return solution
        gld.write_generated_data()
        gmd.create_data()
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

def calculate_session_blocks(leftover_sws:str) -> dict[int, int]:
    #return [1]
    session_blocks = {}
    num = 0
    key_1 = 0
    key_2 = 0
    key_3 = 0
    leftover_sws = int(leftover_sws)
    while leftover_sws > 0:
        if leftover_sws % 2 == 0:
            session_blocks[f"{2}_{key_2}"] = num
            num += 1
            key_2 += 1
            leftover_sws -= 2
        elif leftover_sws >= 3:
            session_blocks[f"{3}_{key_3}"] = num
            num += 1
            key_3 += 1
            leftover_sws -= 3
        elif leftover_sws == 1:
            session_blocks[f"{1}_{key_1}"] = num
            num += 1
            key_1 += 1
            leftover_sws -= 1
    
    return session_blocks




if __name__ == "__main__":
    main()
    #print(test_calculate_session_blocks())
