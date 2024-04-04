import pprint
from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import IntVar

from utils.util2 import *
from utils.BoolVarGenerator import *
from Solver import Solver
from utils.table_printer import TablePrinter


def main():
    solution = run_model()

    # pprint.pprint(solution)

    # pprint.pprint(solution)
    return
    if solution:
        print("Printing solution as Timetable...")
        printer = TablePrinter()
        printer.set_solution(solution)
        # pprint.pprint(result_object)
        printer.print_semester_tables()

def run_model():
    
    SolverObj = Solver()
    SolverObj.addVariables()
    SolverObj.addConstraints()
    SolverObj.solve()
    
    pprint.pprint(SolverObj.model.ModelStats())
    print(SolverObj.model.__dict__)
    print()
    
    print(
        f"Status:{SolverObj.CPsolver.StatusName()}",
        f"Bools:{SolverObj.CPsolver.NumBooleans()}",
        f"Branches:{SolverObj.CPsolver.NumBranches()}",
        f"Conflicts:{SolverObj.CPsolver.NumConflicts()}",
        sep="\n",
    )
    
    return
    
    solution = SolverObj.retrieve_solution()
    
    return solution
    
if __name__ == "__main__":
    main()