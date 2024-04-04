import pprint
import time
import pandas as pd
from ortools.sat.python import cp_model


def data_to_dict_from(path) -> list[dict]:
    return pd.read_csv(path, dtype=str).to_dict(orient="records")

def generate_days(lecturers):
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    result = []
    for day in days:
        try:
            lecturers[0][day]
            result.append(day)
        except KeyError:
            continue
    return result

def modify_modules(modules:list[dict]) -> None:
    modules_new = []
    for module_1 in modules:
        # print(module_1['module_name'])
        for module_2 in modules:
            if (module_1["module_id"][1:] == module_2["module_id"][1:]) and (module_1["module_id"][0] == "p") and module_2["module_id"][0] == "l":
                practice, lecture = module_1, module_2
                practice_count = (int(lecture["participants"]) // int(practice["max_participants"])) + 1
                
                # pprint.pprint(f'{module_1["module_id"]}: {practice_count}')
                remaining_participants = int(lecture["participants"])

                for practice_index in range(practice_count):
                    practice_copy = practice.copy()
                    practice_copy["module_id"] = practice_copy["module_id"] + '_' + str(practice_index+1)

                    participants = remaining_participants // practice_count
                    practice_copy["participants"] = str(participants)
                    remaining_participants -= participants

                    practice_count -= 1
                    modules_new.append(practice_copy)

                lecture_copy = lecture.copy()
                lecture_copy["module_id"] = lecture_copy["module_id"] + '_0'
                modules_new.append(lecture_copy)
        # if module_1["module_id"][0] == 'l':
        #     modules_new.append(module_1)
    
    return modules_new

def get_lecturer_ids(lecturers:list[dict]) -> list[str]:
    return [lecturer["lecturer_id"] for lecturer in lecturers]

def get_module_ids(modules:list[dict]) -> list[str]:
    return [module["module_id"] for module in modules]

def get_room_ids(rooms:list[dict]) -> list[str]:
    return [room["room_id"] for room in rooms]

def calculate_session_blocks(sws:str) -> dict[tuple[int, int], int]:
    #return [1]
    block_sizes_dic = {}
    num = 0
    key_1 = 0
    key_2 = 0
    key_3 = 0
    leftover_sws = int(sws)
    while leftover_sws > 0:
        if leftover_sws % 2 == 0:
            block_sizes_dic[(2, key_2)] = num
            num += 1
            key_2 += 1
            leftover_sws -= 2
        elif leftover_sws >= 3:
            block_sizes_dic[(3, key_3)] = num
            num += 1
            key_3 += 1
            leftover_sws -= 3
        elif leftover_sws == 1:
            block_sizes_dic[(1, key_1)] = num
            num += 1
            key_1 += 1
            leftover_sws -= 1
    
    return block_sizes_dic

def retrieve_solution(data, data_idx, model, timetable, available_rooms_dic, solver, status):
    lecturers = data["lecturers"]
    modules = data["modules"]
    semesters  = data["semesters"]
    days  = data["days"]
    time_slots  = data["time_slots"]
    # positions  = data["positions"]
    rooms  = data["rooms"]
    
    lecturer_idx = data_idx["lecturers"]
    module_idx = data_idx["modules"]
    semester_idx  = data_idx["semesters"]
    day_idx  = data_idx["days"]
    position_idx  = data_idx["positions"]
    room_idx  = data_idx["rooms"]

    print("Retrieving solution...")
    start_time = time.time()
    solution:dict[str, dict[str, dict[int, list | str]]] = {}
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        for semester in semesters:
            solution.update({semester: {}})
            # print(semester)
            for day in days:
                solution[semester].update({day: {}})
                # print(day)
                for time_slot in time_slots:
                    solution[semester][day].update({time_slot: {}})
                    for lecturer in lecturers:
                        for module in modules:
                            for block in module["block_sizes_dic"]:
                                for position in calculate_positions(block[0]):
                                    for room in rooms:

                                        if solver.Value(timetable[(
                                            lecturer_idx[lecturer["lecturer_id"]], 
                                            module_idx[module["module_id"]],
                                            semester_idx[semester], 
                                            day_idx[day], 
                                            time_slot,
                                            position_idx[position],
                                            module["block_sizes_dic"][block],
                                            room_idx[room["room_id"]])]):

                                            solution[semester][day][time_slot].update({
                                                "lecturer": lecturer,
                                                "module": module,
                                                "position": position,
                                                "block": block,
                                                "room": room,
                                            })
                                            # print(f'{module["module_id"]}, {time_slot}, {position}, {room["room_id"]}, {lecturer["lecturer_name"]}')
                                            if available_rooms_dic[(day, time_slot)].count(room["room_id"]):
                                                available_rooms_dic[(day, time_slot)].remove(room["room_id"])
    
        print("Solution retrieved.")
        end_time = time()
        print(f"{round(end_time - start_time, 2)} secs")
        print()
    
        print("RoomsAvailable: ", available_rooms(available_rooms_dic, days, time_slots))
        return solution
    else:
        # print(solver.ResponseStats())
        print("No feasible solution found.")
        return None
    
