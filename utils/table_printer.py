# Add option for more courses (KI, WI, etc.)

class TablePrinter():
    """
    2      | monday     | tue...
    ____________________________________
    0      | KI240, L01 | ....
    ____________________________________
    1      | KI240, L01 | ....
    ____________________________________
    2      | KI240, L01 | ....
    """

    column_width = 12
    days = ["monday", "tuesday", "wednesday", "thursday", "friday"]

    line_top = "+"+"-"*(column_width//2)+"+"+(("-"*column_width)+"+")*(len(days)-1)+ ("-"*column_width)+"+\n"
    line = "+"+"-"*(column_width//2)+"+"+(("-"*column_width)+"+")*(len(days)-1)+ ("-"*column_width)+"+\n"
    line_bot = "+"+"-"*(column_width//2)+"+"+(("-"*column_width)+"+")*(len(days)-1)+ ("-"*column_width)+"+\n"

    def __init__(self, solution_object: dict[str, dict[str, dict[int, list]]]) -> None:
        self.solution = solution_object

    def print_tables(self):
        for table in self.generate_tables():
            print(table)

    def generate_tables(self):
        return [self._generate_semester(semester) for semester in self.solution.keys()]

    def _generate_semester(self, semester):
        result = ""
        result += self._generate_header(semester)
        result += self._generate_footer()

        return result


    def _generate_header(self,semester):
        fields = []
        fields.append(f"{semester:^{self.column_width //2}}")
        fields += list(map(lambda weekday: f"{str.capitalize(weekday):^{self.column_width}}", self.days))

        result = ""
        result += self.line_top
        result += "|" + "|".join(fields) + "|\n"

        result += self.line
        return result
    
    def _generate_footer(self):
        result = ""
        result += self.line_bot
        return result


obj = {
        '2': {
            'monday': {
                0: [],
                1: [],
                2: [['KI240p', 'Auer']],
                3: [['KI240l', 'Auer']],
                4: [],
                5: [['KI250l', 'Eisenreich']],
                6: [['KI210p', 'Kromer']],
                7: [],
                8: [['KI240p', 'Auer']],
                9: []
            },
        },
        "4": {}
    }
TablePrinter(obj).print_tables()
# printer = TablePrinter(obj)
# print(printer._generate_header(2), end="")
# print(printer._generate_footer(), end="")
# print(printer._generate_semester(2))