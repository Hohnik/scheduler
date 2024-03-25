from ortools.sat.python.cp_model import CpModel


class VarGen():
    
    def __init__(self, model:CpModel, data: dict[str, list[dict] | list[str] | range], data_idx:dict[str, dict[str, int]]) -> None:
        self.model = model
        self.data = data
        self.data_idx = data_idx
        self.unpack_data(data)
        self.unpack_data_idx(data_idx)
        
    def unpack_data(self, data):
        self.lecturers = data["lecturers"] 
        self.modules = data["modules"] 
        self.semesters = data["semesters"] 
        self.days = data["days"] 
        self.time_slots = data["time_slots"]
        self.rooms = data["rooms"]
        
    def unpack_data_idx(self, data_idx):
        self.lecturers_idx = data_idx["lecturers"]
        self.modules_idx = data_idx["modules"]
        self.semesters_idx  = data_idx["semesters"]
        self.days_idx  = data_idx["days"]
        self.positions_idx = data_idx["positions"]
        self.rooms_idx  = data_idx["rooms"]
    
    def hasTime(self):
        hasTime = {}
        for lecturer in self.lecturers:
            for day in self.days:
                for time_slot in self.time_slots:
                    hasTime[(
                        self.lecturers_idx[lecturer["lecturer_id"]],
                        self.days_idx[day],
                        time_slot
                    )] = self.model.NewBoolVar(
                        f'({lecturer["lecturer_id"]}, {day}, {time_slot})'
                    )
        return hasTime

    def correctLecturer(self):
        correctLecturer = {}
        for lecturer in self.lecturers:
            for module in self.data["modules"]:
                correctLecturer[(
                    self.lecturers_idx[lecturer["lecturer_id"]],
                    self.modules_idx[module["module_id"]]
                )] = self.model.NewBoolVar(
                    f'({lecturer["lecturer_id"]}, {module["module_id"]})'
                )
        return correctLecturer

    def correctSemester(self):
        correctSemester = {}
        for module in self.data["modules"]:
            for semester in self.data["semesters"]:
                correctSemester[(
                    self.modules_idx[module["modules_id"]],
                    self.semesters_idx[semester]
                )] = self.model.NewBoolVar(
                    f'({module["modules_id"]}, {semester})'
                )
        return correctSemester

    def fittingRoom(self):
        enoughSpace = {}
        for module in self.data["modules"]:
            for room in self.data["rooms"]:
                enoughSpace[(
                    self.modules_idx[module["module_id"]],
                    self.rooms_idx[room["room_id"]],
                )] = self.model.NewBoolVar(
                    f'({module["module_id"]}, {room["room_id"]})'
                )
        return enoughSpace

    def oneModulePerRoom(self):
        oneModulePerRoom = {}
        for module in self.modules:
            for day in self.days:
                for time_slot in self.time_slots:
                    for room in self.data["rooms"]:
                        oneModulePerRoom[(
                            self.modules_idx[module["module_id"]],
                            self.days_idx[day],
                            time_slot,
                            self.rooms_idx[room["room_id"]]
                        )] = self.model.NewBoolVar(
                            f'({module["module_id"]}, {day}, {time_slot}, {room["room_id"]})'
                        )
        return oneModulePerRoom
    
    def oneModulePerLecturer(self):
        oneModulePerLecturer = {}
        for lecturer in self.lecturers:
            for module in self.modules:
                for day in self.days:
                    for time_slot in self.time_slots:
                        oneModulePerLecturer[(
                            self.lecturers_idx[lecturer["lecturer_id"]],
                            self.modules_idx[module["module_id"]],
                            self.days_idx[day],
                            time_slot
                        )] = self.model.NewBoolVar(
                            f'({lecturer["lecturer_id"]}, {module["module_id"]}, {day}, {time_slot})'
                        )
        return oneModulePerLecturer
    
    def oneModulePerSemester(self):
        oneModulePerSemester = {}
        for module in self.modules:
            for semester in self.semesters:
                for day in self.days:
                    for time_slot in self.time_slots:
                        oneModulePerSemester[(
                            self.modules_idx[module["module_id"]],
                            self.semesters_idx[semester],
                            self.days_idx[day],
                            time_slot
                        )] = self.model.NewBoolVar(
                            f'({module["module_id"]}, {semester}, {day}, {time_slot})'
                        )
        return oneModulePerSemester
    
    def correctSWS(self):
        correctSWS = {}
        for module in self.modules:
            for day in self.days:
                for time_slot in self.time_slots:
                    correctSWS[(
                        self.modules_idx[module["module_id"]],
                        self.days_idx[day],
                        time_slot
                    )] = self.model.NewBoolVar(
                        f'({module["module_id"]}, {day}, {time_slot})'
                    )
        return correctSWS