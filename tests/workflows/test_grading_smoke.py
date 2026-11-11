
"""MSVCを使用して採点処理の全工程を確認する統合テスト。"""

from pathlib import Path

import openpyxl
import pytest

from autoprogen.domain.model.debug_settings import DebugSettings
from autoprogen.domain.model.expected_output_file import ExpectedOutputFile
from autoprogen.domain.model.input_file import InputFile
from autoprogen.domain.model.pattern import PatternList, TextPattern
from autoprogen.domain.model.stage import (
    BuildStage,
    CompileStage,
    ExecuteStage,
    TestStage,
)
from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.value import (
    FileID,
    StudentID,
    TargetID,
    TestCaseID,
)


# 製品クラスをpytestのテストクラス候補として収集させない。
TestStage.__test__ = False
TestCaseID.__test__ = False

pytestmark = pytest.mark.msvc_integration

ARCHIVE_NAME = "grading_smoke.zip"
FIXTURES = Path(__file__).parents[1] / "testdata" / "grading_smoke"

STUDENT_INFO = {
    "26HG200001A": ("テスト　一郎", False),
    "26HG200002B": ("テスト　二郎", True),
    "26HG200003C": ("テスト　三郎", True),
    "26HG200004D": ("テスト　四郎", True),
    "26HG200005E": ("テスト　五郎", True),
}

SCORES = {
    "26HG200001A": None,
    "26HG200002B": 10,
    "26HG200003C": 5,
    "26HG200004D": None,
    "26HG200005E": 0,
}


def _report(message: str) -> None:
    """人が実行経過を追跡できる形式でスモークテストの詳細を出力する。"""
    print(f"[grading-smoke] {message}", flush=True)


def _read_fixture(case: str, filename: str) -> str:
    """固定された入力・期待出力を読み込む。"""
    return (FIXTURES / case / filename).read_text(encoding="utf-8")


def _configure_testcases(project_container) -> None:
    """2件のテストケースを作成・保存・再読み込みする。"""
    for case in ("case_yes", "case_no"):
        project_container.testcase_create_usecase.execute(case)

        testcase_id = TestCaseID(case)
        config = project_container.testcase_get_usecase.execute(testcase_id)

        config.execute_config.input_file_collection.put(
            InputFile(
                file_id=FileID.STDIN,
                content=_read_fixture(case, "stdin.txt"),
            )
        )

        if case == "case_yes":
            config.execute_config.input_file_collection.put(
                InputFile(
                    file_id=FileID(Path("savedata.txt")),
                    content=_read_fixture(case, "savedata_input.txt"),
                )
            )

        expected_names = {
            FileID.STDOUT: "stdout_expected.txt",
        }
        if case == "case_yes":
            expected_names[FileID(Path("savedata.txt"))] = (
                "savedata_expected.txt"
            )

        for file_id, filename in expected_names.items():
            expected = _read_fixture(case, filename)
            config.test_config.expected_output_file_collection.put(
                ExpectedOutputFile(
                    file_id=file_id,
                    patterns=PatternList([
                        TextPattern(
                            index=0,
                            is_expected=True,
                            text=expected,
                            is_multiple_space_ignored=False,
                            is_word=False,
                        )
                    ]),
                )
            )

        project_container.testcase_put_usecase.execute(config)

    assert {
        str(item)
        for item in project_container.testcase_config_list_id_usecase.execute()
    } == {"case_yes", "case_no"}

    for case in ("case_yes", "case_no"):
        config = project_container.testcase_get_usecase.execute(
            TestCaseID(case)
        )
        actual = config.execute_config.input_file_collection.find(
            FileID.STDIN
        ).content_string
        assert actual == _read_fixture(case, "stdin.txt")


def _assert_project_students(project_container) -> None:
    """学生情報と提出フォルダを照合する。"""
    project = project_container.current_project_repository.get()
    assert project.is_initialized
    assert int(project.target_id) == 1

    students = project_container.student_repository.list()
    assert {
        str(student.student_id)
        for student in students
    } == set(STUDENT_INFO)

    for student_id_text, (name, submitted) in STUDENT_INFO.items():
        student_id = StudentID(student_id_text)
        student = project_container.student_repository.get(student_id)

        assert student.name == name
        assert student.is_submitted is submitted

        submission_dir = (
            project_container.project_path_layout.student_submission_dir(
                student_id
            )
        )
        assert submission_dir.is_dir() is submitted

        if submitted:
            assert student.submission_folder_name == (
                f"{student_id_text}@{student_id_text}"
            )


def _assert_stage_results(project_container) -> None:
    """5名×2ケースの実行・採点結果を照合する。"""
    stage_paths = project_container.stage_path_list_sub_service.execute()

    assert {
        str(path.testcase_id)
        for path in stage_paths
    } == {"case_yes", "case_no"}

    for student_id_text in STUDENT_INFO:
        student_id = StudentID(student_id_text)

        for path in stage_paths:
            case = str(path.testcase_id)
            result = (
                project_container.student_stage_path_result_get_service.execute(
                    student_id, path
                )
            )

            build = result.get_result_by_stage_type(BuildStage)
            compile_result = result.get_result_by_stage_type(CompileStage)
            execute_result = result.get_result_by_stage_type(ExecuteStage)
            test_result = result.get_result_by_stage_type(TestStage)

            # 未提出、対象ソース不在。
            if student_id_text in (
                "26HG200001A",
                "26HG200004D",
            ):
                assert build is not None and not build.is_success
                expected_reason = (
                    "未提出"
                    if student_id_text.endswith("001A")
                    else "見つかりません"
                )
                assert expected_reason in build.reason
                assert compile_result is None
                assert execute_result is None
                assert test_result is None
                _report(
                    f"student={student_id_text} case={case} "
                    f"build=failed reason={expected_reason}"
                )
                continue

            assert build is not None and build.is_success

            # コンパイルエラー。
            if student_id_text.endswith("005E"):
                assert compile_result is not None
                assert not compile_result.is_success
                assert execute_result is None
                assert test_result is None
                _report(
                    f"student={student_id_text} case={case} "
                    "build=passed compile=failed"
                )
                continue

            # 正常な実行、または誤答。
            assert compile_result is not None
            assert compile_result.is_success
            assert execute_result is not None
            assert execute_result.is_success
            assert test_result is not None
            assert test_result.is_success

            expected_accepted = not (
                student_id_text.endswith("003C")
                and case == "case_yes"
            )
            assert test_result.is_accepted is expected_accepted
            _report(
                f"student={student_id_text} case={case} "
                "build=passed compile=passed execute=passed "
                f"accepted={expected_accepted}"
            )

            # 標準出力の内容を直接比較する。
            actual_stdout = execute_result.output_file_collection.find(
                FileID.STDOUT
            ).content_string
            expected_stdout = _read_fixture(
                case, "stdout_expected.txt"
            )

            if (
                student_id_text.endswith("003C")
                and case == "case_yes"
            ):
                expected_stdout = expected_stdout.replace(
                    "Run count: 8", "Run count: 9"
                )

            assert actual_stdout == expected_stdout

            # ファイル出力の内容を直接比較する。
            file_id = FileID(Path("savedata.txt"))
            if case == "case_yes":
                assert execute_result.output_file_collection.has(file_id)
                actual_file = execute_result.output_file_collection.find(
                    file_id
                ).content_string
                expected_file = (
                    "9\n"
                    if student_id_text.endswith("003C")
                    else _read_fixture(case, "savedata_expected.txt")
                )
                assert actual_file == expected_file
            else:
                assert not execute_result.output_file_collection.has(file_id)


def _assert_cleared(project_container) -> None:
    """全学生のステージ結果が消去されていることを確認する。"""
    for student_id_text in STUDENT_INFO:
        for path in project_container.stage_path_list_sub_service.execute():
            result = (
                project_container.student_stage_path_result_get_service.execute(
                    StudentID(student_id_text), path
                )
            )
            assert all(
                item is None
                for _, item in result.iter_stage_results()
            )


def _assert_marks(project_container) -> None:
    """採点結果の保存状態を確認する。"""
    for student_id_text, score in SCORES.items():
        mark = project_container.student_mark_get_usecase.execute(
            StudentID(student_id_text)
        )
        assert mark.is_marked is (score is not None)
        if score is not None:
            assert mark.score == score


def _export_and_assert_scores(
    app_container,
    project_container,
    excel_path: Path,
) -> None:
    """Excelエクスポートとバックアップを検証する。"""
    # 実際の採点表には触れず、テスト用Excelを作成する。
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = "scores"
    worksheet.append(["# 学籍番号", "# 氏名", "# 合計点", "問1"])

    for student_id_text, (name, _) in STUDENT_INFO.items():
        worksheet.append([student_id_text, name, None, None])

    workbook.save(excel_path)
    workbook.close()

    marks = project_container.student_mark_list_usecase.execute()
    assert {
        str(mark.student_id)
        for mark in marks
    } == set(STUDENT_INFO)

    stats = app_container.score_excel_list_worksheet_stats_usecase.execute(
        excel_fullpath=excel_path,
        student_ids=[StudentID(s) for s in STUDENT_INFO],
    )
    assert len(stats) == 1
    assert stats[0].name == "scores"
    assert stats[0].valid

    assert not app_container.score_excel_has_data_usecase.execute(
        excel_fullpath=excel_path,
        worksheet_name="scores",
        student_ids=[StudentID(s) for s in STUDENT_INFO],
        target_id=TargetID(1),
    )

    backup_path = app_container.score_excel_apply_usecase.execute(
        excel_fullpath=excel_path,
        worksheet_name="scores",
        student_marks=marks,
        target_id=TargetID(1),
        do_backup=True,
    )
    assert backup_path is not None
    assert backup_path.is_file()

    # バックアップは書き込み前の空欄状態。
    before = openpyxl.load_workbook(backup_path)
    try:
        assert all(
            before["scores"].cell(row=r, column=4).value is None
            for r in range(2, 7)
        )
    finally:
        before.close()

    # 書き込み後のExcelに期待得点が入っている。
    after = openpyxl.load_workbook(excel_path)
    try:
        for row, (student_id_text, score) in enumerate(
            SCORES.items(), start=2
        ):
            assert (
                after["scores"].cell(row=row, column=1).value
                == student_id_text
            )
            assert (
                after["scores"].cell(row=row, column=4).value
                == score
            )
    finally:
        after.close()


def test_grading_workflow_msvc(
    app_container_factory,
    archive_path,
    tmp_path,
    development_compiler_tool_fullpath: Path,
) -> None:
    """提出ZIPから採点・出力・再オープンまでのスモークテストを実行する。"""
    _report(f"compiler={development_compiler_tool_fullpath!s}")
    debug_settings = DebugSettings(
        compiler_tool_fullpath=development_compiler_tool_fullpath,
    )
    app_container = app_container_factory(
        debug_settings=debug_settings
    )

    # 1. プロジェクト作成・初期化。
    project_id = app_container.project_create_usecase.execute(
        project_name="grading_smoke_test",
        target_number=1,
        zip_name=ARCHIVE_NAME,
    )
    app_container.project_open_usecase.execute(project_id)
    project_container = app_container.create_project_container(project_id)

    initialized = (
        project_container.current_project_initialize_static_usecase.execute(
            manaba_report_archive_fullpath=archive_path(ARCHIVE_NAME),
        )
    )
    assert not initialized.has_error, initialized.message
    _assert_project_students(project_container)
    _report(f"project initialized: archive={ARCHIVE_NAME} students={len(STUDENT_INFO)}")

    # 2. テストケース設定。
    _configure_testcases(project_container)
    _report("test cases configured: case_yes, case_no")

    # 3. ソース抽出・コンパイル・実行・テスト。
    _report("first grading run started")
    for student_id_text in STUDENT_INFO:
        project_container.student_run_next_stage_usecase.execute(
            student_id=StudentID(student_id_text),
            stop_producer=lambda: False,
        )
    _assert_stage_results(project_container)
    _report("first grading run verified")

    # 4. クリア。
    for student_id_text in STUDENT_INFO:
        project_container.student_stage_result_clear_usecase.execute(
            student_id=StudentID(student_id_text),
            stop_producer=lambda: False,
        )
    _assert_cleared(project_container)
    _report("stage results cleared and verified")

    # 5. 再実行。
    _report("second grading run started")
    for student_id_text in STUDENT_INFO:
        project_container.student_run_next_stage_usecase.execute(
            student_id=StudentID(student_id_text),
            stop_producer=lambda: False,
        )
    _assert_stage_results(project_container)
    _report("second grading run verified")

    # 6. 採点保存・再読み込み。
    for student_id_text, score in SCORES.items():
        project_container.student_mark_put_usecase.execute(
            StudentMark(
                student_id=StudentID(student_id_text),
                score=score,
            )
        )
    _assert_marks(project_container)
    _report(f"marks saved and verified: {SCORES}")

    # 7. Excelエクスポート。
    _export_and_assert_scores(
        app_container,
        project_container,
        tmp_path / "scores.xlsx",
    )
    _report("score Excel export and backup verified")

    # 8. 新しいコンテナからプロジェクトを開き直す。
    reopened_app = app_container_factory(
        debug_settings=debug_settings
    )
    reopened_app.project_open_usecase.execute(project_id)
    reopened = reopened_app.create_project_container(project_id)

    _assert_project_students(reopened)
    assert {
        str(x)
        for x in reopened.testcase_config_list_id_usecase.execute()
    } == {"case_yes", "case_no"}
    _assert_stage_results(reopened)
    _assert_marks(reopened)
    _report("project reopened and persisted results verified")
    _report("smoke test completed successfully")
