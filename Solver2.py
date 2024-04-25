from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import CpModel, CpSolver, IntVar, LinearExpr

from utils.BoolVarGenerator2 import BoolVarGenerator
from Data import Data

class Solver():

    def __init__(self) -> None:
        self.model = CpModel()
        self.data = Data()
        self.BoolVarGenObj = BoolVarGenerator(self.model, self.data)

    def constraintOneModulePerRoom(self):
        """
        At most one room per module per time_slot | two modules cannot be scheduled in the same room at the same time
        """
        print("Constraint One Module Per Room")
        # self.oneModulePerRoom = self.BoolVarGenObj.generateOneModulePerRoom()
        for day in self.data.days:
            for time_slot in self.data.time_slots:
                for room in self.data.rooms:
                    oneModulePerRoom_lst = []
                    for module in self.data.modules:
                        if module["module_id"][0] == room["room_type"] and int(room["capacity"]) >= int(module["participants"]):
                            oneModulePerRoom_lst.append(self.oneModulePerRoom[(self.data.modules_idx[module["module_id"]], self.data.days_idx[day], time_slot, self.data.rooms_idx[room["room_id"]])])
                    self.model.AddAtMostOne(oneModulePerRoom_lst)
                
                for module in self.data.modules:
                    oneRoomPerModule_lst = []
                    for room in self.data.rooms:
                        if module["module_id"][0] == room["room_type"] and int(room["capacity"]) >= int(module["participants"]):
                            oneRoomPerModule_lst.append(self.oneModulePerRoom[(self.data.modules_idx[module["module_id"]], self.data.days_idx[day], time_slot, self.data.rooms_idx[room["room_id"]])])
                    self.model.AddAtMostOne(oneRoomPerModule_lst)

    def constraintOneModuleAndLecturerPerSemesterPerTimeslot(self):
        """
        At most one module per semester per time_slot | two modules in the same semester cannot be scheduled at the same time
        """
        print("Constraint One Module Per Semester")
        # self.oneModulePerSemester = self.BoolVarGenObj.generateOneModulePerSemester()
        for semester in self.data.semesters:
            for day in self.data.days:
                for time_slot in self.data.time_slots:
                    oneModuleAndLecturerPerSemester_lst = []
                    for module in self.data.modules:
                        if semester == module["semester"]:
                            for lecturer in self.data.lecturers:
                                if lecturer["lecturer_id"] in module["lecturer_id"]:
                                    bit = lecturer[day][time_slot]
                                    if bit == "1":
                                        oneModuleAndLecturerPerSemester_lst.append(self.oneModuleAndLecturerPerSemester[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.modules_idx[module["module_id"]], self.data.semesters_idx[semester], self.data.days_idx[day], time_slot)])
                    self.model.AddAtMostOne(oneModuleAndLecturerPerSemester_lst)

    def constraintCorrectSWS(self):
        """
        Sum( time_slots for module ) == module["sws"] | All sws have to be scheduled
        """
        print("Constraint Correct SWS")
        # self.correctSWS = self.BoolVarGenObj.generateCorrectSWS()
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
                                if module["module_id"][0] == room["room_type"] and int(room["capacity"]) >= int(module["participants"]):
                                    if semester == module["semester"]:
                                        if lecturer["lecturer_id"] in module["lecturer_id"]:
                                            bit = lecturer[day][time_slot]
                                            if bit == "1":
                                                    self.model.AddBoolOr([
                                                        # self.oneModulePerRoom[(self.data.modules_idx[module["module_id"]], self.data.days_idx[day], time_slot, self.data.rooms_idx[room["room_id"]])],
                                                        self.oneModuleAndLecturerPerSemester[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.modules_idx[module["module_id"]], self.data.semesters_idx[semester], self.data.days_idx[day], time_slot)].Not(),
                                                        self.correctSWS[(self.data.modules_idx[module["module_id"]], self.data.days_idx[day], time_slot)]
                                                    ])
                                                    self.model.AddBoolOr([
                                                        self.correctSWS[(self.data.modules_idx[module["module_id"]], self.data.days_idx[day], time_slot)].Not(),
                                                        self.oneModuleAndLecturerPerSemester[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.modules_idx[module["module_id"]], self.data.semesters_idx[semester], self.data.days_idx[day], time_slot)]
                                                    ])

    def addVariables(self):
        # self.oneModulePerRoom = self.BoolVarGenObj.generateOneModulePerRoom()
        self.oneModuleAndLecturerPerSemester = self.BoolVarGenObj.generateOneModuleAndLecturerPerSemester()
        self.correctSWS = self.BoolVarGenObj.generateCorrectSWS()
    
    def addConstraints(self):
        # self.constraintOneModulePerRoom()
        self.constraintOneModuleAndLecturerPerSemesterPerTimeslot()
        self.constraintCorrectSWS()
        
        self.constraintCombine()

    def solve(self):
        
        # self.CPsolver = CpSolver()
        # self.solution_printer = SolutionPrinter()
        # self.CPstatus = self.CPsolver.Solve(self.model, self.solution_printer)
        
        self.CPsolver = CpSolver()
        self.CPsolver.parameters.log_search_progress = True
        self.CPcallback = SolutionPrinter()
        self.CPstatus = self.CPsolver.Solve(self.model)
        # self.CPstatus = self.CPsolver.SearchForAllSolutions(self.model, SolutionPrinter())

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
                                        and self.CPsolver.Value(self.oneModuleAndLecturerPerSemester[(self.data.modules_idx[module["module_id"]], self.data.semesters_idx[module["semester"]], self.data.days_idx[day], time_slot)])
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
        

class SolutionPrinter(cp_model.CpSolverSolutionCallback):
        
    counter = 0
    def __init__(self):
        super().__init__()
        self.solutions = []  # Store solutions
        self.max_solutions = 10  # Example stop condition

    def on_solution_callback(self) -> None:
        self.solutions.append(self.ObjectiveValue())
        if len(self.solutions) >= self.max_solutions:
            print(f"Stopping after {self.max_solutions} solutions.")
            pass
            
            return
        print("SolutionCallback")
        