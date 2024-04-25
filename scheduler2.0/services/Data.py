import pandas as pd
import numpy as np
from utils import calc_blocksizes


class Data:
    def __init__(self):
        self.lecturers = pd.read_csv("db/lecturers.csv",
                                     dtype={"monday": str, "tuesday": str, "wednesday": str, "thursday": str,
                                            "friday": str})
        self.modules = pd.read_csv("db/modules.csv")
        self.semesters = self.modules["semester"].unique()
        self.days = np.array(["monday", "tuesday", "wednesday", "thursday", "friday"])
        self.timeslots = self.lecturers["monday"].iloc[0]
        self.blocks = {"block_id": [], "module_id": [], "blocksize": []}

        counter = 0
        for module in self.modules.iloc:
            for blocksize in calc_blocksizes(module["sws"]):
                self.blocks["block_id"].append(counter)
                self.blocks["module_id"].append(module["module_id"])
                self.blocks["blocksize"].append(blocksize)
                counter += 1
        self.blocks = pd.DataFrame(self.blocks)
        # print(self.blocks)