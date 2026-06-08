class Scheduler:

    def __init__(self):
        self.pending_tasks = []

    def submit_task(self, task):
        self.pending_tasks.append(task)

    def get_next_task(self):
        if not self.pending_tasks:
            return None

        return self.pending_tasks.pop(0)

    def has_tasks(self):
        return len(self.pending_tasks) > 0