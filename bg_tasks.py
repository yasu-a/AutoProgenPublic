# from contextlib import contextmanager
#
# from PyQt5.QtCore import QObject, QThread, QTimer, QMutex
#
# import state
# from app_logging import create_logger
# from models.student import StudentProcessStage
# from settings import settings_misc


# class TaskThread(QThread):
#     def identity(self):
#         return None
#
#     def title(self):
#         raise NotImplementedError()
#
#     def message(self):
#         return NotImplementedError()


# class StudentTaskThread(TaskThread):
#     def __init__(self, student_id: str):
#         super().__init__()
#
#         self._student_id = student_id
#
#     def identity(self):
#         return "student", self._student_id
#
#     def student_id_dedicated(self):
#         return self._student_id


# class StudentProcessAllTaskThread(StudentTaskThread):
#     _logger = create_logger()
#
#     def __init__(self, student_id: str):
#         super().__init__(student_id)
#
#     def run(self):
#         while True:
#             with state.data(readonly=True) as data:
#                 next_stage = data.students[self._student_id].required_next_stage
#             if next_stage is None:
#                 self._logger.info(f"all stages done: {self._student_id}")
#                 break
#
#             if next_stage == StudentProcessStage.ENVIRONMENT_BUILDING:
#                 state.project_service.create_runtime_environment(self._student_id)
#             elif next_stage == StudentProcessStage.COMPILE:
#                 state.project_service.compile_environment(self._student_id)
#             elif next_stage == StudentProcessStage.AUTO_TESTING:
#                 state.project_service.run_auto_test(self._student_id)
#             else:
#                 assert False, next_stage
#
#             with state.data(readonly=True) as data:
#                 next_stage_after_process = data.students[self._student_id].required_next_stage
#
#             if next_stage_after_process == next_stage:
#                 self._logger.info(f"stage stopped: {next_stage} {self._student_id}")
#                 break
#
#     def title(self):
#         return f"データの処理中: {self._student_id}"
#
#     def message(self):
#         return ""
#
#     def __repr__(self):
#         return f"<StudentProcessAllTaskThread student_id={self._student_id}>"


# class BackgroundTasks(QObject):
#     _logger = create_logger()
#
#     def __init__(self, parent: QObject = None):
#         super().__init__(parent)
#
#         self.__lock = QMutex()
#         self.__tasks: list[TaskThread] = []
#
#         self.__timer = QTimer(self)
#         self.__timer.setInterval(10)
#         self.__timer.timeout.connect(self.__timer_timeout)  # type: ignore
#         self.__timer.start()
#
#     def list_student_id_in_process(self) -> list[str]:
#         with self._lock():
#             return [
#                 task.student_id_dedicated()
#                 for task in self.__tasks
#                 if isinstance(task, StudentTaskThread)
#             ]
#
#     @contextmanager
#     def _lock(self):
#         self.__lock.lock()
#         try:
#             yield
#         finally:
#             self.__lock.unlock()
#
#     def enqueue(self, target_task: TaskThread):
#         with self._lock():
#             identity = target_task.identity()
#             if identity is not None:
#                 for task in self.__tasks:
#                     if task.identity() == identity:
#                         self._logger.info("{target_task} {identity} already exists")
#                         return
#             self.__tasks.append(target_task)
#             self._logger.info(f"{target_task} now in queue")
#
#     def count_running_tasks(self):
#         with self._lock():
#             return sum([task.isRunning() for task in self.__tasks])
#
#     def count_tasks_in_queue(self):
#         with self._lock():
#             return len(self.__tasks)
#
#     def pop_all_finished(self):
#         with self._lock():
#             pop_indexes = []
#             for i, task in enumerate(self.__tasks):
#                 if task.isFinished():
#                     pop_indexes.append(i)
#             for i in reversed(pop_indexes):
#                 # print(f"[BackgroundTasks] {self.__tasks[i]} removed")
#                 self.__tasks.pop(i)
#
#     def start_new(self):
#         with self._lock():
#             for task in self.__tasks:
#                 if not task.isRunning():
#                     task.start()
#                     # print(f"[BackgroundTasks] {task} started")
#                     break
#
#     def __timer_timeout(self):
#         self.pop_all_finished()
#
#         if self.count_running_tasks() < settings_misc.get_max_workers():
#             self.start_new()


# class BackgroundTaskDispatcher:
#     def __init__(self, tasks):
#         self.__tasks = tasks
#
#     def run_full_process(self, student_id: str):
#         task = StudentProcessAllTaskThread(student_id)
#         self.__tasks.enqueue(task)
#
#     def run_full_process_for_all_students(self):
#         with state.data(readonly=True) as data:
#             student_ids = data.student_ids
#         for student_id in student_ids:
#             self.run_full_process(student_id)
