from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import CpModel, CpSolver, IntVar, LinearExpr

from services.Data import Data
from utils import calc_blocksizes


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

    def one_module_per_timeslot_per_semester(self):
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

    def module_is_placed_sws_times(self):
        """
        Modulecount equals sws
        """
        for m in self.all_modules:
            combo = []
            for l in self.all_lecturers:
                for s in self.all_semesters:
                    for d in self.all_days:
                        for t in self.all_timeslots:
                            if (s, d, t, m, l) in self.bools.keys():
                                combo.append(self.bools[(s, d, t, m, l)])
            self.model.Add(LinearExpr.Sum(combo) == self.data.modules["sws"][m])

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

    def one_module_block_per_day(self):
        """
        A module cant have more than one block per day
        """
        for m in self.all_modules:
            for d in self.all_days:
                for l in self.all_lecturers:
                    for blocksize in calc_blocksizes(self.data.modules["sws"][m]):
                        combo = []
                        for t in self.all_timeslots:
                            for s in self.all_semesters:
                                if (s, d, t, m, l) in self.bools.keys():
                                    combo.append(self.bools[(s,d,t,m,l)])
                        self.model.Add(LinearExpr.Sum(combo) <= blocksize)

    def blocks_are_consecutive(self):
        for d in self.all_days:
            for t in self.all_timeslots:
                for l in self.all_lecturers:
                    for m in self.all_modules:
                        for s in self.all_semesters:
                            if ((s, d, t, m, l) in self.bools.keys()
                                and (s, d, t+1, m, l) in self.bools.keys()):
                                self.model.AddImplication(self.bools[(s, d, t, m, l)], self.bools[(s, d, t+1, m, l)])
                            if ((s, d, t, m, l) in self.bools.keys()
                                and (s, d, t-1, m, l) in self.bools.keys()):
                                self.model.AddImplication(self.bools[(s, d, t, m, l)], self.bools[(s, d, t-1, m, l)])

    def consecutive_timeslots(self):
        """
        # TODO: implement constraint_consecutive_timeslots
        # Wenn 2er-block: stunde vorher nicht mathe --impliziert--> nächste und übernächste stunde ist mathe
        # Hier muss noch gecheckt werden ob wir in einen overflow laufen würden
        # oder
        # Die summe der nächsten zwei kurse muss der blockgröße entsprechen
        # oder
        # Die distanz von allen kursen in einem block muss so gering wie möglich sein
        """
        for d in self.all_days:
            for t in self.all_timeslots:
                for l in self.all_lecturers:
                    for m in self.all_modules:
                        for s in self.all_semesters:
                            if (s, d, t, m, l) in self.bools.keys():
