from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import CpModel, CpSolver, IntVar, LinearExpr

from utils.BoolVarGenerator import BoolVarGenerator
from Data import Data

class Solver():

    def __init__(self) -> None:
        self.model = CpModel()
        self.data = Data()
        self.BoolVarGenObj = BoolVarGenerator(self.model, self.data)
        self.counter = 0
        
    def constraintHasTime(self):
        """
        Implied for every lecturer for every time_slot that time_slot bit == "1" | lecturers only give lectures when they are free (bit == "1")
        """
        print("Constraint Has Time")
        # self.hasTime = self.BoolVarGenObj.generateHasTime()
        for lecturer in self.data.lecturers:
            for day in self.data.days:
                for time_slot, bit in enumerate(lecturer[day]):

                    # self.model.AddImplication(self.hasTime[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.days_idx[day], time_slot)],
                    #     bit == "1"
                    #     )
                    
                    if bit == "1":
                        self.model.Add(self.hasTime[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.days_idx[day], time_slot)]
                            == 1)
                        self.counter += 1
                        print(self.counter)
                    else:
                        self.model.Add(self.hasTime[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.days_idx[day], time_slot)]
                            == 0)
                        self.counter += 1
        print(self.counter)

    def constraintCorrectLecturer(self):
        """
        Implied for every module that lecturer["lecturer_id"] in module["lecturer_id"] | modules can only be taught by their corresponding lecturer
        """
        print("Constraint Correct Lecturer")
        # self.correctLecturer = self.BoolVarGenObj.generateCorrectLecturer()
        for lecturer in self.data.lecturers:
            for module in self.data.modules:
                
                # self.model.AddImplication(self.correctLecturer[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.modules_idx[module["module_id"]])],
                #     lecturer["lecturer_id"] in module["lecturer_id"]
                #     )
                
                if lecturer["lecturer_id"] in module["lecturer_id"]:
                    self.model.Add(self.correctLecturer[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.modules_idx[module["module_id"]])]
                        == 1)
                    self.counter += 1
                    print(self.counter)
                else:
                    self.model.Add(self.correctLecturer[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.modules_idx[module["module_id"]])]
                        == 0)
                    self.counter += 1
        print(self.counter)

    def constraintCorrectSemester(self):
        """
        Implied for every module that semester == module["semester"] | modules linked to respective semesters
        """
        print("Constraint Correct Semester")
        # self.correctSemester = self.BoolVarGenObj.generateCorrectSemester()
        for module in self.data.modules:
            for semester in self.data.semesters:
                
                # self.model.AddImplication(self.correctSemester[(self.data.modules_idx[module["module_id"]], self.data.semesters_idx[semester])],
                #     semester == module["semester"]
                #     )
                
                if semester == module["semester"]:
                    self.model.Add(self.correctSemester[(self.data.modules_idx[module["module_id"]], self.data.semesters_idx[semester])]
                        == 1)
                    self.counter += 1
                    print(self.counter)
                else:
                    self.model.Add(self.correctSemester[(self.data.modules_idx[module["module_id"]], self.data.semesters_idx[semester])]
                        == 0)
                    self.counter += 1
        print(self.counter)

    def constraintFittingRoom(self):
        """
        Implied for every room that room["capacity"] >= module["participants"] | room has enough space for the module
        """
        print("Constraint Fitting Room")
        # self.fittingRoom = self.BoolVarGenObj.generateFittingRoom()
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
                    self.counter += 1
                    print(self.counter)
                else:
                    self.model.Add(self.fittingRoom[(self.data.modules_idx[module["module_id"]], self.data.rooms_idx[room["room_id"]])]
                        == 0)
                    self.counter += 1
        print(self.counter)

    def constraintOneModulePerRoom(self):
        """
        At most one room per module per time_slot | two modules cannot be scheduled in the same room at the same time
        """
        print("Constraint One Module Per Room")
        # self.oneModulePerRoom = self.BoolVarGenObj.generateOneModulePerRoom()
        for day in self.data.days:
            for time_slot in self.data.time_slots:
                for room in self.data.rooms:
                    self.model.AddAtMostOne(self.oneModulePerRoom[(self.data.modules_idx[module["module_id"]], self.data.days_idx[day], time_slot, self.data.rooms_idx[room["room_id"]])]
                    for module in self.data.modules
                    )
                    self.counter += 1
                    print(self.counter)
                for module in self.data.modules:
                    self.model.AddAtMostOne(self.oneModulePerRoom[(self.data.modules_idx[module["module_id"]], self.data.days_idx[day], time_slot, self.data.rooms_idx[room["room_id"]])]
                    for room in self.data.rooms
                    )
                    self.counter += 1
                    print(self.counter)
        print(self.counter)

    def constraintOneModulePerLecturer(self):
        """
        At most one module per lecturer per time_slot | a lecturer cannot be scheduled for two modules at the same time
        """
        print("Constraint One Module Per Lecturer")
        # self.oneModulePerLecturer = self.BoolVarGenObj.generateOneModulePerLecturer()
        for day in self.data.days:
            for time_slot in self.data.time_slots:
                for lecturer in self.data.lecturers:
                    self.model.AddAtMostOne(self.oneModulePerLecturer[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.modules_idx[module["module_id"]], self.data.days_idx[day], time_slot)]
                    for module in self.data.modules
                    )
                    self.counter += 1
                    print(self.counter)
                for module in self.data.modules:
                    self.model.AddAtMostOne(self.oneModulePerLecturer[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.modules_idx[module["module_id"]], self.data.days_idx[day], time_slot)]
                    for lecturer in self.data.lecturers
                    )
                    self.counter += 1
                    print(self.counter)
        print(self.counter)

    def constraintOneModulePerSemester(self):
        """
        At most one module per semester per time_slot | two modules in the same semester cannot be scheduled at the same time
        """
        print("Constraint One Module Per Semester")
        # self.oneModulePerSemester = self.BoolVarGenObj.generateOneModulePerSemester()
        for semester in self.data.semesters:
            for day in self.data.days:
                for time_slot in self.data.time_slots:
                    self.model.AddAtMostOne(self.oneModulePerSemester[(self.data.modules_idx[module["module_id"]], self.data.semesters_idx[semester], self.data.days_idx[day], time_slot)]
                    for module in self.data.modules
                    )
                    self.counter += 1
                    print(self.counter)
        print(self.counter)

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
            self.counter += 1
            print(self.counter)
        print(self.counter)

    def constraintCombine(self):
        
        for semester in self.data.semesters:
            for day in self.data.days:
                for time_slot in self.data.time_slots:
                        self.model.Add(LinearExpr.Sum([
                            self.correctSWS[(self.data.modules_idx[module["module_id"]], self.data.days_idx[day], time_slot)]
                        for module in self.data.modules
                        ] + [
                            self.hasTime[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.days_idx[day], time_slot)]
                        for lecturer in self.data.lecturers
                        ] + [
                            self.correctLecturer[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.modules_idx[module["module_id"]])]
                        for lecturer in self.data.lecturers
                        for module in self.data.modules
                        ] + [
                            self.correctSemester[(self.data.modules_idx[module["module_id"]], self.data.semesters_idx[semester])]
                        for module in self.data.modules
                        ] + [
                            self.fittingRoom[(self.data.modules_idx[module["module_id"]], self.data.rooms_idx[room["room_id"]])]
                        for module in self.data.modules
                        for room in self.data.rooms
                        ] + [
                            self.oneModulePerRoom[(self.data.modules_idx[module["module_id"]], self.data.days_idx[day], time_slot, self.data.rooms_idx[room["room_id"]])]
                        for module in self.data.modules
                        for room in self.data.rooms
                        ] + [
                            self.oneModulePerLecturer[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.modules_idx[module["module_id"]], self.data.days_idx[day], time_slot)]
                        for lecturer in self.data.lecturers
                        for module in self.data.modules
                        ] + [
                            self.oneModulePerSemester[(self.data.modules_idx[module["module_id"]], self.data.semesters_idx[module["semester"]], self.data.days_idx[day], time_slot)]
                        for module in self.data.modules
                        ]
                        ) <= 8)

    def addVariables(self):
        self.hasTime = self.BoolVarGenObj.generateHasTime()
        self.correctLecturer = self.BoolVarGenObj.generateCorrectLecturer()
        self.correctSemester = self.BoolVarGenObj.generateCorrectSemester()
        self.fittingRoom = self.BoolVarGenObj.generateFittingRoom()
        self.oneModulePerRoom = self.BoolVarGenObj.generateOneModulePerRoom()
        self.oneModulePerLecturer = self.BoolVarGenObj.generateOneModulePerLecturer()
        self.oneModulePerSemester = self.BoolVarGenObj.generateOneModulePerSemester()
        self.correctSWS = self.BoolVarGenObj.generateCorrectSWS()
    
    def addConstraints(self):
        self.constraintHasTime()
        self.constraintCorrectLecturer()
        self.constraintCorrectSemester()
        self.constraintFittingRoom()
        self.constraintOneModulePerRoom()
        self.constraintOneModulePerLecturer()
        self.constraintOneModulePerSemester()
        self.constraintCorrectSWS()
        
        self.constraintCombine()

    def solve(self):
        
        # self.CPsolver = CpSolver()
        # self.solution_printer = SolutionPrinter()
        # self.CPstatus = self.CPsolver.Solve(self.model, self.solution_printer)
        
        self.CPsolver = CpSolver()
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
            
        if self.counter > 100:
            return
        self.counter += 1
        print("SolutionCallback")
        