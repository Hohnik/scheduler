import pandas as pd
from ortools.sat.python import cp_model

# Read the lecturer data from the CSV file using Pandas
lecturers_df = pd.read_csv("db/lecturers.csv")

# Read the module data from the CSV file using Pandas
modules_df = pd.read_csv("db/modules.csv")

# Convert the Pandas DataFrames to Python data structures
lecturers_data = lecturers_df.to_dict(orient="records")
modules_data = modules_df.to_dict(orient="records")
days = ["monday", "tuesday", "wednesday", "thursday", "friday"]

# Create the model
model = cp_model.CpModel()

# Create the timetable variables
timetable = {}
for lecturer in lecturers_data:
    for day in days:
        for time_slot, bitmask in enumerate(lecturer[day]):
            if bitmask == "1":
                timetable[(lecturer["lecturer_id"], day, time_slot)] = model.NewBoolVar(
                    f"{lecturer['lecturer_id']}_{day}_{time_slot}"
                )


## Define the constraints
## Each lecturer can only hold one module at a time
#for time_slot in range(10):
#    for day in days:
#        model.Add(
#            sum(
#                timetable[(lecturer["lecturer_id"], day, time_slot)]
#                for lecturer in lecturers_data
#            )
#            <= 1
#        )
#
#
#
## Define the constraints
## Lecturers cannot be scheduled for two modules at the same time
#for day in days:
#    for time_slot in range(10):
#        for lecturer in lecturers_data:
#            model.Add(timetable[(lecturer['lecturer_id'], day, time_slot)] <= 1)

# Define the constraints
# Lecturers cannot be scheduled for overlapping modules
for lecturer in lecturers_data:
    for day in days:
        for time_slot, bitmask in enumerate(lecturer[day]):
            if bitmask == '1':
                overlapping_modules = [
                    timetable[(other_lecturer['lecturer_id'], day, time_slot)]
                    for other_lecturer in lecturers_data
                    if other_lecturer['lecturer_id'] != lecturer['lecturer_id']
                ]
                model.AddImplication(
                    timetable[(lecturer['lecturer_id'], day, time_slot)],
                    sum(overlapping_modules) == 0
                )

# Modules that are in the same semester cannot be at the same time
for module1 in modules_data:
    for module2 in modules_data:
        if (
            module1["semester"] == module2["semester"]
            and module1["module_id"] != module2["module_id"]
        ):
            for day in days:
                for time_slot in range(10):
                    model.AddImplication(
                        timetable[(module1["lecturer_id"], day, time_slot)],
                        sum(
                            timetable[(module2["lecturer_id"], day, time_slot)]
                            for day in days
                        )
                        == 0,
                    )

# Lecturers can only do modules if they have a 1 in the specific timeslot of the weekday
for module in modules_data:
    lecturer = next(
        (
            lecturer
            for lecturer in lecturers_data
            if lecturer["lecturer_id"] == module["lecturer_id"]
        ),
        None,
    )
    if lecturer:
        for day in days:
            for time_slot, bitmask in enumerate(lecturer[day]):
                if bitmask == "0":
                    model.Add(timetable[(module["lecturer_id"], day, time_slot)] == 0)

# Solve the model
solver = cp_model.CpSolver()
status = solver.Solve(model)

# Retrieve the solution
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    for module in modules_data:
        lecturer = next(
            (
                lecturer
                for lecturer in lecturers_data
                if lecturer["lecturer_id"] == module["lecturer_id"]
            ),
            None,
        )
        if lecturer:
            for day in days:
                for time_slot, bitmask in enumerate(lecturer[day]):
                    if bitmask == "1" and solver.Value(
                        timetable[(module["lecturer_id"], day, time_slot)]
                    ):
                        print(
                            f"Lecturer {lecturer['lecturer_name']} is teaching {module['module_name']} on {day} at time slot {time_slot}"
                        )
else:
    print("No feasible solution found.")
