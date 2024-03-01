# by Niklas Hohn & Julien Sauter

import pprint
from ortools.sat.python import cp_model


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
        pprint.pprint(result_object)
        printer.print_semester_tables()


def run_model():
    data = {
        "lecturers": read_data_from("db/lecturers.csv"),
        "modules": read_data_from("db/modules.csv"),
        "rooms": read_data_from("db/rooms.csv"),
    }
    data.update({
        "semesters": sorted(list(set([module.get("semester") for module in data.get("modules")]))),
        "days": generate_days(data.get("lecturers")),
    })
    data.update({
        "time_slots": range(len(data.get("lecturers")[0][data.get("days")[0]])),
    })
    data.update({
        "positions": ["s", "m_1", "e"] # We can add a key max_block_size in modules.csv to indicate the longest block_size for each module. Then we can calculate the possible positions for each module, but we would have to slightly adjust the calculate_session_blocks function to allow for different block_sizes for each module. Just add the parameter module["max_block_size"] to calculate_session_blocks which then defines which block_size calculation logic is used. Currently, the longest block_size is 3. This would be the default value.
    })
    
    modify_modules(data["modules"]) # Generate praktika

    lecturers= data["lecturers"] 
    modules = data["modules"] 
    rooms = data["rooms"] 
    semesters = data["semesters"] 
    days = data["days"] 
    time_slots = data["time_slots"] 
    # time_slot_times = ["8:45-9:30","9:30-10:15","10:30-11:15","11:15-12:00","12:50-13:35","13:35-14:20","14:30-15:15","15:15-16:00","16:10-16:55","16:55-17:40","17:50-18:35","18:35-19:20","19:30-20:15","20:15-21:00"]

    data_idx:dict[str, dict[str, int]] = {
        "lecturers":{lecturer_id: num for num, lecturer_id in enumerate(get_lecturer_ids(lecturers))},
        "modules": {module_id: num for num, module_id in enumerate(get_module_ids(modules))},
        "semesters": {semester: num for num, semester in enumerate(semesters)},
        "days": {day: num for num, day in enumerate(days)},
        "rooms": {room_id: num for num, room_id in enumerate(get_room_ids(rooms))},
    }

    lecturer_idx = data_idx["lecturers"]
    module_idx = data_idx["modules"]
    semester_idx  = data_idx["semesters"]
    day_idx  = data_idx["days"]
    room_idx  = data_idx["rooms"]

    # Add course to module dictionary
    # TODO string slicing is kinda wanky :D
    for module in modules:
        module["course"] = module["module_id"][1:3]

    # Create available_rooms_dic to check how many rooms are free for each time_slot
    available_rooms_dic = {(day, time_slot): [room_id for room_id in get_room_ids(rooms)]
        for day in days
        for time_slot in time_slots
        }

    # Create model
    model = cp_model.CpModel()
    timetable = generate_vars(model, data, data_idx)

    print("Variables: ", len(timetable))
    
    # # Constraint consecutive time_slots
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
    #                                     model.AddImplication(timetable[(lecturer_idx[lecturer["lecturer_id"]], module_idx[module["module_id"]], semester_idx[semester], day_idx[day], time_slot, room_idx[room["room_id"]])],
    #                                         timetable[(lecturer_idx[lecturer["lecturer_id"]], module_idx[module["module_id"]], semester_idx[semester], day_idx[day], time_slot, room_idx[room["room_id"]])])

    #                                     model.AddImplication(t0m, t1e)

    #                                     model.AddImplication(t0s, t2e)

    # if two block_sizes are the same, we need an additional constraint to enforce that block_1 != block_2, probably taken care of by the constraint that lecturers cannot be scheduled for two time_slots at the same time

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

    solver, status = solve_model(model)
    return retrieve_solution(data, data_idx, model, timetable, available_rooms_dic, solver, status)


def solve_model(model):
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
    return (solver, status)
    #return retrieve_solution(data, data_idx, model, timetable, available_rooms_dic)

def retrieve_solution(data, data_idx, model, timetable, available_rooms_dic, solver, status):
    lecturers = data["lecturers"]
    modules = data["modules"]
    semesters  = data["semesters"]
    days  = data["days"]
    time_slots  = data["time_slots"]
    rooms  = data["rooms"]
    
    lecturer_idx = data_idx["lecturers"]
    module_idx = data_idx["modules"]
    semester_idx  = data_idx["semesters"]
    day_idx  = data_idx["days"]
    room_idx  = data_idx["rooms"]

    solution = {}
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        for semester in semesters:
            solution.update({semester: {}})
            for day in days:
                solution[semester].update({day: {}})
                for time_slot in time_slots:
                    solution[semester][day].update({time_slot: {}})
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

                                    solution[semester][day][time_slot].update({
                                        "lecturer": lecturer,
                                        "module": module,
                                        "room": room,
                                    })

                                    available_rooms_dic[(day, time_slot)].remove(room["room_id"])

        print("RoomsAvailable: ", available_rooms(available_rooms_dic, days, time_slots))
        return solution
    else:
        # print(solver.ResponseStats())
        print("No feasible solution found.")
        return None


if __name__ == "__main__":
    main()
