import pandas as pd
from ortools.sat.python import cp_model

# Read the lecturer data from the CSV file using Pandas
lecturers_df = pd.read_csv("db/lecturers.csv", dtype=str)

# Read the module data from the CSV file using Pandas
modules_df = pd.read_csv("db/modules.csv", dtype=str)


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
        for time_slot, bit in enumerate(lecturer[day]):
            if bit == "1":
                timetable[(lecturer["lecturer_id"], day, time_slot)] = model.NewBoolVar(
                    f"{lecturer['lecturer_id']}_{day}_{time_slot}"
                )

# Define the constraints
# Lecturers cannot be scheduled for two modules at the same time
# for lecturer in lecturers_data:
#     for day in days:
#         for time_slot, bit in enumerate(lecturer[day]):
#             if bit == "1":
#                 overlapping_modules = [
#                     timetable[(module["lecturer_id"], day, time_slot)]
#                     for module in modules_data
#                     if module["lecturer_id"] == lecturer["lecturer_id"]
#                 ]
#                 model.AddImplication(
#                     timetable[(lecturer["lecturer_id"], day, time_slot)],
#                     len(overlapping_modules) <= 1,
#                 )

# Modules that are in the same semester cannot be at the same time
# for day in days:
#    for module1 in modules_data:
#        for module2 in modules_data:
#            if (
#                module1["semester"] == module2["semester"]
#                and module1["module_id"] != module2["module_id"]
#            ):
#                for lecturer1 in lecturers_data:
#                    for lecturer2 in lecturers_data:
#                        if (lecturer1["lecturer_id"] == module1["lecturer_id"] and
#                            lecturer2["lecturer_id"] == module2["lecturer_id"] and
#                            lecturer1["lecturer_id"] != lecturer2["lecturer_id"] ):
#                                for time_slot1, bit1 in enumerate(lecturer1[day]):
#                                    for time_slot2, bit2 in enumerate(lecturer2[day]):
#                                        # print(f"{lecturer1['lecturer_id']}:{bit1}:{time_slot1} , {lecturer2['lecturer_id']}:{bit2}:{time_slot2}")
#                                        if bit1 == "1" and bit2 == "1":
#                                            model.Add(
#                                                timetable[(module1["lecturer_id"], day, time_slot1)] +
#                                                timetable[(module2["lecturer_id"], day, time_slot2)] <= 1,
#                                            )

# Solve the model
solver = cp_model.CpSolver()
status = solver.Solve(model)
print(solver.StatusName())
print(solver.NumBooleans(), solver.NumBranches(), solver.NumConflicts())
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
                for time_slot, bit in enumerate(lecturer[day]):
                    if bit == "1":
                        if solver.Value(
                            timetable[(module["lecturer_id"], day, time_slot)]
                        ):
                            print(
                                f"Lecturer {lecturer['lecturer_name']} is teaching {module['module_name']} on {day} at time slot {time_slot}"
                            )
else:
    print("No feasible solution found.")
