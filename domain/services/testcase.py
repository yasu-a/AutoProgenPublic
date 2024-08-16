# from domain.errors import ExecuteConfigEditDomainServiceError
# from domain.models.testcase import ExecuteConfig
#
#
# class ExecuteConfigInputFileEditDomainService:
#     def __init__(self, execute_config: ExecuteConfig):
#         self._execute_config = execute_config
#
#     def add_stdin(self) -> None:
#         if None in self._execute_config.input_files:
#             raise ExecuteConfigEditDomainServiceError(
#                 reason=f"標準入力は既に存在します",
#             )
#         self._execute_config.input_files[None] = b""
#
#     def add_input_file(self, filename: str) -> None:
#         if filename in self._execute_config.input_files:
#             raise ExecuteConfigEditDomainServiceError(
#                 reason=f"既に存在するファイル名です: '{filename}'",
#             )
#         self._execute_config.input_files[filename] = b""
#
#     def set_stdin_content_string(self, content: str) -> None:
#         if None not in self._execute_config.input_files:
#             raise ExecuteConfigEditDomainServiceError(
#                 reason=f"標準入力は存在しません",
#             )
#         self._execute_config.input_files[None] = content.encode("utf-8")
#
#     def set_input_file_content_string(self, filename: str, content: str) -> None:
#         if filename not in self._execute_config.input_files:
#             raise ExecuteConfigEditDomainServiceError(
#                 reason=f"存在しないファイル名です: '{filename}'",
#             )
#         self._execute_config.input_files[filename] = content.encode("utf-8")
#
#     def get_stdin_content_string(self) -> str:
#         if None not in self._execute_config.input_files:
#             raise ExecuteConfigEditDomainServiceError(
#                 reason=f"標準入力は存在しません",
#             )
#         return self._execute_config.input_files[None].decode("utf-8")
#
#     def get_input_file_content_string(self, filename: str) -> str:
#         if filename not in self._execute_config.input_files:
#             raise ExecuteConfigEditDomainServiceError(
#                 reason=f"存在しないファイル名です: '{filename}'",
#             )
#         return self._execute_config.input_files[filename].decode("utf-8")
#
#     def rename_input_file(self, filename: str, new_filename: str) -> None:
#         if filename not in self._execute_config.input_files:
#             raise ExecuteConfigEditDomainServiceError(
#                 reason=f"存在しないファイル名です: '{filename}'",
#             )
#         self._execute_config.input_files[new_filename] \
#             = self._execute_config.input_files.pop(filename)
#
#     def delete_stdin(self) -> None:
#         if None not in self._execute_config.input_files:
#             raise ExecuteConfigEditDomainServiceError(
#                 reason=f"標準入力は存在しません",
#             )
#         del self._execute_config.input_files[None]
#
#     def delete_input_file(self, filename: str) -> None:
#         if filename not in self._execute_config.input_files:
#             raise ExecuteConfigEditDomainServiceError(
#                 reason=f"存在しないファイル名です: '{filename}'",
#             )
#         del self._execute_config.input_files[filename]
