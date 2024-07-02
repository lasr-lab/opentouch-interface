from typing import Callable, List, Tuple


class TaskManager:
    """
    Manages and executes tasks registered for the application.
    """
    def __init__(self):
        self.functions: List[Tuple[Callable, bool, tuple, dict]] = []

    def register(self, func: Callable, execute_once: bool = False, *args, **kwargs):
        """
        Register a function to be executed by the task manager.
        """
        self.functions.append((func, execute_once, args, kwargs))

    def execute(self):
        """
        Execute all registered functions. Functions registered to execute once will be run first.
        """
        for func, execute_once, args, kwargs in self.functions:
            if execute_once:
                func(*args, **kwargs)

        while True:
            for func, execute_once, args, kwargs in self.functions:
                if not execute_once:
                    func(*args, **kwargs)
