class Constraint:
    def __init__(self, bools, model, data):
        self.bools = bools
        self.model = model
        self.data = data

        self.all_semesters = range(len(data.semesters))
        self.all_days = range(len(data.days))
        self.all_timeslots = range(len(data.timeslots))
        self.all_lecturers = range(len(data.lecturers))
        self.all_modules = range(len(data.modules))

    def oneModulePerTimeslot(self):
        """
        Each slot is assigned to exactly one lecturer-module combo.
        """
        for s in self.all_semesters:
            for d in self.all_days:
                for t in self.all_timeslots:
                    combo = []
                    for m in self.all_modules:
                        for l in self.all_lecturers:
                            if (s, d, t, m, l) in self.bools.keys():
                                combo.append(self.bools[(s, d, t, m, l)])
                    self.model.AddAtMostOne(combo)