# from files.project import ProjectIO
# from files.settings import GlobalSettingsIO
# from files.testcase import TestCaseIO
# from models.values import StudentID, TestCaseID
#
#
# class ExecuteService:
#     def __init__(
#             self,
#             *,
#             global_settings_io: GlobalSettingsIO,
#             project_io: ProjectIO,
#             testcase_io: TestCaseIO,
#     ):
#         self._global_settings_io = global_settings_io
#         self._project_io = project_io
#         self._testcase_io = testcase_io
#
#     def list_testcase_ids(self) -> list[TestCaseID]:
#         return self._testcase_io.list_ids()
#
#     def construct_test_folder_from_testcase(self, testcase_id: TestCaseID):
#
#
#     def _execute_and_save_result(self, student_id: StudentID):
#         list_testcase_ids
#
#     def execute_and_save_result(self, student_id: StudentID):
#         try:
#             self._execute_and_save_result(student_id)
