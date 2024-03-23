def generate_hasTime(model, data, data_idx):
    hasTime = {}
    for lecturer in data["lecturers"]:
        for day in data["days"]:
            for time_slot in data["time_slots"]:
                hasTime[(
                    data_idx["lecturers"][lecturer["lecturer_id"]],
                    data_idx["days"][day],
                    time_slot
                )] = model.NewBoolVar(
                    f'{lecturer["lecturer_id"]}, {day}, {time_slot})'
                )
    return hasTime

def generate_correctLecturer(model, data, data_idx):
    correctLecturer = {}
    for lecturer in data["lecturers"]:
        for module in data["modules"]:
            correctLecturer[(
                data_idx["lecturers"][lecturer["lecturer_id"]],
                data_idx["modules"][module["module_id"]]
            )] = model.NewBoolVar(
                f'{lecturer["lecturer_id"]}, {module["module_id"]})'
            )
    return correctLecturer

def generate_correctSemester(model, data, data_idx):
    correctSemester = {}
    for module in data["modules"]:
        for semester in data["semesters"]:
            correctSemester[(
                data_idx["modules"][module["modules_id"]],
                data_idx["semesters"][semester]
            )] = model.NewBoolVar(
                f'{module["modules_id"]}, {semester})'
            )
    return correctSemester