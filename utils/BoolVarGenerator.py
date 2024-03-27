from ortools.sat.python.cp_model import CpModel
from Data import Data


class BoolVarGenerator():
    
    def __init__(self, model:CpModel, data:Data) -> None:
        self.model = model
        self.data = data
    
    def generateHasTime(self):
        self.hasTime = {}
        for lecturer in self.data.lecturers:
            for day in self.data.days:
                for time_slot in self.data.time_slots:
                    self.hasTime[(
                        self.data.lecturers_idx[lecturer["lecturer_id"]],
                        self.data.days_idx[day],
                        time_slot
                    )] = self.model.NewBoolVar(
                        f'({lecturer["lecturer_id"]}, {day}, {time_slot})'
                    )
        return self.hasTime

    def generateCorrectLecturer(self):
        self.correctLecturer = {}
        for lecturer in self.data.lecturers:
            for module in self.data.modules:
                self.correctLecturer[(
                    self.data.lecturers_idx[lecturer["lecturer_id"]],
                    self.data.modules_idx[module["module_id"]]
                )] = self.model.NewBoolVar(
                    f'({lecturer["lecturer_id"]}, {module["module_id"]})'
                )
        return self.correctLecturer

    def generateCorrectSemester(self):
        self.correctSemester = {}
        for module in self.data.modules:
            for semester in self.data.semesters:
                self.correctSemester[(
                    self.data.modules_idx[module["module_id"]],
                    self.data.semesters_idx[semester]
                )] = self.model.NewBoolVar(
                    f'({module["module_id"]}, {semester})'
                )
        return self.correctSemester

    def generateFittingRoom(self):
        self.enoughSpace = {}
        for module in self.data.modules:
            for room in self.data.rooms:
                self.enoughSpace[(
                    self.data.modules_idx[module["module_id"]],
                    self.data.rooms_idx[room["room_id"]],
                )] = self.model.NewBoolVar(
                    f'({module["module_id"]}, {room["room_id"]})'
                )
        return self.enoughSpace

    def generateOneModulePerRoom(self):
        self.oneModulePerRoom = {}
        for module in self.data.modules:
            for day in self.data.days:
                for time_slot in self.data.time_slots:
                    for room in self.data.rooms:
                        self.oneModulePerRoom[(
                            self.data.modules_idx[module["module_id"]],
                            self.data.days_idx[day],
                            time_slot,
                            self.data.rooms_idx[room["room_id"]]
                        )] = self.model.NewBoolVar(
                            f'({module["module_id"]}, {day}, {time_slot}, {room["room_id"]})'
                        )
        return self.oneModulePerRoom
    
    def generateOneModulePerLecturer(self):
        self.oneModulePerLecturer = {}
        for lecturer in self.data.lecturers:
            for module in self.data.modules:
                for day in self.data.days:
                    for time_slot in self.data.time_slots:
                        self.oneModulePerLecturer[(
                            self.data.lecturers_idx[lecturer["lecturer_id"]],
                            self.data.modules_idx[module["module_id"]],
                            self.data.days_idx[day],
                            time_slot
                        )] = self.model.NewBoolVar(
                            f'({lecturer["lecturer_id"]}, {module["module_id"]}, {day}, {time_slot})'
                        )
        return self.oneModulePerLecturer
    
    def generateOneModulePerSemester(self):
        self.oneModulePerSemester = {}
        for module in self.data.modules:
            for semester in self.data.semesters:
                for day in self.data.days:
                    for time_slot in self.data.time_slots:
                        self.oneModulePerSemester[(
                            self.data.modules_idx[module["module_id"]],
                            self.data.semesters_idx[semester],
                            self.data.days_idx[day],
                            time_slot
                        )] = self.model.NewBoolVar(
                            f'({module["module_id"]}, {semester}, {day}, {time_slot})'
                        )
        return self.oneModulePerSemester
    
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
                        f'({module["module_id"]}, {day}, {time_slot})'
                    )
        return self.correctSWS