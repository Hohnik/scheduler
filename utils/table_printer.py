import pprint

def main():
    data = {
        "KI2": {
            "monday": {
                0: {
                    "lecturer": {"lecturer_id": "001", "lecturer_name": "Osendorfer"},
                    "module": {"module_id": "lKI210", "module_name": "Programmieren I"},
                    "room": {"room_id": "G005"},
                },
            },
        }
    }

    print("Here a little test table:")
    printer = TablePrinter(data)
    printer.print_semester_tables(end="The print_tables method can be used like a normal print")

class TablePrinter():
    days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    def __init__(self, solution: dict[str, dict[str, dict[int, list | str]]]) -> None:
        self.solution = solution
        # self.col_width = self.calc_dynamic_col_width(solution)
        self.col_width = 30
        self.line_top = "+"+"-"*(self.col_width//2)+"+"+(("-"*self.col_width)+"+")*(len(self.days)-1)+ ("-"*self.col_width)+"+\n"
        self.line_mid = "+"+"-"*(self.col_width//2)+"+"+(("-"*self.col_width)+"+")*(len(self.days)-1)+ ("-"*self.col_width)+"+\n"
        self.line_bot = "+"+"-"*(self.col_width//2)+"+"+(("-"*self.col_width)+"+")*(len(self.days)-1)+ ("-"*self.col_width)+"+\n"

    def print_semester_tables(self, *args, **kwargs):
        for table_string in self.generate_semester_table_strings():
            print(table_string, *args, **kwargs)

    def print_lecturer_tables(self, *args, **kwargs):
        for table_string in self.generate_semester_table_strings():
            print(table_string, *args, **kwargs)
        pass

    def generate_semester_table_strings(self):
        return [self._generate_semester(semester) for semester in self.solution.keys()]

    def generate_lecturer_table_strings(self):
        return [self._generate_semester(semester) for semester in self.solution.keys()]

    def _generate_semester(self, semester):
        result = ""
        result += self._generate_header(semester)
        result += self._generate_body(semester, False)
        result += self._generate_footer()

        return result

    def _generate_header(self,semester):
        fields = []
        fields.append(f'{semester:^{self.col_width //2}}')
        fields += list(map(lambda weekday: f'{str.capitalize(weekday):^{self.col_width}}', self.days))

        result = ""
        result += self.line_top
        result += "|" + "|".join(fields) + "|\n"

        return result

    def _generate_body(self, semester, print_rows: bool):
        result = ""

        for time_slot in range(self._calculate_max_slot() + 1):
            module_fields = []
            lecturer_fields = []
            room_fields = []
            fields = []

            for day in self.days:
                try:
                    data = self.solution[semester][day][time_slot]

                    if print_rows:
                        module = f'{data["module"]["module_id"]}'
                        lecturer = f'{data["lecturer"]["lecturer_name"]}'
                        room = f'{data["room"]["room_id"]}'

                        module_fields.append(f'{module:^{self.col_width}}')
                        lecturer_fields.append(f'{lecturer:^{self.col_width}}')
                        room_fields.append(f'{room:^{self.col_width}}')
                    
                    else:
                        text = f'{data["position"]}, {data["module"]["module_id"]}, {data["lecturer"]["lecturer_name"]}'
                        fields.append(f'{text:<{self.col_width}}')


                except KeyError:
                    module_fields.append(f'{"":{self.col_width}}')
                    lecturer_fields.append(f'{"---":^{self.col_width}}')
                    room_fields.append(f'{"":{self.col_width}}')
                    fields.append(f'{"---":^{self.col_width}}')
                    continue

            result += self.line_mid
            if print_rows:
                result += f'|{"":^{self.col_width //2}}|'
                result += "|".join(module_fields) + "|\n"

                result += f'|{time_slot+1:^{self.col_width //2}}|'
                result += "|".join(lecturer_fields) + "|\n"

                result += f'|{"":^{self.col_width //2}}|'
                result += "|".join(room_fields) + "|\n"
            else:
                result += f'|{time_slot+1:^{self.col_width //2}}|'
                result += "|".join(fields) + "|\n"

        return result
    
    def _generate_footer(self):
        result = ""
        result += self.line_bot
        return result

    def calc_dynamic_col_width(self, solution):
        words = []
        for semester in solution.values():
            for day in semester.values():
                for slot in day.values():
                    try: 
                        words.append(len(slot["lecturer"]["lecturer_name"]) + len(slot["module"]["module_id"]))
                    except KeyError:
                        pass
        return max(words) + 3

    def _calculate_max_slot(self):
        result = 0
        for days in self.solution.values():
            for time_slots in days.values():
                current_max = list(time_slots.keys())[-1]
                result =  max(current_max, result)
        return result


if __name__ == "__main__":
    main()
