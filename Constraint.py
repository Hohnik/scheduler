class Constraint():

    def __init__(self, model, data):
        self.model = model
        self.data = data
        
    def constraintHasTime(self):
        """
        Implied for every lecturer for every time_slot that time_slot bit == "1" | lecturers only give lectures when they are free (bit == "1")
        """
        self.hasTime = self.BoolVarGenObj.generateHasTime()
        for lecturer in self.data.lecturers:
            for day in self.data.days:
                for time_slot, bit in enumerate(lecturer[day]):
                    self.model.AddImplication(self.hasTime[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.days_idx[day], time_slot)],
                        bit == "1"
                        )
    
    def constraintCorrectLecturer(self):
        """
        Implied for every module that lecturer["lecturer_id"] in module["lecturer_id"] | modules can only be taught by their corresponding lecturer
        """
        self.correctLecturer = self.BoolVarGenObj.generateCorrectLecturer()
        for lecturer in self.data.lecturers:
            for module in self.data.modules:
                self.model.AddImplication(self.correctLecturer[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.modules_idx[module["module_id"]])],
                    lecturer["lecturer_id"] in module["lecturer_id"]
                    )
    
    def constraintCorrectSemester(self):
        """
        Implied for every module that semester == module["semester"] | modules linked to respective semesters
        """
        self.correctSemester = self.BoolVarGenObj.generateCorrectSemester()
        for module in self.data.modules:
            for semester in self.data.semesters:
                self.model.AddImplication(self.correctSemester[(self.data.modules_idx[module["module_id"]], self.data.semesters_idx[semester])],
                    semester == module["semester"]
                    )

    def constraintfittingRoom(self):
        """
        Implied for every room that room["capacity"] >= module["participants"] | room has enough space for the module
        """
        self.fittingRoom = self.BoolVarGenObj.generateFittingRoom()
        for module in self.data.modules:
            for room in self.data.rooms:
                self.model.AddImplication(self.fittingRoom[(self.data.modules_idx[module["module_id"]], self.data.rooms_idx[room["room_id"]])],
                    room["capacity"] >= module["participants"]
                    )
                self.model.AddImplication(self.fittingRoom[(self.data.modules_idx[module["module_id"]], self.data.rooms_idx[room["room_id"]])],
                    module["module_id"][0] == room["room_type"]
                )

    def constraintOneModulePerRoom(self):
        """
        At most one room per module per time_slot | two modules cannot be scheduled in the same room at the same time
        """
        self.oneModulePerRoom = self.BoolVarGenObj.generateOneModulePerRoom()
        for day in self.data.days:
            for time_slot in self.data.time_slots:
                for room in self.data.rooms:
                    self.model.AddAtMostOne(self.oneModulePerRoom[(self.data.modules_idx[module["module_id"]], self.data.days_idx[day], time_slot, self.data.rooms_idx[room["room_id"]])]
                    for module in self.data.modules
                    )
                for module in self.data.modules:
                    self.model.AddAtMostOne(self.oneModulePerRoom[(self.data.modules_idx[module["module_id"]], self.data.days_idx[day], time_slot, self.data.rooms_idx[room["room_id"]])]
                    for room in self.data.rooms
                    )

    def constraintOneModulePerLecturer(self):
        """
        At most one module per lecturer per time_slot | a lecturer cannot be scheduled for two modules at the same time
        """
        self.oneModulePerLecturer = self.BoolVarGenObj.generateOneModulePerLecturer()
        for day in self.data.days:
            for time_slot in self.data.time_slots:
                for lecturer in self.data.lecturers:
                    self.model.AddAtMostOne(self.oneModulePerLecturer[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.modules_idx[module["module_id"]], self.data.days_idx[day], time_slot)]
                    for module in self.data.modules
                    )
                for module in self.data.modules:
                    self.model.AddAtMostOne(self.oneModulePerLecturer[(self.data.lecturers_idx[lecturer["lecturer_id"]], self.data.modules_idx[module["module_id"]], self.data.days_idx[day], time_slot)]
                    for lecturer in self.data.lecturers
                    )

    def constraintOneModulePerSemester(self):
        """
        At most one module per semester per time_slot | two modules in the same semester cannot be scheduled at the same time
        """
        self.oneModulePerSemester = self.BoolVarGenObj.generateOneModulePerSemester()
        for semester in self.data.semesters:
            for day in self.data.days:
                for time_slot in self.data.time_slots:
                    self.model.AddAtMostOne(self.oneModulePerSemester[(self.data.modules_idx[module["module_id"]], self.data.semesters_idx[module["semester"]], self.data.days_idx[day], time_slot)]
                    for module in self.data.modules
                    )

    def constraintCorrectSWS(self):