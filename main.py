# by Niklas Hohn & Julien Sauter

# course = KI(unknown), etc.
# module = KI210l(dic), etc.
# lecturer = L01(dic), etc.
# room = G005(dic), etc.
# semester = 1, etc.
# day = monday, etc.
# lecturer[day] = 1010111010, etc.

import pprint
import pandas as pd
from ortools.sat.python import cp_model

import utils.generate_lecturers_data as gld
import utils.generate_modules_data as gmd
from utils.table_printer import TablePrinter

#INFO: all for loops above contraint are consumed, and all for loops in constraint are chosen/reused


#TODO[ ] IMPORTANT: fix solution object: see table_printer.py for example object
#TODO[ ] IMPORTANT: time_slots are currently treated as 60 minute windows, even though they are 45 min. This drastically changes how we have to check if sws per module are being taught. >= won't be enough because we don't want to overbook modules.



#TODO[x] remove sws_pu and participants_lu from modules.csv file and create new modules instead
#TODO[ ] tidy up code, create classes and methods, OOP
#TODO[ ] for performance try to merge contraints into one for loop struct (save previous for loop values)
#TODO[ ] if necessary, add gender, etc. to lecturers for german spelling and other information
#TODO[ ] implement print function (or equivalent/analogous output) in different languages
#TODO[ ] MAYBE: Let courses define more accurately what they need in a room, instead of just lecture vs practice

#HEURISTIC[ ]: for each module, Optimise: same room (same room -OR- constraint modules are always same room)
#HEURISTIC[ ]: for each lecturer, Optimise: less days -OR- shorter periods -OR- more breaks
#HEURISTIC[ ]: for each semester for each day, Optimise: same room for as long as possible
#HEURISTIC[ ]: for each semester for each day, Optimise: lower walking distance (add Mensa as room for break time) (same building -OR- room_coordinates with manhattan/euclidean distance -OR- constraint courses have specific buildings)
#HEURISTIC[ ]: for each module for each room, Optimise: just over half full rooms (normal distribution, slightly right-skewed)

def run_model():
    
    # Read in data file
    lecturers_df = pd.read_csv("db/lecturers.csv", dtype=str)
    modules_df = pd.read_csv("db/modules.csv", dtype=str)
    rooms_df = pd.read_csv("db/rooms.csv", dtype=str)

    # Pandas data frame to dictionary
    lecturers_data = lecturers_df.to_dict(orient="records")
    modules_data = modules_df.to_dict(orient="records")
    rooms_data = rooms_df.to_dict(orient="records")

    # Better names
    lecturers = lecturers_data
    modules = modules_data
    rooms = rooms_data
    
    # Generate praktika
    for module_p in modules:
        if module_p["module_id"][0] == "p":
            for module_l in modules:
                if module_l["module_id"][0] == "l" and module_p["module_id"][1:] == module_l["module_id"][1:]:
                    numof_prak = (int(module_l["participants"]) // 20) + 1
                    remaining_participants = int(module_l["participants"])
                    for num in range(numof_prak):
                        module_p_copy = module_p.copy()
                        module_p_copy["module_id"] = module_p_copy["module_id"] + '_' + str(num+1)
                        
                        participants = remaining_participants // numof_prak
                        module_p_copy["participants"] = str(participants)
                        remaining_participants -= participants
                        numof_prak -= 1
                        modules.append(module_p_copy)
                    
                    modules.remove(module_p)
    
    # Create id dictionary
    lecturer_ids = [lecturer["lecturer_id"] for lecturer in lecturers]
    module_ids = [module["module_id"] for module in modules]
    room_ids = [room["room_id"] for room in rooms]
    
    # Create other data sources
    semesters = list(set([module["semester"] for module in modules]))
    semesters.sort()
    days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    time_slots = range(len(lecturers[0][days[0]]))
    #print(len(lecturers[0][days[0]]))
    
    time_slot_times = ["8:45-9:30","9:30-10:15","10:30-11:15","11:15-12:00","12:50-13:35","13:35-14:20","14:30-15:15","15:15-16:00","16:10-16:55","16:55-17:40","17:50-18:35","18:35-19:20","19:30-20:15","20:15-21:00"]

    # Link ids to int values
    lecturer_ids_dic = {lecturer_id: num for num, lecturer_id in enumerate(lecturer_ids)}
    module_ids_dic = {module_id: num for num, module_id in enumerate(module_ids)}
    room_ids_dic = {room_id: num for num, room_id in enumerate(room_ids)}
    semesters_dic = {semester: num for num, semester in enumerate(semesters)}
    days_dic = {day: num for num, day in enumerate(days)}
    days_uniform_dic = {day: day[:3] for day in days}
    time_slot_times_dic = {time_slot_time:time_slot for time_slot, time_slot_time in zip(time_slots, time_slot_times) if time_slot < len(time_slots)}
    
    # Add course to module dictionary
    for module in modules:
        module["course"] = module["module_id"][1:3]
    
    

    # Create model
    model = cp_model.CpModel()
    timetable = {}
    for lecturer in lecturers:
        for module in modules:
            for semester in semesters:
                for day in days:
                    for time_slot in time_slots:
                        for room in rooms:
                            timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]])] = model.NewBoolVar(
                                f'{lecturer["lecturer_id"]}_{module["module_id"]}_{semester}_{day}_{time_slot}'
                            )

    print(len(timetable))

    # Define the constraints
    for lecturer in lecturers:
        for module in modules:
            for semester in semesters:
                for day in days:
                    for time_slot, bit in enumerate(lecturer[day]):
                        for room in rooms:
                            
                            # Implied for every lecturer for every time_slot that time_slot bit == "1" | lecturers only give lectures when they are free (bit == "1")
                            model.AddImplication(timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]])],
                                bit == "1"
                                )

                            # Implied for every module that lecturer["lecturer_id"] in module["lecturer_id"] | modules can only be taught by their corresponding lecturer
                            model.AddImplication(timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]])],
                                lecturer["lecturer_id"] in module["lecturer_id"]
                                )
                        
                            # Implied for every module that semester == module["semester"] | modules linked to respective semesters
                            model.AddImplication(timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]])],
                                semester == module["semester"]
                                )

                            # Implied for every room that room["capacity"] >= module["participants"] | room has enough space for the module
                            model.AddImplication(timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]])],
                                room["capacity"] >= module["participants"]
                                )

                            # Implied for every room that module["module_id"][0] == room["room_type"] | room type fits to module type
                            model.AddImplication(timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]])],
                                module["module_id"][0] == room["room_type"]
                                )

    # | All modules should be in blocks of consecutive time_slots if possible (if leftover_sws == 3: 3, elif leftover_sws == 1: 1 else: leftover_sws -= 2: 2)    
    def calculate_session_blocks(leftover_sws:str):
        #return [1]
        session_blocks = []
        leftover_sws = int(leftover_sws)
        while leftover_sws > 0:
            if leftover_sws % 2 == 0:
                leftover_sws -= 2
                session_blocks.append(2)
            elif leftover_sws >= 3:
                leftover_sws -= 3
                session_blocks.append(3)
            elif leftover_sws == 1:
                leftover_sws -= 1
                session_blocks.append(1)
        
        return session_blocks

    # 5  = [3+2]          [[3+2][2+2+1][3+1+1][2+1+1+1][1+1+1+1+1]]
    # 10 = [2+2+2+2+2]

    for lecturer in lecturers:
        for module in modules:
            session_blocks = calculate_session_blocks(module["sws"])
            for block_size in session_blocks:
                for semester in semesters:
                    for day in days:
                        for time_slot in range(len(time_slots) - block_size + 1):  # Adjust based on block size
                            for room in rooms:
                                l = lecturer_ids_dic[lecturer["lecturer_id"]]
                                m = module_ids_dic[module["module_id"]]
                                s = semesters_dic[semester]
                                d = days_dic[day]
                                t = time_slot
                                r = room_ids_dic[room["room_id"]]

                                start_block = timetable[((l, m, s, d, t, r))]
                                #test = [1, 1]
                                #lst = [timetable[(l, m, s, d, t+offset, r )] for offset in range(block_size)]
                                if block_size == 2:
                                    model.AddBoolAnd(start_block, timetable[(l, m, s, d, t+1, r )])
                                elif block_size == 3:
                                    model.AddBoolAnd(start_block, timetable[(l, m, s, d, t+1, r )], timetable[(l, m, s, d, t+2, r )])

    def test():
        return model.AddImplication(test)

    # At most one room per module per time_slot | two modules cannot be scheduled in the same room at the same time
    for day in days:
        for time_slot in time_slots:
            for room in rooms:
                model.AddAtMostOne(timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]])]
                for lecturer in lecturers
                for module in modules
                for semester in semesters
                )

    # At most one module per lecturer per time_slot | a lecturer cannot be scheduled for two modules at the same time
    for lecturer in lecturers:
        for day in days:
            for time_slot in time_slots:
                model.AddAtMostOne(timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]])]
                for module in modules
                for semester in semesters
                for room in rooms
                )

    # At most one module per semester per time_slot | two modules in the same semester cannot be scheduled at the same time
    for semester in semesters:
        for day in days:
            for time_slot in time_slots:
                model.AddAtMostOne(timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]])]
                for lecturer in lecturers
                for module in modules
                for room in rooms
                )
    
    # Sum( time_slots for module ) == module["sws"] | All sws have to be scheduled
    for module in modules:
        model.Add(cp_model.LinearExpr.Sum([timetable[(lecturer_ids_dic[lecturer["lecturer_id"]], module_ids_dic[module["module_id"]], semesters_dic[semester], days_dic[day], time_slot, room_ids_dic[room["room_id"]])]
            for lecturer in lecturers
            for semester in semesters
            for day in days
            for time_slot in time_slots
            for room in rooms
        ]) == int(module["sws"]))



    # Solve the model
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    print( f'Status:{solver.StatusName()}',f'Bools:{solver.NumBooleans()}', f'Branches:{solver.NumBranches()}', f'Conflicts:{solver.NumConflicts()}', sep='\n', end='\n\n')
    solution = {}
    # Retrieve the solution
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        
        # Create available_rooms_dic to check how many rooms are free for each time_slot
        available_rooms_dic = {(day, time_slot): [room_id for room_id in room_ids]
                               for day in days
                               for time_slot in time_slots
                               }
        
        for semester in semesters:
            print()
            solution.update({semester:{}})
            print(f'Semester {semester}:')
            for day in days:
                print(f'{day}:')
                solution[semester].update({day:{}})
                for time_slot in time_slots:
                    solution[semester][day].update({time_slot:{}}) # @niklas Why not another dictionary with keys as id's from the variables from the for loops below and values as the variable itself (timeslot:{lecturer_id: lecturer, module_id: module, room_id: room})?
                    for lecturer in lecturers:
                        for module in modules:
                            for room in rooms:
                                
                                if solver.Value(timetable[(
                                        lecturer_ids_dic[lecturer["lecturer_id"]], 
                                        module_ids_dic[module["module_id"]],
                                        semesters_dic[semester], 
                                        days_dic[day], 
                                        time_slot, 
                                        room_ids_dic[room["room_id"]])]):
                                    
                                    module_id_nicer = module["module_id"][1:] + module["module_id"][0]
                                    
                                    available_rooms_dic[(day, time_slot)].remove(room["room_id"])
                                    solution[semester][day][time_slot].update({
                                        "lecturer": lecturer,
                                        "module": module,
                                        "room": room
                                        })
                                    
                                    
                                    print(
                                        f'{time_slot} {module_id_nicer:7} {room["room_id"]} ({module["module_id"][0]}={room["room_type"]}) ({module["participants"]}/{room["capacity"]}) {lecturer["lecturer_name"]}'
                                        #f'At time slot {time_slot} {module_id_nicer} is being taught in room {room["room_id"]} ({module["module_id"][0]}={room["room_type"]}) ({module["participants"]}/{room["capacity"]}) by Lecturer {lecturer["lecturer_name"]}'
                                        #f'An Zeitpunkt {time_slot} wird {module_id_nicer} unterrichtet in Raum {room["room_id"]} ({module["participants"]}/{room["capacity"]}) von Professor {lecturer["lecturer_name"]}'
                                    )
                    
        print(numof_available_rooms(available_rooms_dic, days, time_slots))
        
        # print([(module["module_id"], module["participants"]) for module in modules])
        for semester in semesters:
            for day in days:
                solution[semester][days_uniform_dic[day]] = solution[semester][day]
        for semester in semesters:
            for day in days:
                del solution[semester][day]

        #pprint.pprint(solution)
        return solution
    else:
        print(solver.SolutionInfo())
        print("No feasible solution found.")
        gld.generate_data()
        gmd.create_data()
        run_model()


# number of available rooms per time_slot
def numof_available_rooms(available_rooms_dic, days, time_slots):
    numof_available_rooms_lst = [len(available_rooms_dic[(day, time_slot)]) for day in days for time_slot in time_slots]
    n_a_r_l_dic = {}
    for elem in numof_available_rooms_lst:
        if elem in n_a_r_l_dic:
            n_a_r_l_dic[elem] += 1
        else:
            n_a_r_l_dic[elem] = 1
    return n_a_r_l_dic


gld.generate_data()
gmd.create_data()
result_object = run_model()
# pprint.pprint(result_object)
printer = TablePrinter(result_object)
printer.print_tables()