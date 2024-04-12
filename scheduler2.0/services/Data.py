import pandas as pd
import numpy as np
class Data(): 
    def __init__(self):
        lecturers_df = pd.read_csv("db/lecturers.csv", dtype={"monday": str, "tuesday": str, "wednesday": str, "thursday": str, "friday": str})
        modules_df = pd.read_csv("db/modules.csv")

        self.semesters = modules_df["semester"].unique()
        self.days = np.array(["monday", "tuesday", "wednesday", "thursday", "friday"])
        self.timeslots = lecturers_df["monday"].iloc[0]
        self.lecturers = lecturers_df
        self.modules = modules_df

        # print("semesters: ", self.semesters)
        # print("days: ", self.days)
        # print("timesots: ", self.timeslots)
        # print("lecurers: ", self.lecturers, sep="\n")
        # print("modules: ", self.modules, sep="\n")

    def calculate_session_blocks(self, sws:str) -> dict[tuple[int, int], int]:
        block_sizes_dic = {}
        num = 0
        key_1 = 0
        key_2 = 0
        key_3 = 0
        leftover_sws = int(sws)
        while leftover_sws > 0:
            if leftover_sws % 2 == 0:
                block_sizes_dic[(2, key_2)] = num
                num += 1
                key_2 += 1
                leftover_sws -= 2
            elif leftover_sws >= 3:
                block_sizes_dic[(3, key_3)] = num
                num += 1
                key_3 += 1
                leftover_sws -= 3
            elif leftover_sws == 1:
                block_sizes_dic[(1, key_1)] = num
                num += 1
                key_1 += 1
                leftover_sws -= 1

        return block_sizes_dic

if __name__ == "__main__":
    data = Data()
