import os
import re
from abc import ABCMeta
from typing import NamedTuple, Collection

from domain.models.environment import EnvEntryLabel


class EnvItemToImport(NamedTuple):
    item_name: str
    content_bytes: bytes
    label: EnvEntryLabel


class SubmissionFolder(NamedTuple):
    student_id: str
    fullpath: str


class SubmissionImportError(ValueError, metaclass=ABCMeta):
    pass


class SubmissionFormatError(SubmissionImportError):
    def __init__(self, *, reason):
        self.reason = reason


class SubmissionArchiveContentError(SubmissionImportError):
    def __init__(self, *, reason, item_name):
        self.reason = reason
        self.item_name = item_name


class SubmissionArchiveItem(NamedTuple):
    item_name: str
    content_bytes: bytes

    @property
    def extension(self) -> str:
        return os.path.splitext(self.item_name)[1]

    @property
    def filename(self):
        return os.path.split(self.item_name)[1]

    @property
    def filename_except_extension(self):
        return os.path.splitext(self.filename)[0]

    def replace_item_name(self, new_item_name):
        return SubmissionArchiveItem(
            item_name=new_item_name,
            content_bytes=self.content_bytes,
        )

    def replace_content_bytes(self, new_content_bytes):
        return SubmissionArchiveItem(
            item_name=self.item_name,
            content_bytes=new_content_bytes,
        )


class SubmissionArchiveItemMapper:
    @classmethod
    def map_name(cls, item: SubmissionArchiveItem) -> SubmissionArchiveItem:
        if item.extension == ".c":
            m = re.fullmatch(r"[a-z]*(\d+)", item.filename_except_extension)
            if not m:
                raise SubmissionArchiveContentError(
                    reason="ファイル名から問題番号が読み取れません",
                    item_name=item.item_name,
                )
            if not m:
                pass
            q_number = int(m.group(1))
            if q_number >= 100:
                raise SubmissionArchiveContentError(
                    reason="ファイル名から問題番号が読み取れません",
                    item_name=item.item_name,
                )
            new_filename = f"source_main_{q_number:02}.c"
            return item.replace_item_name(new_filename)
        else:
            raise SubmissionArchiveContentError(
                reason="ファイルの種別が不明です",
                item_name=item.item_name,
            )

    @staticmethod
    def __decode_content(content_bytes: bytes, encodings: Collection[str]) -> str | None:
        for encoding in encodings:
            try:
                return content_bytes.decode(encoding, errors="strict")
            except UnicodeDecodeError:
                continue
        return None

    @classmethod
    def map_content(cls, item: SubmissionArchiveItem) -> SubmissionArchiveItem:
        if item.extension == ".c":
            content_str = cls.__decode_content(item.content_bytes, encodings=["utf-8", "shift-jis"])
            if content_str is None:
                raise SubmissionArchiveContentError(
                    reason="ファイルの文字コードが不明です",
                    item_name=item.item_name,
                )
            new_content_bytes = content_str.encode("utf-8")
            return item.replace_content_bytes(new_content_bytes)
        else:
            assert False, item.extension

    @classmethod
    def produce_label(cls, item: SubmissionArchiveItem) -> EnvEntryLabel:
        if item.extension == ".c":
            return EnvEntryLabel.SOURCE_MAIN
        else:
            assert False, item.extension

    @classmethod
    def process(cls, item: SubmissionArchiveItem) -> EnvItemToImport:
        item = cls.map_name(item)
        item = cls.map_content(item)
        label = cls.produce_label(item)
        return EnvItemToImport(
            item_name=item.item_name,
            content_bytes=item.content_bytes,
            label=label,
        )

#
# class StudentSubmissionImporter:
#     def __init__(self, env_io: "EnvironmentIO", submission_io: "SubmissionIO"):
#         self.__env_io = env_io
#         self.__submission_io = submission_io
#
#     @classmethod
#     def find_zipfiles(cls, submission_folder_fullpath: str):
#         zipfile_paths = []
#         for filename in os.listdir(submission_folder_fullpath):
#             fullpath = os.path.join(submission_folder_fullpath, filename)
#             if zipfile.is_zipfile(fullpath):
#                 zipfile_paths.append(fullpath)
#         return zipfile_paths
#
#     @classmethod
#     def find_one_zipfile(cls, submission_folder_fullpath: str):
#         zipfile_paths = cls.find_zipfiles(submission_folder_fullpath)
#         if len(zipfile_paths) != 1:
#             raise SubmissionFormatError(
#                 reason="レポートに含まれているzipファイルが1つではありません"
#             )
#         return zipfile_paths[0]
#
#     @classmethod
#     def iter_zipfile_content_bytes(cls, zipfile_path) -> Iterator[SubmissionArchiveItem]:
#         with zipfile.ZipFile(zipfile_path, "r") as zf:
#             for item_info in zf.infolist():
#                 if item_info.is_dir():
#                     continue
#                 with zf.open(item_info.filename, "r") as f:
#                     content_bytes = f.read()
#                     yield SubmissionArchiveItem(
#                         item_name=item_info.filename,
#                         content_bytes=content_bytes,
#                     )
#
#     def import_student_and_iter_result(self, student_meta: StudentMeta) \
#             -> Iterator[tuple[StudentEnvImportResult, StudentEnvEntry | None]]:
#         try:
#             self.__env_io.remove_if_exists(student_meta.student_id)
#             if student_meta.submission_folder_name is None:
#                 raise SubmissionFormatError(
#                     reason="提出フォルダが存在しません",
#                 )
#             submission_folder_fullpath = self.__submission_io.student_submission_folder_fullpath(
#                 student_meta.submission_folder_name
#             )
#             zipfile_path = self.find_one_zipfile(submission_folder_fullpath)
#             for item in self.iter_zipfile_content_bytes(zipfile_path):
#                 try:
#                     item_to_be_imported = SubmissionArchiveItemMapper.process(item)
#                     absent = self.__env_io.import_if_absent(
#                         student_id=student_meta.student_id,
#                         item_name=item_to_be_imported.item_name,
#                         content_bytes=item_to_be_imported.content_bytes,
#                     )
#                     if not absent:
#                         raise SubmissionArchiveContentError(
#                             item_name=item.item_name,
#                             reason="ファイルが既に存在します",
#                         )
#                 except SubmissionArchiveContentError as e:
#                     import_result = StudentEnvImportResult(
#                         source_item_path=item.item_name,
#                         env_item_path=None,
#                         success=False,
#                         reason=e.reason,
#                     )
#                     entry_info = None
#                 else:
#                     import_result = StudentEnvImportResult(
#                         source_item_path=item.item_name,
#                         env_item_path=item_to_be_imported.item_name,
#                         success=True,
#                         reason=None,
#                     )
#                     entry_info = StudentEnvEntry(
#                         path=item_to_be_imported.item_name,
#                         label=item_to_be_imported.label,
#                         updated_at=datetime.now(),
#                     )
#                 yield import_result, entry_info
#         except PermissionError as e:
#             import_result = StudentEnvImportResult(
#                 source_item_path=None,
#                 env_item_path=None,
#                 success=False,
#                 reason=f"{e.strerror}: {e.filename}",
#             )
#             entry_info = None
#             yield import_result, entry_info
#         except SubmissionFormatError as e:
#             import_result = StudentEnvImportResult(
#                 source_item_path=None,
#                 env_item_path=None,
#                 success=False,
#                 reason=e.reason,
#             )
#             entry_info = None
#             yield import_result, entry_info
#
#     def import_all_and_create_env_meta(self, student_meta_list: list[StudentMeta]) \
#             -> dict[str, StudentEnvMeta]:  # student_id -> StudentEnvMeta
#         result = {}
#         for student_meta in student_meta_list:
#             import_results = {}
#             entries = {}
#             for import_result, entry_info in self.import_student_and_iter_result(student_meta):
#                 import_results[import_result.source_item_path] = import_result
#                 if entry_info is not None:
#                     entries[entry_info.path] = entry_info
#             result[student_meta.student_id] = StudentEnvMeta(
#                 path=self.__env_io.env_path,
#                 import_results=import_results,
#                 entries=entries,
#             )
#         return result
