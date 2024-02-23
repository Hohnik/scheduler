from ortools.sat.python import cp_model


def main():
    SearchForAllSolutionsSampleSat()

def SearchForAllSolutionsSampleSat():
    """Showcases calling the solver to search for all solutions."""
    # Creates the model.
    model = cp_model.CpModel()

    # Creates the variables.
    num_vals = 3
    x = model.NewIntVar(0, num_vals - 1, "x")
    y = model.NewIntVar(0, num_vals - 1, "y")
    z = model.NewIntVar(0, num_vals - 1, "z")

    # Create the constraints.
    model.Add(x != y)

    # Create a solver and solve.
    solver = cp_model.CpSolver()
    solution_printer = VarArraySolutionPrinter([x, y, z])
    # Enumerate all solutions.
    solver.parameters.enumerate_all_solutions = True
    # Solve.
    status = solver.Solve(model, solution_printer)

    print(f"Status = {solver.StatusName(status)}")
    print(f"Number of solutions found: {solution_printer.solution_count()}")

if __name__ == "__main__":
    main()
