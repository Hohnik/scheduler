class Constraint():

    def __init__(self, model, data):
        self.model = model
        self.data = data

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
