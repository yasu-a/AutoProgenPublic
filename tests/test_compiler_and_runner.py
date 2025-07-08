from contextlib import contextmanager
from pathlib import Path

import pytest

from application.dependency.path_provider import get_global_path_provider
from application.dependency.repositories import get_storage_repository
from application.dependency.services import get_storage_create_service, \
    get_storage_load_test_source_service, get_storage_delete_service, \
    get_storage_run_compiler_service, get_storage_run_executable_service
from application.state.current_project import set_current_project_id, get_current_project_id
from application.state.debug import set_debug
from domain.errors import StorageRunCompilerServiceError, StorageRunExecutableServiceError
from domain.models.values import ProjectID, FileID


def override_dependency():
    import application.dependency.path_provider

    print(f"{Path(__file__).parent=}")

    def get_project_list_folder_fullpath_override():
        return Path(__file__).parent / "test_project_list"

    application.dependency.path_provider.get_project_list_folder_fullpath \
        = get_project_list_folder_fullpath_override

    def get_global_base_path_override():
        return Path(__file__).parent / "test_global"

    application.dependency.path_provider.get_global_base_path \
        = get_global_base_path_override

    def get_storage_path_provider_override():
        return Path(__file__).parent / "test_storage"

    application.dependency.path_provider.get_storage_path_provider \
        = get_storage_path_provider_override


@pytest.fixture(autouse=True)
def setup_test():
    set_debug(True)  # コンパイラの設定をデバッグ時の設定にするため
    if get_current_project_id() is None:
        set_current_project_id(ProjectID("test_project_id"))  # テスト用プロジェクトを設定
    override_dependency()


def write_test_source(source: str):
    test_source_filepath = get_global_path_provider().test_source_file_fullpath()
    test_source_filepath.parent.mkdir(parents=True, exist_ok=True)
    test_source_filepath.write_text(source, encoding="utf-8")


# ストレージ領域
@contextmanager
def create_storage():
    storage_id = get_storage_create_service().execute()
    try:
        yield storage_id
    finally:
        get_storage_delete_service().execute(storage_id=storage_id)


# Storage内のファイルのパス
SOURCE_FILE_RELATIVE_PATH = Path("main.c")
EXECUTABLE_FILE_RELATIVE_PATH = Path("main.exe")


def test_compile_success():
    write_test_source(r"""
        #include <stdio.h>
        int main() {
            printf("Hello, world!");
            return 0;
        }
    """)

    with create_storage() as storage_id:
        # ストレージ領域にテスト用のソースコードをロード
        get_storage_load_test_source_service().execute(
            storage_id=storage_id,
            file_relative_path=SOURCE_FILE_RELATIVE_PATH,
        )

        # コンパイルの実行
        try:
            service_result = get_storage_run_compiler_service().execute(
                storage_id=storage_id,
                source_file_relative_path=SOURCE_FILE_RELATIVE_PATH,
            )
        except StorageRunCompilerServiceError as e:
            print(" *** reason")
            print(e.reason)
            print(" *** output")
            print(e.output)
            assert False  # コンパイルは成功するはず
        else:
            print(" *** output")
            print(service_result.output)


def test_compile_fail():
    write_test_source(r"""
        #include <stdio.h>
        int main() {
            printf("Hello, world!")
            return 0;
        }
    """)

    with create_storage() as storage_id:
        # ストレージ領域にテスト用のソースコードをロード
        get_storage_load_test_source_service().execute(
            storage_id=storage_id,
            file_relative_path=SOURCE_FILE_RELATIVE_PATH,
        )

        # コンパイルの実行
        try:
            service_result = get_storage_run_compiler_service().execute(
                storage_id=storage_id,
                source_file_relative_path=SOURCE_FILE_RELATIVE_PATH,
            )
        except StorageRunCompilerServiceError as e:
            print(" *** reason")
            print(e.reason)
            print(" *** output")
            print(e.output)
            assert "コンパイルエラーが発生しました" in e.reason
            assert "main.c(5): error C2143" in e.output
        else:
            print(" *** output")
            print(service_result.output)
            assert False  # コンパイルは失敗するはず


def test_execute_normal_source_code():
    write_test_source(r"""
        #include <stdio.h>
        int main() {
            printf("Hello, world!\n");
            return 0;
        }
    """)

    with create_storage() as storage_id:
        # ストレージ領域にテスト用のソースコードをロード
        get_storage_load_test_source_service().execute(
            storage_id=storage_id,
            file_relative_path=SOURCE_FILE_RELATIVE_PATH,
        )

        # コンパイルの実行
        try:
            get_storage_run_compiler_service().execute(
                storage_id=storage_id,
                source_file_relative_path=SOURCE_FILE_RELATIVE_PATH,
            )
        except StorageRunCompilerServiceError:
            assert False  # コンパイルは成功するはず

        # コンパイルの実効と標準出力ファイルの書き込み
        try:
            service_result = get_storage_run_executable_service().execute(
                storage_id=storage_id,
                executable_file_relative_path=EXECUTABLE_FILE_RELATIVE_PATH,
                timeout=2,
            )
        except StorageRunExecutableServiceError as e:
            print(" *** reason")
            print(e.reason)
            assert False
        else:
            print(" *** output")
            print(repr(service_result.stdout_text))
            assert service_result.stdout_text == "Hello, world!\n"


def test_execute_normal_scanf_source_code():
    write_test_source(r"""
        #include <stdio.h>
        int main() {
            int a, b;
            scanf("%d", &a);
            scanf("%d", &b);
            printf("sum = %d\n", a + b);
            return 0;
        }
    """)

    with create_storage() as storage_id:
        # ストレージ領域にテスト用のソースコードをロード
        get_storage_load_test_source_service().execute(
            storage_id=storage_id,
            file_relative_path=SOURCE_FILE_RELATIVE_PATH,
        )

        # コンパイルの実行
        try:
            get_storage_run_compiler_service().execute(
                storage_id=storage_id,
                source_file_relative_path=SOURCE_FILE_RELATIVE_PATH,
            )
        except StorageRunCompilerServiceError:
            assert False  # コンパイルは成功するはず

        # 標準入力の準備
        storage_repo = get_storage_repository()
        storage = storage_repo.get(storage_id)
        storage.files[FileID.STDIN.deployment_relative_path] = b"12345\n45678\n"
        storage_repo.put(storage)

        # コンパイルの実効と標準出力ファイルの書き込み
        try:
            service_result = get_storage_run_executable_service().execute(
                storage_id=storage_id,
                executable_file_relative_path=EXECUTABLE_FILE_RELATIVE_PATH,
                timeout=2,
            )
        except StorageRunExecutableServiceError as e:
            print(" *** reason")
            print(e.reason)
            assert False
        else:
            print(" *** output")
            print(repr(service_result.stdout_text))
            assert service_result.stdout_text == "sum = 58023\n"  # 12345 + 45678


# FIXME: NOT WORKING 実行のタイムアウトが再現できない
# def test_execute_infinite_scanf_blocking_timeout():
#     write_test_source(r"""
#         #include <stdio.h>
#         int main() {
#             int a, b;
#             scanf("%d", &a);
#             scanf("%d", &b);
#             printf("sum = %d\n", a + b);
#             return 0;
#         }
#     """)  # too many scanfs
#
#     with create_storage() as storage_id:
#         # ストレージ領域にテスト用のソースコードをロード
#         get_storage_load_test_source_service().execute(
#             storage_id=storage_id,
#             file_relative_path=SOURCE_FILE_RELATIVE_PATH,
#         )
#
#         # コンパイルの実行
#         try:
#             get_storage_run_compiler_service().execute(
#                 storage_id=storage_id,
#                 source_file_relative_path=SOURCE_FILE_RELATIVE_PATH,
#             )
#         except StorageRunCompilerServiceError:
#             assert False  # コンパイルは成功するはず
#
#         # 標準入力の準備
#         # storage_repo = get_storage_repository()
#         # storage = storage_repo.get(storage_id)
#         # storage.files[FileID.STDIN.deployment_relative_path] = b""  # give nothing
#         # storage_repo.put(storage)
#
#         # コンパイルの実効と標準出力ファイルの書き込み
#         try:
#             get_storage_run_executable_service().execute(
#                 storage_id=storage_id,
#                 executable_file_relative_path=EXECUTABLE_FILE_RELATIVE_PATH,
#                 timeout=2,
#             )
#         except StorageRunExecutableServiceError as e:
#             print(" *** reason")
#             print(e.reason)
#             assert "タイムアウト" in e.reason
#         else:
#             assert False
