from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import CpModel, CpSolver, IntVar, LinearExpr

from utils.BoolVarGenerator import BoolVarGenerator
from Data import Data

class Solver():

    def __init__(self) -> None:
        self.model = CpModel()
        self.data = Data()
        self.BoolVarGenObj = BoolVarGenerator(self.model, self.data)
        
    def constraintHasTime(self):
        """
        Implied for every lecturer for every time_slot that time_slot bit == "1" | lecturers only give lectures when they are free (bit == "1")
        """
        self.hasTime = self.BoolVarGenObj.generateHasTime()
        for lecturer in self.data.lecturers:
            for day in self.data.days:
                for time_slot, bit in enumerate(lecturer[day]):

                    # self.model.AddImplication(self.hasTime[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.days_idx[day], time_slot)],
                    #     bit == "1"
                    #     )
                    
                    if bit == "1":
                        self.model.Add(self.hasTime[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.days_idx[day], time_slot)]
                            == 1)
                    else:
                        self.model.Add(self.hasTime[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.days_idx[day], time_slot)]
                            == 0)

    def constraintCorrectLecturer(self):
        """
        Implied for every module that lecturer["lecturer_id"] in module["lecturer_id"] | modules can only be taught by their corresponding lecturer
        """
        self.correctLecturer = self.BoolVarGenObj.generateCorrectLecturer()
        for lecturer in self.data.lecturers:
            for module in self.data.modules:
                
                # self.model.AddImplication(self.correctLecturer[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.modules_idx[module["module_id"]])],
                #     lecturer["lecturer_id"] in module["lecturer_id"]
                #     )
                
                if lecturer["lecturer_id"] in module["lecturer_id"]:
                    self.model.Add(self.correctLecturer[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.modules_idx[module["module_id"]])]
                        == 1)
                else:
                    self.model.Add(self.correctLecturer[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.modules_idx[module["module_id"]])]
                        == 0)

    def constraintCorrectSemester(self):
        """
        Implied for every module that semester == module["semester"] | modules linked to respective semesters
        """
        self.correctSemester = self.BoolVarGenObj.generateCorrectSemester()
        for module in self.data.modules:
            for semester in self.data.semesters:
                
                # self.model.AddImplication(self.correctSemester[(self.data.modules_idx[module["module_id"]], self.data.semesters_idx[semester])],
                #     semester == module["semester"]
                #     )
                
                if semester == module["semester"]:
                    self.model.Add(self.correctSemester[(self.data.modules_idx[module["module_id"]], self.data.semesters_idx[semester])]
                        == 1)
                else:
                    self.model.Add(self.correctSemester[(self.data.modules_idx[module["module_id"]], self.data.semesters_idx[semester])]
                        == 0)

    def constraintfittingRoom(self):
        """
        Implied for every room that room["capacity"] >= module["participants"] | room has enough space for the module
        """
        self.fittingRoom = self.BoolVarGenObj.generateFittingRoom()
        for module in self.data.modules:
            for room in self.data.rooms:
                
                # self.model.AddImplication(self.fittingRoom[(self.data.modules_idx[module["module_id"]], self.data.rooms_idx[room["room_id"]])],
                #     room["capacity"] >= module["participants"]
                #     )
                # self.model.AddImplication(self.fittingRoom[(self.data.modules_idx[module["module_id"]], self.data.rooms_idx[room["room_id"]])],
                #     module["module_id"][0] == room["room_type"]
                # )
                
                if int(room["capacity"]) >= int(module["participants"]) and module["module_id"][0] == room["room_type"]:
                    self.model.Add(self.fittingRoom[(self.data.modules_idx[module["module_id"]], self.data.rooms_idx[room["room_id"]])]
                        == 1)
                else:
                    self.model.Add(self.fittingRoom[(self.data.modules_idx[module["module_id"]], self.data.rooms_idx[room["room_id"]])]
                        == 0)

    def constraintOneModulePerRoom(self):
        """
        At most one room per module per time_slot | two modules cannot be scheduled in the same room at the same time
        """
        self.oneModulePerRoom = self.BoolVarGenObj.generateOneModulePerRoom()
        for day in self.data.days:
            for time_slot in self.data.time_slots:
                for room in self.data.rooms:
                    self.model.AddAtMostOne(self.oneModulePerRoom[(self.data.modules_idx[module["module_id"]], self.data.days_idx[day], time_slot, self.data.rooms_idx[room["room_id"]])]
                    for module in self.data.modules
                    )
                for module in self.data.modules:
                    self.model.AddAtMostOne(self.oneModulePerRoom[(self.data.modules_idx[module["module_id"]], self.data.days_idx[day], time_slot, self.data.rooms_idx[room["room_id"]])]
                    for room in self.data.rooms
                    )

    def constraintOneModulePerLecturer(self):
        """
        At most one module per lecturer per time_slot | a lecturer cannot be scheduled for two modules at the same time
        """
        self.oneModulePerLecturer = self.BoolVarGenObj.generateOneModulePerLecturer()
        for day in self.data.days:
            for time_slot in self.data.time_slots:
                for lecturer in self.data.lecturers:
                    self.model.AddAtMostOne(self.oneModulePerLecturer[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.modules_idx[module["module_id"]], self.data.days_idx[day], time_slot)]
                    for module in self.data.modules
                    )
                for module in self.data.modules:
                    self.model.AddAtMostOne(self.oneModulePerLecturer[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.modules_idx[module["module_id"]], self.data.days_idx[day], time_slot)]
                    for lecturer in self.data.lecturers
                    )

    def constraintOneModulePerSemester(self):
        """
        At most one module per semester per time_slot | two modules in the same semester cannot be scheduled at the same time
        """
        self.oneModulePerSemester = self.BoolVarGenObj.generateOneModulePerSemester()
        for semester in self.data.semesters:
            for day in self.data.days:
                for time_slot in self.data.time_slots:
                    self.model.AddAtMostOne(self.oneModulePerSemester[(self.data.modules_idx[module["module_id"]], self.data.semesters_idx[module["semester"]], self.data.days_idx[day], time_slot)]
                    for module in self.data.modules
                    )

    def constraintCorrectSWS(self):
        """
        Sum( time_slots for module ) == module["sws"] | All sws have to be scheduled
        """
        self.correctSWS = self.BoolVarGenObj.generateCorrectSWS()
        for module in self.data.modules:
            self.model.Add(LinearExpr.Sum([self.correctSWS[(self.data.modules_idx[module["module_id"]], self.data.days_idx[day], time_slot)]
            for day in self.data.days
            for time_slot in self.data.time_slots
            ]) == int(module["sws"]))

    def constraintCombine(self):
        for lecturer in self.data.lecturers:
            for module in self.data.modules:
                for semester in self.data.semesters:
                    for day in self.data.days:
                        for time_slot in self.data.time_slots:
                            for room in self.data.rooms:
                                self.model.AddBoolAnd([
                                    self.hasTime[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.days_idx[day], time_slot)],
                                    self.correctLecturer[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.modules_idx[module["module_id"]])],
                                    self.correctSemester[(self.data.modules_idx[module["module_id"]], self.data.semesters_idx[semester])],
                                    self.fittingRoom[(self.data.modules_idx[module["module_id"]], self.data.rooms_idx[room["room_id"]])],
                                    self.oneModulePerRoom[(self.data.modules_idx[module["module_id"]], self.data.days_idx[day], time_slot, self.data.rooms_idx[room["room_id"]])],
                                    self.oneModulePerLecturer[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.modules_idx[module["module_id"]], self.data.days_idx[day], time_slot)],
                                    self.oneModulePerSemester[(self.data.modules_idx[module["module_id"]], self.data.semesters_idx[module["semester"]], self.data.days_idx[day], time_slot)],
                                    self.correctSWS[(self.data.modules_idx[module["module_id"]], self.data.days_idx[day], time_slot)],
                                ])

    def addConstraints(self):
        self.constraintHasTime()
        self.constraintCorrectLecturer()
        self.constraintCorrectSemester()
        self.constraintfittingRoom()
        self.constraintOneModulePerRoom()
        self.constraintOneModulePerLecturer()
        self.constraintOneModulePerSemester()
        self.constraintCorrectSWS()
        self.constraintCombine()

    def solve(self):
        self.CPsolver = CpSolver()
        self.CPstatus = self.CPsolver.Solve(self.model)
        return (self.CPsolver, self.CPstatus)
    
    def retrieve_solution(self):
        self.solution:dict[str, dict[str, dict[int, list | str]]] = {}
        if self.CPstatus == cp_model.OPTIMAL or self.CPstatus == cp_model.FEASIBLE:
            for semester in self.data.semesters:
                self.solution.update({semester: {}})
                for day in self.data.days:
                    self.solution[semester].update({day: {}})
                    for time_slot in self.data.time_slots:
                        self.solution[semester][day].update({time_slot: {}})
                        for lecturer in self.data.lecturers:
                            # print(self.CPsolver.Value(self.hasTime[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.days_idx[day], time_slot)]))
                            for module in self.data.modules:
                                for room in self.data.rooms:

                                    
                                    if (
                                            self.CPsolver.Value(self.hasTime[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.days_idx[day], time_slot)])
                                        and self.CPsolver.Value(self.correctLecturer[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.modules_idx[module["module_id"]])])
                                        and self.CPsolver.Value(self.correctSemester[(self.data.modules_idx[module["module_id"]], self.data.semesters_idx[semester])])
                                        and self.CPsolver.Value(self.fittingRoom[(self.data.modules_idx[module["module_id"]], self.data.rooms_idx[room["room_id"]])])
                                        and self.CPsolver.Value(self.oneModulePerRoom[(self.data.modules_idx[module["module_id"]], self.data.days_idx[day], time_slot, self.data.rooms_idx[room["room_id"]])])
                                        and self.CPsolver.Value(self.oneModulePerLecturer[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.modules_idx[module["module_id"]], self.data.days_idx[day], time_slot)])
                                        and self.CPsolver.Value(self.oneModulePerSemester[(self.data.modules_idx[module["module_id"]], self.data.semesters_idx[module["semester"]], self.data.days_idx[day], time_slot)])
                                        and self.CPsolver.Value(self.correctSWS[(self.data.modules_idx[module["module_id"]], self.data.days_idx[day], time_slot)])
                                    ):
                                        self.solution[semester][day][time_slot].update({
                                            "lecturer": lecturer,
                                            "module": module,
                                            "room": room,
                                        })
                                        
                                        if self.data.available_rooms_dict[(day, time_slot)].count(room["room_id"]):
                                            self.data.available_rooms_dict[(day, time_slot)].remove(room["room_id"])
                                    
                                    # self.solution[semester][day][time_slot].update({
                                    #     (lecturer["lecturer_id"], module["module_id"], room["room_id"]): 1
                                    # })
        
            return self.solution
        else:
            # print(solver.ResponseStats())
            print("No feasible solution found.")
            return None