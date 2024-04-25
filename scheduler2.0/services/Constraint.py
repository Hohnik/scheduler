from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import CpModel, CpSolver, IntVar, LinearExpr, BoolVar

from services.Data import Data
from utils import calc_blocksizes


class Constraint:
    def __init__(self, bools:dict[tuple, IntVar], model:CpModel, data:Data):
        self.bools = bools
        self.model = model
        self.data = data

        self.all_semesters = range(len(data.semesters))
        self.all_days = range(len(data.days))
        self.all_timeslots = range(len(data.timeslots))
        self.all_lecturers = range(len(data.lecturers))
        self.all_modules = range(len(data.modules))

    def one_module_per_timeslot(self):
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
                    
    def correct_sws(self):
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

    def one_module_per_lecturer_per_timeslot(self):
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

    def consecutive_timeslots(self):
        """
        # TODO: implement constraint_consecutive_timeslots
        # Wenn 2er-block: stunde vorher nicht mahte --impliziert--> nächste und übernächste stunde ist mathe
        # Hier muss noch gecheckt werden ob wir in einen overflow laufen würden
        """
        for d in self.all_days:
            for t in self.all_timeslots:
                for l in self.all_lecturers:
                    for m in self.all_modules:
                        for s in self.all_semesters:
                            blocks = self.calc_blocksizes(int(self.data.modules["sws"][m]))
                            for b in blocks:
                                if b == 2:
                                    if t <= 7 and (s, d, t, m, l) in self.bools.keys():
                                        self.model.AddImplication(self.bools[(s, d, t, m, l)].Not(), self.bools[(s, d, t+1, m, l)])

    def calc_blocksizes(self, sws: int, blocks=[]) -> list:
        """
        Calculate the best possible combination of blocks.
        """
        if not sws:
            return blocks

        if sws % 2 == 0:
            return self.calc_blocksizes(sws-2, blocks + [2])

        if sws >= 3:
            return self.calc_blocksizes(sws-3, blocks + [3])

        if sws == 1:
            return self.calc_blocksizes(sws-1, blocks + [1])