# by Niklas Hohn & Julien Sauter

import pprint
from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import IntVar

import utils.generate_lecturers_data as gld
import utils.generate_modules_data as gmd
from utils.table_printer import TablePrinter
from utils.util import * # get_lecturer_ids, get_module_ids, get_room_ids, modify_modules, read_data_from, generate_days, generate_vars, available_rooms

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
    # gld.generate_data()
    # gmd.create_data()
    result_object = run_model()
    if result_object:
        printer = TablePrinter(result_object)
        # pprint.pprint(result_object)
        printer.print_semester_tables()


def run_model():
    data: dict[str, list[dict] | list[str] | range] = {
        "lecturers": data_to_dict_from("db/lecturers.csv"),
        "modules": data_to_dict_from("db/modules.csv"),
        "rooms": data_to_dict_from("db/rooms.csv"),
    }
    data.update({
        "semesters": sorted(list(set([module.get("semester") for module in data.get("modules")]))),
        "days": generate_days(data.get("lecturers")),
    })
    data.update({
        "time_slots": range(len(data.get("lecturers")[0][data.get("days")[0]])),
    })
    data.update({
        "positions": ["s", "m_1", "e"] # ORDER IS IMPORTANT. We can add a key max_block_size in modules.csv to indicate the longest block_size for each module. Then we can calculate the possible positions for each module, but we would have to slightly adjust the calculate_session_blocks function to allow for different block_sizes for each module. Just add the parameter module["max_block_size"] to calculate_session_blocks which then defines which block_size calculation logic is used. Currently, the longest block_size is 3. This would be the default value.
    })
    
    modify_modules(data["modules"]) # Generate praktika

    lecturers= data["lecturers"] 
    modules = data["modules"] 
    rooms = data["rooms"] 
    semesters = data["semesters"] 
    days = data["days"] 
    positions = data["positions"]
    time_slots = data["time_slots"]
    # time_slot_times = ["8:45-9:30","9:30-10:15","10:30-11:15","11:15-12:00","12:50-13:35","13:35-14:20","14:30-15:15","15:15-16:00","16:10-16:55","16:55-17:40","17:50-18:35","18:35-19:20","19:30-20:15","20:15-21:00"]

    data_idx:dict[str, dict[str, int]] = {
        "lecturers":{lecturer_id: num for num, lecturer_id in enumerate(get_lecturer_ids(lecturers))},
        "modules": {module_id: num for num, module_id in enumerate(get_module_ids(modules))},
        "semesters": {semester: num for num, semester in enumerate(semesters)},
        "days": {day: num for num, day in enumerate(days)},
        "positions": {position: num for num, position in enumerate(positions)},
        "rooms": {room_id: num for num, room_id in enumerate(get_room_ids(rooms))},
    }

    lecturers_idx = data_idx["lecturers"]
    modules_idx = data_idx["modules"]
    semesters_idx  = data_idx["semesters"]
    days_idx  = data_idx["days"]
    positions_idx = data_idx["positions"]
    rooms_idx  = data_idx["rooms"]

    # Add course to module dictionary
    # TODO string slicing is kinda wanky :D
    for module in modules:
        module["course"] = module["module_id"][1:3]

    # Generate lecturer["skip_time_slots"] dictionary for each lecturer for faster access
    for lecturer in lecturers:
        lecturer["skip_time_slots"] = {(day, time_slot): bit == "0" for day in days for time_slot, bit in enumerate(time_slots)}

    # Calculate module["session_blocks"] list for each module
    for module in modules:
        module["block_sizes_dic"] = calculate_session_blocks(module["sws"])
        # module["session_blocks"] = {block_size: num for num, block in enumerate(module["session_blocks"])}


    # Create available_rooms_dic to check how many rooms are free for each time_slot
    available_rooms_dic = {(day, time_slot): [room_id for room_id in get_room_ids(rooms)]
        for day in days
        for time_slot in time_slots
        }

    # Create model
    model = cp_model.CpModel()
    timetable = generate_vars(model, data, data_idx)

    print("Variables: ", len(timetable))
    
    # Constraint consecutive time_slots
    for module in modules:
        for lecturer in lecturers:
            # lecturer implied, if statement allowed
            if lecturer["lecturer_id"] in module["lecturer_id"]:
                for semester in semesters:
                    # semester implied, if statement allowed
                    if semester == module["semester"]:
                        for block in module["block_sizes_dic"]:
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
                                        block_size = block[0]
                                        # enough time_slots available for block_size
                                        if time_slot < (len(lecturer[day]) - block_size + 1):
                                            for room in rooms:
                                            
                                                l = lecturers_idx[lecturer["lecturer_id"]]
                                                m = modules_idx[module["module_id"]]
                                                s = semesters_idx[semester]
                                                d = days_idx[day]
                                                t = time_slot
                                                r = rooms_idx[room["room_id"]]

                                                if block_size > 1:
                                                    block_bool_vars:list[IntVar] = [timetable[(l, m, s, d, t+offset, positions_idx[position], r)]
                                                        for offset in range(block_size)
                                                        for position in positions
                                                        ]
                                                    #print(block_bool_vars)
                                                    #print(len(block_bool_vars))
                                                    block_bool_vars_counter:int = block_size
                                                    for offset in range(1, block_size):
                                                        if lecturer[day][time_slot+offset] == "0":
                                                            for var in block_bool_vars[(len(positions)*offset)-1:(len(positions)*offset+1)-1]:
                                                                model.Add(var == 0) # If lecturer is not available during any time of block, block cannot be scheduled
                                                            block_bool_vars_counter -= 1

                                                    # skip as many time_slots as possible to save resources
                                                    #print(block_bool_vars_counter)
                                                        skip_time_slots = block_size
                                                        
                                                        for keep_steps in range(block_bool_vars_counter): # == block_size - (time_slot bits equal to 0)
                                                            skip_time_slots -= 1
                                                        if skip_time_slots > 0:
                                                            #print("didn't arrive at Implication", day, time_slot)
                                                            continue

                                                if block_size == 2:
                                                    model.AddImplication(timetable[(l, m, s, d, t, positions_idx["s"], r)],
                                                        timetable[(l, m, s, d, t+1, positions_idx["e"], r)])
                                                    model.AddImplication(timetable[(l, m, s, d, t+1, positions_idx["e"], r)],
                                                        timetable[(l, m, s, d, t, positions_idx["s"], r)])
                                                    model.AddImplication(timetable[(l, m, s, d, t, positions_idx["s"], r)].Not(),
                                                        timetable[(l, m, s, d, t+1, positions_idx["e"], r)].Not())
                                                    model.AddImplication(timetable[(l, m, s, d, t+1, positions_idx["e"], r)].Not(),
                                                        timetable[(l, m, s, d, t, positions_idx["s"], r)].Not())

                                    # model.AddImplication(timetable[(l, m, s, d, t, positions_idx[position], r)],
                                    #     position != "m_1")
                                                
                                                    
                                                    # model.AddImplication(timetable[(lecturers_idx[lecturer["lecturer_id"]], modules_idx[module["module_id"]], semesters_idx[semester], days_idx[day], time_slot, positions_idx[position], rooms_idx[room["room_id"]])],
                                                    #     cp_model.LinearExpr.Sum([timetable[(lecturers_idx[lecturer["lecturer_id"]], modules_idx[module["module_id"]], semesters_idx[semester], days_idx[day], time_slot+1, positions_idx[], rooms_idx[room["room_id"]])],
                                                    # ]) == 1)
                                                        
                                                    # model.AddImplication(timetable[(lecturers_idx[lecturer["lecturer_id"]], modules_idx[module["module_id"]], semesters_idx[semester], days_idx[day], time_slot + 1, positions_idx[position], rooms_idx[room["room_id"]])],
                                                    #     (positions_idx[position]*10 + time_slot) // 10 == 2)
                                                    # model.AddImplication(timetable[(lecturer_idx[lecturer["lecturer_id"]], module_idx[module["module_id"]], semester_idx[semester], day_idx[day], time_slot, position, room_idx[room["room_id"]])],
                                                    #     position == positions[1])


                                                        # timetable[l, m, s, d, t, r], p*10 + t // 10 == 0
                                                        # timetable[l, m, s, d, t+1, r], t // 10 == 0
                                                        
                                                        # model.AddImplication(t0s, t1e)
                                                        
                                                        # model.AddImplication(t0m, t1e)

                                                        # model.AddImplication(t0s, t2e)

    # if two block_sizes are the same, we need an additional constraint to enforce that block_1 != block_2, probably taken care of by the constraint that lecturers cannot be scheduled for two time_slots at the same time

    # Define the constraints
    for lecturer in lecturers:
        for module in modules:
            for semester in semesters:
                for day in days:
                    for time_slot, bit in enumerate(lecturer[day]):
                        for position in positions:
                            for room in rooms:

                                # Implied for every lecturer for every time_slot that time_slot bit == "1" | lecturers only give lectures when they are free (bit == "1")
                                model.AddImplication(timetable[(lecturers_idx[lecturer["lecturer_id"]], modules_idx[module["module_id"]], semesters_idx[semester], days_idx[day], time_slot, positions_idx[position], rooms_idx[room["room_id"]])],
                                    bit == "1"
                                    )

                                # Implied for every module that lecturer["lecturer_id"] in module["lecturer_id"] | modules can only be taught by their corresponding lecturer
                                model.AddImplication(timetable[(lecturers_idx[lecturer["lecturer_id"]], modules_idx[module["module_id"]], semesters_idx[semester], days_idx[day], time_slot, positions_idx[position], rooms_idx[room["room_id"]])],
                                    lecturer["lecturer_id"] in module["lecturer_id"]
                                    )

                                # Implied for every module that semester == module["semester"] | modules linked to respective semesters
                                model.AddImplication(timetable[(lecturers_idx[lecturer["lecturer_id"]], modules_idx[module["module_id"]], semesters_idx[semester], days_idx[day], time_slot, positions_idx[position], rooms_idx[room["room_id"]])],
                                    semester == module["semester"]
                                    )

                                # Implied for every room that room["capacity"] >= module["participants"] | room has enough space for the module
                                model.AddImplication(timetable[(lecturers_idx[lecturer["lecturer_id"]], modules_idx[module["module_id"]], semesters_idx[semester], days_idx[day], time_slot, positions_idx[position], rooms_idx[room["room_id"]])],
                                    room["capacity"] >= module["participants"]
                                    )

                                # Implied for every room that module["module_id"][0] == room["room_type"] | room type fits to module type
                                model.AddImplication(timetable[(lecturers_idx[lecturer["lecturer_id"]], modules_idx[module["module_id"]], semesters_idx[semester], days_idx[day], time_slot, positions_idx[position], rooms_idx[room["room_id"]])],
                                    module["module_id"][0] == room["room_type"]
                                    )

    # At most one room per module per time_slot | two modules cannot be scheduled in the same room at the same time
    for day in days:
        for time_slot in time_slots:
            for room in rooms:
                model.AddAtMostOne(timetable[(lecturers_idx[lecturer["lecturer_id"]], modules_idx[module["module_id"]], semesters_idx[semester], days_idx[day], time_slot, positions_idx[position], rooms_idx[room["room_id"]])]
                for lecturer in lecturers
                for module in modules
                for semester in semesters
                for position in positions
                )

    # At most one module per lecturer per time_slot | a lecturer cannot be scheduled for two modules at the same time
    for lecturer in lecturers:
        for day in days:
            for time_slot in time_slots:
                model.AddAtMostOne(timetable[(lecturers_idx[lecturer["lecturer_id"]], modules_idx[module["module_id"]], semesters_idx[semester], days_idx[day], time_slot, positions_idx[position], rooms_idx[room["room_id"]])]
                for module in modules
                for semester in semesters
                for position in positions
                for room in rooms
                )

    # At most one module per semester per time_slot | two modules in the same semester cannot be scheduled at the same time
    for semester in semesters:
        for day in days:
            for time_slot in time_slots:
                model.AddAtMostOne(timetable[(lecturers_idx[lecturer["lecturer_id"]], modules_idx[module["module_id"]], semesters_idx[semester], days_idx[day], time_slot, positions_idx[position], rooms_idx[room["room_id"]])]
                for lecturer in lecturers
                for module in modules
                for room in rooms
                for position in positions
                )

    # Sum( time_slots for module ) == module["sws"] | All sws have to be scheduled
    for module in modules:
        model.Add(cp_model.LinearExpr.Sum([timetable[(lecturers_idx[lecturer["lecturer_id"]], modules_idx[module["module_id"]], semesters_idx[semester], days_idx[day], time_slot, positions_idx[position], rooms_idx[room["room_id"]])]
            for lecturer in lecturers
            for semester in semesters
            for day in days
            for time_slot in time_slots
            for position in positions
            for room in rooms
        ]) == int(module["sws"]))

    solver, status = solve_model(model)
    return retrieve_solution(data, data_idx, model, timetable, available_rooms_dic, solver, status)



if __name__ == "__main__":
    main()
