# [x] Each lecturer
# [x] start OR end: 0 OR 00
# [x] 10 slots per day
# [x] 1 day: 0000000000
# [x] all days: 2-4 random slots = 0

import random

import pandas as pd


def create_data():
    lecturers_df = pd.read_csv("db/lecturers.csv", dtype=str)
    
    lecturers_data = lecturers_df.to_dict(orient="records")
    
    days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    lst_bool = [True, False]

    lecturers_data_randomized = []
    for lecturer in lecturers_data:
        for day in days:
            str_bit = ""
            start = random.choice(lst_bool)
            if start:
                one_zero = random.choice(lst_bool)
                if one_zero:
                    str_bit += "01"
                else:
                    str_bit += "00"

            for _ in range(8):
                chance = random.randint(0, 39)
                if chance <= 2:
                    str_bit += "0"
                else:
                    str_bit += "1"

            if not start:
                one_zero = random.choice(lst_bool)
                if one_zero:
                    str_bit += "10"
                else:
                    str_bit += "00"

            lecturer[day] = str_bit

        lecturer[random.choice(days)] = "0000000000"

        lecturers_data_randomized.append(lecturer)

    pd.DataFrame(lecturers_data_randomized).to_csv("db/lecturers.csv", index=False)
