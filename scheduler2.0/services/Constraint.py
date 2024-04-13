from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import CpModel, CpSolver, IntVar, LinearExpr

from services.Data import Data


class Constraint:
    def __init__(self, bools:dict, model:CpModel, data:Data):
        self.bools = bools
        self.model = model
        self.data = data

        self.all_semesters = range(len(data.semesters))
        self.all_days = range(len(data.days))
        self.all_timeslots = range(len(data.timeslots))
        self.all_lecturers = range(len(data.lecturers))
        self.all_modules = range(len(data.modules))

    def oneModulePerTimeslot(self):
        """
        Each slot is assigned to exactly one lecturer-module combo.
        """
        for s in self.all_semesters:
            for d in self.all_days:
                for t in self.all_timeslots:
                    combo = []
                    for m in self.all_modules:
                        for l in self.all_lecturers:
                            if (s, d, t, m, l) in self.bools.keys():
                                combo.append(self.bools[(s, d, t, m, l)])
                    self.model.AddAtMostOne(combo)
                    
    def correctSWS(self):
        """
        Sum( time_slots for module ) == module["sws"] | All sws have to be scheduled
        """
        for m in self.all_modules:
            combo = []
            for l in self.all_lecturers:
                for s in self.all_semesters:
                    for d in self.all_days:
                        for t in self.all_timeslots:
                            if (s, d, t, m, l) in self.bools.keys():
                                combo.append(self.bools[(s, d, t, m, l)])
            self.model.Add(LinearExpr.Sum(combo) == int(self.data.modules["sws"][m]))

    def oneModulePerLecturerPerTimeslot(self):
        """
        A lecturer cannot be scheduled for two modules at the same time
        """
        for d in self.all_days:
            for t in self.all_timeslots:
                for l in self.all_lecturers:
                    combo = []
                    for m in self.all_modules:
                        for s in self.all_semesters:
                            if (s, d, t, m, l) in self.bools.keys():
                                combo.append(self.bools[(s, d, t, m, l)])
                    self.model.AddAtMostOne(combo)