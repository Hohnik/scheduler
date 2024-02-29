import pandas as pd

def read_data_from(path) -> list[dict]:
    return pd.read_csv(path, dtype=str).to_dict(orient="records")

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