# [x] Each module
# [x] capacity: 20-50

import random

import pandas as pd


def create_data():
    modules_df = pd.read_csv("db/modules.csv", dtype=str)
    
    modules_data = modules_df.to_dict(orient="records")
    
    semesters = list(set([dct["semester"] for dct in modules_data]))
    semesters.sort()
    lst_bool = [True, False]
    

    modules_data_randomized = []
    for module in modules_data:
        if module["module_id"][0] == "l":
            module["participants"] = random.choices([num for num in range(20,51)], [weight/sum([x for x in range(31)]) for weight in range(31)])[0]
            modules_data_randomized.append(module)
        else:
            module["participants"] = 0
            #module["participants"] = random.choices([num for num in range(10,21)], [weight/sum([x for x in range(11)]) for weight in range(11)])[0]
            modules_data_randomized.append(module)


    pd.DataFrame(modules_data_randomized).to_csv("db/modules.csv", index=False)
