from ortools.sat.python.cp_model import CpModel
from Data import Data


class BoolVarGenerator():
    
    def __init__(self, model:CpModel, data:Data) -> None:
        self.model = model
        self.data = data

    def generateOneModulePerRoom(self):
        self.oneModulePerRoom = {}
        for module in self.data.modules:
            for room in self.data.rooms:
                if module["module_id"][0] == room["room_type"] and int(room["capacity"]) >= int(module["participants"]):
                    for day in self.data.days:
                        for time_slot in self.data.time_slots:
                            self.oneModulePerRoom[(
                                self.data.modules_idx[module["module_id"]],
                                self.data.days_idx[day],
                                time_slot,
                                self.data.rooms_idx[room["room_id"]]
                            )] = self.model.NewBoolVar(
                                f'{module["module_id"]}_{day}_{time_slot}_{room["room_id"]}'
                            )
        return self.oneModulePerRoom
    
    def generateOneModuleAndLecturerPerSemester(self):
        self.oneModuleAndLecturerPerSemester = {}
        for lecturer in self.data.lecturers:
            for module in self.data.modules:
                if lecturer["lecturer_id"] in module["lecturer_id"]:
                    for semester in self.data.semesters:
                        if semester == module["semester"]:
                            for day in self.data.days:
                                for time_slot, bit in enumerate(lecturer[day]):
                                    if bit == "1":
                                        self.oneModuleAndLecturerPerSemester[(
                                            self.data.lecturers_idx[lecturer["lecturer_id"]],
                                            self.data.modules_idx[module["module_id"]],
                                            self.data.semesters_idx[semester],
                                            self.data.days_idx[day],
                                            time_slot
                                        )] = self.model.NewBoolVar(
                                            f'{module["module_id"]}_{semester}_{day}_{time_slot}'
                                        )
        return self.oneModuleAndLecturerPerSemester
    
    def generateCorrectSWS(self):
        self.correctSWS = {}
        for module in self.data.modules:
            for day in self.data.days:
                for time_slot in self.data.time_slots:
                    self.correctSWS[(
                        self.data.modules_idx[module["module_id"]],
                        self.data.days_idx[day],
                        time_slot
                    )] = self.model.NewBoolVar(
                        f'{module["module_id"]}_{day}_{time_slot}'
                    )
        return self.correctSWS
    