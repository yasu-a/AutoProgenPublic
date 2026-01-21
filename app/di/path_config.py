# import sys
# from dataclasses import dataclass
# from pathlib import Path
# from typing import Callable
# 
# from shared.domain.value.identifier import ProjectID, StudentID, StorageID
# 
# 
# @dataclass(slots=True)
# class PathConfig:
#     # === グローバルパス（引数なし） ===
#     global_base_path: Path
#     static_resource_base_path: Path
#     settings_json_fullpath: Path
#     test_source_file_fullpath: Path
#     app_version_json_fullpath: Path
#     project_list_folder_fullpath: Path
# 
#     # === プロジェクト依存パス ===
#     project_folder_fullpath: Callable[[ProjectID], Path]  # project id
#     project_config_json_fullpath: Callable[[ProjectID], Path]  # project id
# 
#     # === カレントプロジェクト用ベースパス ===
#     current_project_testcase_config_base_folder: Callable[[ProjectID], Path]  # current project id
#     current_project_database_fullpath: Callable[[ProjectID], Path]  # current project id
# 
#     # === ID引数が必要なパス ===
#     storage_folder_fullpath: Callable[
#         [ProjectID, StorageID], Path]  # current project id, storage id
#     student_submission_folder_fullpath: Callable[
#         [ProjectID, StudentID], Path]  # current project id, student id
# 
#     # === 静的リソースパス ===
#     icon_fullpath: Callable[[str], Path]  # filename
#     image_fullpath: Callable[[str], Path]  # filename
# 
# 
# def create_path_config() -> PathConfig:
#     global_base = Path(sys.argv[0]).resolve().parent
#     static_resource_base = global_base / "static"
#     project_list_folder = Path("~/AutoProgenProjects").expanduser().resolve()
# 
#     # ベースとなるラムダ定義
#     project_folder = lambda pid: project_list_folder / str(pid)
#     testcase_config_base = lambda pid: project_folder(pid) / "testcases"
#     dynamic_base = lambda pid: project_folder(pid) / "dynamic"
#     static_base = lambda pid: project_folder(pid) / "static"
#     submission_base = lambda pid: static_base(pid) / "reports"
#     storage_base = lambda pid: dynamic_base(pid) / "StorageEntity"
# 
#     return PathConfig(
#         # === グローバルパス（引数なし） ===
#         global_base_path=global_base,
#         static_resource_base_path=static_resource_base,
#         settings_json_fullpath=global_base / "settings.json",
#         test_source_file_fullpath=global_base / "vctest" / "test.c",
#         app_version_json_fullpath=global_base / "app_version.json",
#         project_list_folder_fullpath=project_list_folder,
# 
#         # === プロジェクト依存パス ===
#         project_folder_fullpath=project_folder,
#         project_config_json_fullpath=lambda pid: project_folder(pid) / "config.json",
# 
#         # === カレントプロジェクト用ベースパス ===
#         current_project_testcase_config_base_folder=testcase_config_base,
#         current_project_database_fullpath=lambda pid: dynamic_base(pid) / "database.sqlite3",
# 
#         # === ID引数が必要なパス ===
#         storage_folder_fullpath=lambda pid, st_id: storage_base(pid) / str(st_id),
#         student_submission_folder_fullpath=lambda pid, s_id: submission_base(pid) / str(s_id),
# 
#         # === 静的リソースパス ===
#         icon_fullpath=lambda filename: static_resource_base / "icon" / f"{filename}.png",
#         image_fullpath=lambda filename: static_resource_base / "img" / f"{filename}.jpg",
#     )
# 
# 
# _path_config = create_path_config()
# 
# 
# def get_path_config() -> PathConfig:
#     return _path_config
