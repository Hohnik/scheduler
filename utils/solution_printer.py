from ortools.sat.python import cp_model

class SolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

    def __init__(self, variables):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.__variables = variables
        self.__solution_count = 0

    def on_solution_callback(self):
        counter = 0
        self.__solution_count += 1

        open("solution.txt", "w").close()
        with open("solution.txt", "a") as f:
            for v in self.__variables:
                counter += 1
                if self.Value(v) == 1:
                    f.write(f"{v}={self.Value(v)}\n")

            f.write("\n")
            print(counter)

    def solution_count(self):
        return self.__solution_count
