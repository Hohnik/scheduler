import pprint
from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import IntVar

from utils.util2 import *
from utils.BoolVarGenerator import *
from Solver import Solver
from utils.table_printer import TablePrinter


def main():
    solution = run_model()

    pprint.pprint(solution)

    if solution:
        print("Printing solution as Timetable...")
        printer = TablePrinter()
        printer.set_solution(solution)
        # pprint.pprint(result_object)
        printer.print_semester_tables()

def run_model():

    model = cp_model.CpModel()
    
    SolverObj = Solver(model)
    SolverObj.addConstraints()
    SolverObj.solve()
    
    solution = SolverObj.retrieve_solution()
    
    return solution
    
if __name__ == "__main__":
    main()