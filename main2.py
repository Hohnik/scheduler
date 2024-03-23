import pprint
from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import IntVar

from utils.util2 import *
from utils.util2_generate_vars import *

def main():
    pass

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
    # data.update({
    #     "positions": ["s", "m_1", "e"] # ORDER IS IMPORTANT. We can add a key max_block_size in modules.csv to indicate the longest block_size for each module. Then we can calculate the possible positions for each module, but we would have to slightly adjust the calculate_session_blocks function to allow for different block_sizes for each module. # TODO Just add the parameter module["max_block_size"] to calculate_session_blocks which then defines which block_size calculation logic is used. Currently, the longest block_size is 3. This would be the default value.
    # })
    # pprint.pprint(data["modules"])
    data["modules"] = modify_modules(data["modules"]) # Generate praktika

    lecturers = data["lecturers"] 
    modules = data["modules"] 
    semesters = data["semesters"] 
    days = data["days"] 
    time_slots = data["time_slots"]
    rooms = data["rooms"] 


    data_idx:dict[str, dict[str, int]] = {
        "lecturers":{lecturer_id: num for num, lecturer_id in enumerate(get_lecturer_ids(lecturers))},
        "modules": {module_id: num for num, module_id in enumerate(get_module_ids(modules))},
        "semesters": {semester: num for num, semester in enumerate(semesters)},
        "days": {day: num for num, day in enumerate(days)},
        "positions": {"s": 0, "m_0": 1, "e": 2},
        "rooms": {room_id: num for num, room_id in enumerate(get_room_ids(rooms))},
    }

    lecturers_idx = data_idx["lecturers"]
    modules_idx = data_idx["modules"]
    semesters_idx  = data_idx["semesters"]
    days_idx  = data_idx["days"]
    positions_idx = data_idx["positions"]
    rooms_idx  = data_idx["rooms"]

    # Add course to module dictionary
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

    model = cp_model.CpModel()
    
    # Implied for every lecturer for every time_slot that time_slot bit == "1" | lecturers only give lectures when they are free (bit == "1")
    hasTime = generate_hasTime(model, data, data_idx)
    for lecturer in lecturers:
        for day in days:
            for time_slot, bit in enumerate(lecturers[day]):
                model.AddImplication(hasTime[(lecturers_idx[lecturer["lecturer_id"]], days_idx[day], time_slot)],
                    bit == "1"
                    )
    
    # Implied for every module that lecturer["lecturer_id"] in module["lecturer_id"] | modules can only be taught by their corresponding lecturer
    correctLecturer = generate_correctLecturer(model, data, data_idx)
    for lecturer in lecturers:
        for module in modules:
            model.AddImplication(correctLecturer[(lecturers_idx[lecturer["lecturer_id"]], modules_idx[module["modules_id"]])],
                lecturer["lecturer_id"] in module["lecturer_id"]
                )
    
    # Implied for every module that semester == module["semester"] | modules linked to respective semesters
    correctSemester = generate_correctSemester(model, data, data_idx)
    for module in modules:
        for semester in semesters:
            model.AddImplication(correctSemester[(modules_idx[module["modules_id"]], semesters_idx[semester])],
                semester == module["semester"]
                )
    
    