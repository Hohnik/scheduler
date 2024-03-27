import pandas as pd

class Data():
    def __init__(self):
        self.data = self.load_data_from_database()
        self.data.update(self.generate_semesters())
        self.data.update(self.generate_days())
        self.data.update(self.generate_time_slots())
        
        self.data.update({"modules": self.modified_modules()})
        
        self.unpack_data()
        self.unpack_data_idx()
        
        self.add_module_course()
        self.generate_lecturer_skipped_time_slots()
        self.generate_module_session_blocks()
        
        self.available_rooms_dict = self.generate_available_rooms_dic()
        
    def unpack_data(self):
        self.lecturers = self.data["lecturers"] 
        self.modules = self.data["modules"] 
        self.semesters = self.data["semesters"] 
        self.days = self.data["days"] 
        self.time_slots = self.data["time_slots"]
        self.rooms = self.data["rooms"]
        
    def unpack_data_idx(self):
        self.lecturers_idx = {lecturer_id: num for num, lecturer_id in enumerate(self.get_lecturer_ids())}
        self.modules_idx = {module_id: num for num, module_id in enumerate(self.get_module_ids())}
        self.semesters_idx  = {semester: num for num, semester in enumerate(self.semesters)}
        self.days_idx  = {day: num for num, day in enumerate(self.days)}
        self.positions_idx = {"s": 0, "m_0": 1, "e": 2}
        self.rooms_idx  = {room_id: num for num, room_id in enumerate(self.get_room_ids())}

    def get_lecturer_ids(self) -> list[str]:
        return [lecturer["lecturer_id"] for lecturer in self.lecturers]

    def get_module_ids(self) -> list[str]:
        return [module["module_id"] for module in self.modules]

    def get_room_ids(self) -> list[str]:
        return [room["room_id"] for room in self.rooms]
    
    def load_data_from_database(self) -> dict[str, list[str, dict]]:
        return {
            "lecturers": self.data_to_dict("db/lecturers.csv"),
            "modules": self.data_to_dict("db/modules.csv"),
            "rooms": self.data_to_dict("db/rooms.csv"),
        }
    
    def generate_semesters(self):
        return {
            "semesters": sorted(list(set([module.get("semester") for module in self.data.get("modules")])))
        }
    
    def generate_days(self):
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        result = []
        for day in days:
            try:
                self.data["lecturers"][0][day]
                result.append(day)
            except KeyError:
                continue
        return {
            "days": result
        }

    def generate_time_slots(self):
        return {
            "time_slots": range(len(self.data.get("lecturers")[0][self.data.get("days")[0]])),
        }

    @classmethod
    def data_to_dict(self, path) -> list[dict]:
        return pd.read_csv(path, dtype=str).to_dict(orient="records")
    
    def modified_modules(self) -> None:
        modules_new = []
        for module_1 in self.data["modules"]:
            # print(module_1['module_name'])
            for module_2 in self.data["modules"]:
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
    
    def add_module_course(self):
        """
        Add course to module dictionary
        """
        for module in self.modules:
            module["course"] = module["module_id"][1:3]

    def generate_lecturer_skipped_time_slots(self):
        """
        Generate lecturer["skip_time_slots"] dictionary for each lecturer for faster access
        """
        for lecturer in self.lecturers:
            lecturer["skip_time_slots"] = {(day, time_slot): bit == "0" for day in self.days for time_slot, bit in enumerate(self.time_slots)}
    
    def generate_module_session_blocks(self):
        """
        Calculate module["session_blocks"] list for each module
        """
        for module in self.modules:
            module["block_sizes_dic"] = self.calculate_session_blocks(module["sws"])
    
    def generate_available_rooms_dic(self):
        """
        Create available_rooms_dic to check how many rooms are free for each time_slot
        """
        return {
            (day, time_slot): [room_id for room_id in self.get_room_ids()]
            for day in self.days
            for time_slot in self.time_slots
        }
    
    def calculate_session_blocks(self, sws:str) -> dict[tuple[int, int], int]:
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