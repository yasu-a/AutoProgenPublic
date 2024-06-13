import codecs
import os
from dataclasses import dataclass

import dateutil.parser

import state
from files.environment import EnvironmentIO
from files.master import StudentMasterIO
from files.submission import SubmissionIO
from files.testcase import TestCaseIO
from models.environment import EnvEntryLabel
from models.student import StudentMeta, Student
from models.testcase import TestSessionResult, StudentTestResult
from services.compiler import StudentEnvCompiler
from services.importer import StudentSubmissionImporter
from services.tester import StudentEnvironmentTester


class ProjectService:
    def __init__(self, project_path, env_dir_path):
        self.__project_path = project_path
        self.__env_dir_path = env_dir_path
        self.__master_path = os.path.join(self.__project_path, "reportlist.xlsx")

        self.__env_io = EnvironmentIO(env_path=self.__env_dir_path)
        self.__submission_io = SubmissionIO(project_path=self.__project_path)
        self.__master_io = StudentMasterIO(master_path=self.__master_path)
        self.__testcase_io = TestCaseIO(
            testcase_dir_fullpath=os.path.join(self.__project_path, "testcases"),
        )

    def create_student_profile_if_not_exists(self):
        with state.data() as data:
            if data.has_student_profiles():
                return
            df = self.__master_io.read_as_dataframe()
            for _, row in df.iterrows():
                has_submission = row["submission_folder_name"] is not None
                student_meta = StudentMeta(
                    student_id=row["student_id"],
                    name=row["name"],
                    name_en=row["name_en"],
                    email_address=row["email_address"],
                    submitted_at=dateutil.parser.parse(
                        row["submitted_at"]) if has_submission else None,
                    num_submissions=int(row["num_submissions"]) if has_submission else 0,
                    submission_folder_name=row["submission_folder_name"],
                )
                student = Student.from_meta(student_meta)
                data.students[student_meta.student_id] = student
            state.commit_data()

    def open_submission_folder_in_explorer(self, student_id: str):
        with state.data() as data:
            student = data.students[student_id]

        if student.meta.submission_folder_name is None:
            return

        submission_folder_fullpath = self.__submission_io.student_submission_folder_fullpath(
            student.meta.submission_folder_name
        )
        os.startfile(submission_folder_fullpath)

    def create_runtime_environment(self, student_id):
        with state.data() as data:
            submission_importer = StudentSubmissionImporter(
                env_io=self.__env_io,
                submission_io=self.__submission_io,
            )
            student_mata = data.students[student_id].meta
            student_env_meta_mapping = submission_importer.import_all_and_create_env_meta(
                student_meta_list=[student_mata],
            )
            for student_id, env_meta in student_env_meta_mapping.items():
                data.students[student_id].env_meta = env_meta
            state.commit_data()

    def compile_environment(self, student_id):
        environment_compiler = StudentEnvCompiler(
            env_io=self.__env_io,
        )
        with state.data(readonly=True) as data:
            student = data.students[student_id]
        student_compile_result = environment_compiler.compile_and_get_result(student)
        with state.data() as data:
            data.students[student_id].compile_result = student_compile_result
            state.commit_data()

    def run_auto_test(self, student_id):
        tester = StudentEnvironmentTester(
            env_io=self.__env_io,
            testcase_io=self.__testcase_io,
        )
        target_indexes = self.__testcase_io.list_target_numbers()
        with state.data(readonly=True) as data:
            student = data.students[student_id]
        test_session_results: dict[int, TestSessionResult] = tester.run_all_tests_on_student(
            student=student,
            target_indexes=target_indexes,
        )
        with state.data() as data:
            data.students[student_id].test_result = StudentTestResult(
                test_session_results=test_session_results,
            )
            state.commit_data()

    def get_testcase_io(self):  # TODO: Lock this resource
        return self.__testcase_io

    @classmethod
    def clear_all_test_results(cls):
        with state.data() as data:
            for student in data.students.values():
                student.test_result = None
            state.commit_data()

    def get_submitted_source_code_for(self, student_id: str, target_number: int) -> str | None:
        with state.data() as data:
            entry_source = data.students[student_id].env_meta.get_env_entry_by_label_and_number(
                label=EnvEntryLabel.SOURCE_MAIN,
                number=target_number,
            )
        if entry_source is None:
            return None
        source_fullpath = self.__env_io.get_student_env_entry_fullpath(
            student_id=student_id,
            item_name=entry_source.path,
        )
        with codecs.open(source_fullpath, "r", "utf-8") as f:
            return f.read()

    @dataclass
    class MarkEntry:
        student: Student
        target_number: int

        def __eq__(self, other):
            return self.student.meta.student_id == other.student.meta.student_id \
                and self.target_number == other.target_number

    def list_mark_entries(self) -> list[MarkEntry]:
        entries = []
        with state.data(readonly=True) as data:
            for student_id in data.student_ids:
                student = data.students[student_id]
                if student.test_result is None:
                    continue
                for target_number in student.test_result.test_session_results.keys():
                    entry = self.MarkEntry(
                        student=student,
                        target_number=target_number,
                    )
                    entries.append(entry)
        entries = sorted(entries, key=lambda e: e.target_number)
        return entries
