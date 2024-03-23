from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import IntVar

import utils.generate_lecturers_data as gld
import utils.generate_modules_data as gmd
from utils.table_printer import TablePrinter
from utils.util2 import *

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
    
    modify_modules(data["modules"]) # Generate praktika
