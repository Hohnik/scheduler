import pandas as pd
from ortools.sat.python import cp_model


class db:
    modules: list[dict] = pd.read_csv("db/modules").to_dict(orient="records")
    lecturers: list[dict] = pd.read_csv("db/lecturers").to_dict(orient="records")

    def __init__(self) -> None:
        pass

    @classmethod
    def get_lecturers_count(cls):
        return len(cls.lecturers)

    @classmethod
    def get_modules_count(cls):
        return len(cls.modules)


def main():
    # DATA
    num_modules = db.get_modules_count()
    num_lecturers = db.get_lecturers_count()
    num_slots = 10
    num_days = 5

    modules = [
        lecture["lecture_id"] for lecture in db.modules
    ]  # ["KI210", "KI220", ...]
    lecturers = [
        lecturer["lecturer_id"] for lecturer in db.lecturers
    ]  # ["L01", "L02", ...]
    working_days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    # levels = ["1-", "2-", "3-"]
    # sections = ["A"]
    # lecturers = ["Mario", "Elvis", "Donald", "Ian"]
    # lecturers_work_hours = [18, 12, 12, 18]

    periods = ["08:00-09:30", "09:45-11:15", "11:30-13:00"]
    # curriculum = {
    #     ("1-", "English"): 3,
    #     ("2-", "English"): 4,
    #     ("2-", "Math"): 2,
    #     ("3-", "History"): 2,
    # }

    # Subject -> List of lecturers who can teach it
    specialties_idx_inverse = [
        [1, 3],  # English   -> Elvis & Ian
        [0, 3],  # Math      -> Mario & Ian
        [2, 3],  # History   -> Donald & Ian
    ]

    problem = SchoolSchedulingProblem(
        modules,
        lecturers,
        curriculum,
        specialties_idx_inverse,
        working_days,
        periods,
        levels,
        sections,
        lecturers_work_hours,
    )
    solver = SchoolSchedulingSatSolver(problem)
    solver.solve()
    solver.print_status()


class SchoolSchedulingProblem(object):

    def __init__(
        self,
        lectures,
        lecturers,
        curriculum,
        specialties,
        working_days,
        periods,
        levels,
        sections,
        lecturer_work_hours,
    ):
        self.lectures = lectures
        self.lecturers = lecturers
        self.curriculum = curriculum
        self.specialties = specialties
        self.working_days = working_days
        self.periods = periods
        self.levels = levels
        self.sections = sections
        self.lecturer_work_hours = lecturer_work_hours


class SchoolSchedulingSatSolver(object):

    def __init__(self, problem:SchoolSchedulingProblem):
        # Problem
        self.problem = problem

        # Utilities
        self.timeslots = [
            "{0:10} {1:6}".format(x, y)
            for x in problem.working_days
            for y in problem.periods
        ]
        self.num_days = len(problem.working_days)
        self.num_periods = len(problem.periods)
        self.num_slots = len(self.timeslots)
        self.num_lecturers = len(problem.lecturers)
        self.num_lectures = len(problem.lectures)
        self.num_levels = len(problem.levels)
        self.num_sections = len(problem.sections)
        self.courses = [
            x * self.num_levels + y for x in problem.levels for y in problem.sections
        ]
        self.num_courses = self.num_levels * self.num_sections

        all_courses = range(self.num_courses)
        all_lecturers = range(self.num_lecturers)
        all_slots = range(self.num_slots)
        all_sections = range(self.num_sections)
        all_lectures = range(self.num_lectures)
        all_levels = range(self.num_levels)

        self.model = cp_model.CpModel()

        self.assignment = {}
        for c in all_courses:
            for s in all_lectures:
                for t in all_lecturers:
                    for slot in all_slots:
                        if t in self.problem.specialties[s]:
                            name = "C:{%i} S:{%i} T:{%i} Slot:{%i}" % (c, s, t, slot)
                            self.assignment[c, s, t, slot] = self.model.NewBoolVar(name)
                        else:
                            name = "NO DISP C:{%i} S:{%i} T:{%i} Slot:{%i}" % (
                                c,
                                s,
                                t,
                                slot,
                            )
                            self.assignment[c, s, t, slot] = self.model.NewIntVar(
                                0, 0, name
                            )

        # Constraints

        # Each course must have the quantity of classes specified in the curriculum
        for level in all_levels:
            for section in all_sections:
                course = level * self.num_sections + section
                for lecture in all_lectures:
                    required_slots = self.problem.curriculum[
                        self.problem.levels[level], self.problem.lectures[lecture]
                    ]
                    self.model.Add(
                        sum(
                            self.assignment[course, lecture, lecturer, slot]
                            for slot in all_slots
                            for lecturer in all_lecturers
                        )
                        == required_slots
                    )

        # Teacher can do at most one class at a time
        for lecturer in all_lecturers:
            for slot in all_slots:
                self.model.Add(
                    sum(
                        [
                            self.assignment[c, s, lecturer, slot]
                            for c in all_courses
                            for s in all_lectures
                        ]
                    )
                    <= 1
                )

        # Maximum work hours for each lecturer
        for lecturer in all_lecturers:
            self.model.Add(
                sum(
                    [
                        self.assignment[c, s, lecturer, slot]
                        for c in all_courses
                        for s in all_lectures
                        for slot in all_slots
                    ]
                )
                <= self.problem.lecturer_work_hours[lecturer]
            )

        # Teacher makes all the classes of a lecture's course
        lecturer_courses = {}
        for level in all_levels:
            for section in all_sections:
                course = level * self.num_sections + section
                for lecture in all_lectures:
                    for t in all_lecturers:
                        name = "C:{%i} S:{%i} T:{%i}" % (course, lecture, lecturer)
                        lecturer_courses[course, lecture, t] = self.model.NewBoolVar(
                            name
                        )
                        temp_array = [
                            self.assignment[course, lecture, t, slot]
                            for slot in all_slots
                        ]
                        self.model.AddMaxEquality(
                            lecturer_courses[course, lecture, t], temp_array
                        )
                    self.model.Add(
                        sum(lecturer_courses[course, lecture, t] for t in all_lecturers)
                        == 1
                    )

        # Solution collector
        self.collector = None

    def solve(self):
        print("Solving")
        solver = cp_model.CpSolver()
        solution_printer = SchoolSchedulingSatSolutionPrinter()
        status = solver.SearchForAllSolutions(self.model, solution_printer)
        print()
        print("Branches", solver.NumBranches())
        print("Conflicts", solver.NumConflicts())
        print("WallTime", solver.WallTime())

    def print_status(self):
        pass


class SchoolSchedulingSatSolutionPrinter(cp_model.CpSolverSolutionCallback):

    def NewSolution(self):
        print("Found Solution!")


if __name__ == "__main__":
    main()
