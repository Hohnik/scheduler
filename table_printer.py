# Add option for more courses (KI, WI, etc.)

class TablePrinter():
    """
    {
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
    }

    2      | monday     | tue...
    ____________________________________
    0      | KI240, L01 | ....
    ____________________________________
    1      | KI240, L01 | ....
    ____________________________________
    2      | KI240, L01 | ....
    """
    column_width = 15
    def __init__(self, solution_object: dict) -> None:
        self.solution = solution_object
        pass


    def generate_headers(self):
        semester = iter(self.solution.keys())
        result = []
        fields = []
        while True:
            try:
                fields.append(f"{next(semester)}:<{self.column_width}")
            except:
                return iter(result)

        print()