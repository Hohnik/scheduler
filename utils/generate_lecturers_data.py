import pprint
import random

import pandas as pd

def main():
    pprint.pprint(generate_data())
    write_data("db/lecturers.csv", generate_data())

def write_generated_data():
    write_data("db/lecturers.csv", generate_data())

def write_data(path, data):
    pd.DataFrame(data).to_csv(path, index=False)

def generate_data():
    days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    empty_data = generate_lecturers_data_empty() 
    lst_bool = [True, False]

    result_rows = []
    for lecturer_row in empty_data:
        for day in days:
            time_slots = ""
            overslept = random.choice(lst_bool)
            if overslept:
                if random.choice(lst_bool):
                    time_slots += "01"
                else:
                    time_slots += "00"

            for _ in range(8):
                if random.randint(0, 39)<= 2:
                    time_slots += "0"
                else:
                    time_slots += "1"

            if not overslept:
                if random.choice(lst_bool):
                    time_slots += "10"
                else:
                    time_slots += "00"

            lecturer_row[day] = time_slots
        lecturer_row[random.choice(days)] = "0"*10
        result_rows.append(lecturer_row)
    return result_rows

def generate_lecturers_data_empty():
    names = ["Osendorfer", "Kromer", "Eisenreich", "Auer", "Ziegler", "Uhrmann", "Siebert", "Schröter", "Nazareth"]
    names_iter = iter(names)

    result_object = []
    for i in range(len(names)):
        result_object.append(
            {
                "lecturer_id": f"{i+1:03d}",
                "monday": None,
                "tuesday": None,
                "wednesday": None,
                "thursday": None,
                "friday": None,
                "lecturer_name": f"{next(names_iter)}",
            }
        )
    return result_object

if __name__ == "__main__":
    main()
