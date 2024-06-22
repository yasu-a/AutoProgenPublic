from collections import OrderedDict
from dataclasses import dataclass

# from models.student import Student, StudentMeta

#
# @dataclass(slots=True)
# class ProjectData:
#     students: OrderedDict[str, Student]  # student_id -> Student
#     # test_sessions: dict[int, TestSession]  # question target id -> TestCaseGroup
#     version: tuple[int] = (0, 1)
#
#     def to_json(self):
#         return dict(
#             students={k: v.to_json() for k, v in self.students.items()},
#             # testflows TODO: impl
#             version=self.version,
#         )
#
#     @classmethod
#     def from_json(cls, body):
#         return cls(
#             students=OrderedDict({
#                 k: Student.from_json(body["students"][k])
#                 for k in sorted(body["students"])
#             }),
#             # test_sessions={},  # TODO: impl
#             version=tuple(body["version"]),
#         )
#
#     @classmethod
#     def create_empty(cls):
#         return cls(
#             students=OrderedDict(),
#             # test_sessions={},
#         )
#
#     def has_student_profiles(self):
#         return bool(self.students)
#
#     def clear_student_profile(self):
#         self.students.clear()
#
#     @property
#     def student_meta_mapping(self) -> dict[str, StudentMeta]:  # student_id -> StudentMeta
#         return {k: v.meta for k, v in self.students.items()}
#
#     @property
#     def student_ids(self) -> list[str]:
#         return list(self.students.keys())
#
#     @property
#     def target_indexes_recorded(self) -> list[int]:
#         target_indexes_recorded = set()
#         for student in self.students.values():
#             if student.test_result is not None:
#                 target_indexes = student.test_result.test_session_results.keys()
#                 for target_index in target_indexes:
#                     target_indexes_recorded.add(target_index)
#         return sorted(target_indexes_recorded)
