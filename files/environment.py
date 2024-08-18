# import os
# import shutil
#
#
# class EnvironmentIO:
#     def __init__(self, *, env_path):
#         self.__env_path = env_path
#
#     @property
#     def env_path(self):
#         return self.__env_path
#
#     def student_env_fullpath(self, student_id) -> str:
#         return os.path.join(self.__env_path, student_id)  # type: ignore
#
#     def remove_if_exists(self, student_id):
#         student_env_fullpath = self.student_env_fullpath(student_id)
#         if os.path.exists(student_env_fullpath):
#             shutil.rmtree(student_env_fullpath)
#
#     def import_if_absent(self, student_id: str, item_name: str, content_bytes: bytes) -> bool:
#         student_env_fullpath = self.student_env_fullpath(student_id)
#         os.makedirs(student_env_fullpath, exist_ok=True)
#         item_dst_path = os.path.join(student_env_fullpath, item_name)
#         item_dst_dir_path = os.path.dirname(item_dst_path)
#         os.makedirs(item_dst_dir_path, exist_ok=True)
#         if os.path.exists(item_dst_path):
#             return False
#         with open(item_dst_path, "wb") as f:
#             f.write(content_bytes)
#         return True
#
#     @classmethod
#     def get_executable_fullpath_by_source_fullpath(cls, source_fullpath: str) -> str | None:
#         source_dirname, source_filename = os.path.split(source_fullpath)
#         source_filename_except_ext, _ = os.path.splitext(source_filename)
#         executable_fullpath = os.path.join(source_dirname, source_filename_except_ext + ".exe")
#         if not os.path.exists(executable_fullpath):
#             return None  # 実行ファイルがない（ソースがないかコンパイル失敗？）
#         return executable_fullpath
#
#     def get_student_env_entry_fullpath(
#             self,
#             student_id: str,
#             item_name: str,
#     ) -> str:
#         student_env_fullpath = self.student_env_fullpath(student_id)
#         entry_fullpath = os.path.join(student_env_fullpath, item_name)
#         return entry_fullpath
#
#     def get_student_env_executable_fullpath(
#             self,
#             student_id: str,
#             item_name: str,
#     ) -> str | None:
#         source_entry_fullpath = self.get_student_env_entry_fullpath(
#             student_id=student_id,
#             item_name=item_name,
#         )
#         executable_fullpath \
#             = self.get_executable_fullpath_by_source_fullpath(source_entry_fullpath)
#         return executable_fullpath
