class TaskManager:
    def __init__(self):
        self.functions = []

    def register(self, func, execute_once=False, *args, **kwargs):
        self.functions.append((func, execute_once, args, kwargs))

    def execute(self):
        for func, execute_once, args, kwargs in self.functions:
            if execute_once:
                func(*args, **kwargs)

        while True:
            for func, execute_once, args, kwargs in self.functions:
                if not execute_once:
                    func(*args, **kwargs)
