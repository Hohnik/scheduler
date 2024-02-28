#TODO Update data structure to -> semester: { day: { time_slot: { lecturer: {}, module: {}, room: {}}}}
class TablePrinter():
    days = ["mon", "tue", "wed", "thu", "fri"]
    def __init__(self, solution: dict[str, dict[str, dict[int, list]]]) -> None:
        print(type(solution))
        self.solution = solution
        self.col_width = self.calc_dynamic_col_width(solution)
        self.line_top = "+"+"-"*(self.col_width//2)+"+"+(("-"*self.col_width)+"+")*(len(self.days)-1)+ ("-"*self.col_width)+"+\n"
        self.line = "+"+"-"*(self.col_width//2)+"+"+(("-"*self.col_width)+"+")*(len(self.days)-1)+ ("-"*self.col_width)+"+\n"
        self.line_bot = "+"+"-"*(self.col_width//2)+"+"+(("-"*self.col_width)+"+")*(len(self.days)-1)+ ("-"*self.col_width)+"+\n"

    def print_tables(self, *args, **kwargs):
        for table_string in self.generate_table_strings():
            print(table_string, *args, **kwargs)

    def generate_table_strings(self):
        return [self._generate_semester(semester) for semester in self.solution.keys()]

    def _generate_semester(self, semester):
        result = ""
        result += self._generate_header(semester)
        result += self._generate_body(semester)
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

    def _generate_body(self, semester):
        result = ""
        for time_slot in range(list(self.solution[list(self.solution.keys())[0]]["mon"].keys())[-1]+1):
            result += self.line
            result += f'|{time_slot:^{self.col_width //2}}|'

            fields = []
            for day in self.days:
                try:
                    data = self.solution[semester][day][time_slot]
                    text = f'{data["module"]["module_id"]}, {data["lecturer"]["lecturer_name"]}'
                    fields.append(f'{text:<{self.col_width}}')
                except KeyError:
                    fields.append(f'{"---":^{self.col_width}}')
                    continue
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

obj = {
        'KI2': {
            'mon': {
                0: {
                    "lecturer": {
                        "lecturer_id": "001",
                        "lecturer_name": "Osendorfer"
                    }, 
                    "module": {
                        "module_id": "lKI210",
                        "module_name": "Programmieren I"
                    }, 
                    "room": {
                        "room_id": "G005",
                    }
                },
                1: {
                },
            },
        }
    }


if __name__ == "__main__":
    print("Here a little test table:")
    printer = TablePrinter(obj)
    printer.print_tables(end="The print_tables method can be used like a normal print")