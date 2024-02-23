from ortools.sat.python import cp_model


def main():
    num_lecturers = 10
    num_time_slots = 10

    all_lecturers = range(num_lecturers)
    all_slots = range(num_time_slots)

    model = cp_model.CpModel()
    shifts = {}
    for slot in all_slots:



if __name__ == "__main__":
    main()
