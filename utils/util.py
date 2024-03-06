import pandas as pd
from ortools.sat.python import cp_model


def data_to_dict_from(path) -> list[dict]:
    return pd.read_csv(path, dtype=str).to_dict(orient="records")


def generate_vars(model, data, data_idx):
        vars = {}
        for lecturer in data["lecturers"]:
            for module in data["modules"]:
                for semester in data["semesters"]:
                    # block_type_tracker = []
                    for block in module["block_sizes_dic"]:
                        # block_type = block[0]
                        # if block_type in block_type_tracker:
                        #     continue
                        # else:
                        #     block_type_tracker.append(block_type)
                        for day in data["days"]:
                            for time_slot in data["time_slots"]:
                                block_size = block[0]
                                for position in calculate_positions(block_size):
                                    for room in data["rooms"]:
                                        vars[(
                                            data_idx["lecturers"][lecturer["lecturer_id"]],
                                            data_idx["modules"][module["module_id"]],
                                            data_idx["semesters"][semester],
                                            data_idx["days"][day],
                                            time_slot,
                                            data_idx["positions"][position],
                                            module["block_sizes_dic"][block],
                                            data_idx["rooms"][room["room_id"]],
                                        )] = model.NewBoolVar(
                                            f'{lecturer["lecturer_id"]}_{module["module_id"]}_{semester}_{day}_{time_slot}_{position}_{block}_{room["room_id"]}'
                                        )

        return vars

def calculate_positions(block_size):
    if block_size == 1:
        return ["s"]
    elif block_size == 2:
        return ["s", "e"]
    elif block_size >= 3:
        return ["s"] + calculate_block_size_greater3(block_size-2, block_size-2) + ["e"]

def calculate_block_size_greater3(block_size, num):
    if block_size == 1:
        return [f"m_{num-1}"]
    else:
        num -= 1
        return calculate_block_size_greater3(block_size-1, num) + [f"m_{num}"]

def modify_modules(modules:list[dict]) -> None:
    for module_1 in modules:
        for module_2 in modules:
            if (module_1["module_id"][1:] == module_2["module_id"][1:]) and (module_1["module_id"][0] == "p") and module_2["module_id"][0] == "l":
                practice, lecture = module_1, module_2
                practice_count = (int(lecture["participants"]) // int(practice["max_participants"])) + 1
                remaining_participants = int(lecture["participants"])

                for practice_index in range(practice_count):
                    practice_copy = practice.copy()
                    practice_copy["module_id"] = practice_copy["module_id"] + '_' + str(practice_index+1)

                    participants = remaining_participants // practice_count
                    practice_copy["participants"] = str(participants)
                    remaining_participants -= participants

                    practice_count -= 1
                    modules.append(practice_copy)

                modules.remove(practice)

                lecture_copy = lecture.copy()
                lecture_copy["module_id"] = lecture_copy["module_id"] + '_0'
                modules.append(lecture_copy)
                modules.remove(lecture)


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


# def calculate_session_blocks(leftover_sws:str):
#     #return [1]
#     session_blocks = []
#     leftover_sws = int(leftover_sws)
#     while leftover_sws > 0:
#         if leftover_sws % 2 == 0:
#             leftover_sws -= 2
#             session_blocks.append(2)
#         elif leftover_sws >= 3:
#             leftover_sws -= 3
#             session_blocks.append(3)
#         elif leftover_sws == 1:
#             leftover_sws -= 1
#             session_blocks.append(1)

#     return session_blocks

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

def available_rooms(available_rooms_dic, days, time_slots):
    '''number of available rooms per time_slot'''
    numof_available_rooms_lst = [len(available_rooms_dic[(day, time_slot)]) for day in days for time_slot in time_slots]
    n_a_r_l_dic = {}
    for elem in numof_available_rooms_lst:
        if elem in n_a_r_l_dic:
            n_a_r_l_dic[elem] += 1
        else:
            n_a_r_l_dic[elem] = 1
    return n_a_r_l_dic


def is_practice(module):
    if module["module_id"][0] == "p":
        return True


def is_module_lecturer(module, lecturer):
    if module["lecturer_id"] == lecturer["lecturer_id"]:
        return True
    else:
        return False

def get_lecturer_ids(lecturers:list[dict]) -> list[str]:
    return [lecturer["lecturer_id"] for lecturer in lecturers]

def get_module_ids(modules:list[dict]) -> list[str]:
    return [module["module_id"] for module in modules]

def get_room_ids(rooms:list[dict]) -> list[str]:
    return [room["room_id"] for room in rooms]

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
    # positions  = data["positions"]
    rooms  = data["rooms"]
    
    lecturer_idx = data_idx["lecturers"]
    module_idx = data_idx["modules"]
    semester_idx  = data_idx["semesters"]
    day_idx  = data_idx["days"]
    position_idx  = data_idx["positions"]
    room_idx  = data_idx["rooms"]

    solution:dict[str, dict[str, dict[int, list | str]]] = {}
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        for semester in semesters:
            solution.update({semester: {}})
            print(semester)
            for day in days:
                solution[semester].update({day: {}})
                print(day)
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
                                                "room": room,
                                            })
                                            print(f'{module["module_id"]}, {time_slot}, {position}, {room["room_id"]}, {lecturer["lecturer_name"]}')
                                            if available_rooms_dic[(day, time_slot)].count(room["room_id"]):
                                                available_rooms_dic[(day, time_slot)].remove(room["room_id"])

        print("RoomsAvailable: ", available_rooms(available_rooms_dic, days, time_slots))
        return solution
    else:
        # print(solver.ResponseStats())
        print("No feasible solution found.")
        return None
    
if __name__ == "__main__":
    
    # print(calculate_positions(1))
    # print(calculate_positions(2))
    # print(calculate_positions(3))
    # print(calculate_positions(4))
    # print(calculate_positions(5))
    # print(calculate_positions(6))
    # print(calculate_positions(7))
    # print(calculate_positions(8))
    # print(calculate_positions(9))
    
    pass