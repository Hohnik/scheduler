import pprint
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