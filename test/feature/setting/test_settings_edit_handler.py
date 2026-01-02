"""
SettingEditHandlerのテスト
テスト範囲: Handler層（SettingEditHandler）
依存関係: PyQt5、UseCase層（ISettingGetUseCase、ISettingPutUseCase等）、Navigator
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from feature.setting.handler.settings_edit import SettingEditHandler
from feature.setting.handler.interface import (
    ISettingEditView,
    SettingEditDTO,
    PathNotAbsoluteError,
    PathNotExistsError,
)
from feature.setting.usecase.interface import (
    ISettingGetUseCase,
    ISettingPutUseCase,
    ITestCompileStageUseCase,
    ICompilerSearchUseCase,
)
from shared.domain.value.setting import Setting
from shared.handler.interface import INavigator


@pytest.fixture
def mock_view():
    """Viewのモック"""
    mock = MagicMock(spec=ISettingEditView)
    mock.get_parent_widget.return_value = MagicMock()
    return mock


@pytest.fixture
def mock_setting_get_usecase():
    """SettingGetUseCaseのモック"""
    return MagicMock(spec=ISettingGetUseCase)


@pytest.fixture
def mock_setting_put_usecase():
    """SettingPutUseCaseのモック"""
    return MagicMock(spec=ISettingPutUseCase)


@pytest.fixture
def mock_test_compile_stage_usecase():
    """TestCompileStageUseCaseのモック"""
    return MagicMock(spec=ITestCompileStageUseCase)


@pytest.fixture
def mock_compiler_search_usecase():
    """CompilerSearchUseCaseのモック"""
    return MagicMock(spec=ICompilerSearchUseCase)


@pytest.fixture
def mock_navigator():
    """Navigatorのモック"""
    return MagicMock(spec=INavigator)


@pytest.fixture
def sample_setting():
    """テスト用のSetting"""
    return Setting(
        compiler_tool_fullpath=Path("C:/test/path/VsDevCmd.bat"),
        compile_timeout=60.0,
        max_workers=4,
        backup_before_export=True,
        show_editing_symbols_in_stream_content=False,
        show_editing_symbols_in_source_code=False,
        enable_line_wrap_in_stream_content=False,
        enable_line_wrap_in_source_code=False,
    )


@pytest.fixture
def sample_dto():
    """テスト用のDTO"""
    return SettingEditDTO(
        compiler_tool_fullpath="C:/test/path/VsDevCmd.bat",
        compile_timeout=60.0,
        max_workers=4,
        backup_before_export=True,
        show_editing_symbols_in_stream_content=False,
        show_editing_symbols_in_source_code=False,
        enable_line_wrap_in_stream_content=False,
        enable_line_wrap_in_source_code=False,
    )


@pytest.fixture
def handler(
    mock_view,
    mock_navigator,
    mock_setting_get_usecase,
    mock_setting_put_usecase,
    mock_test_compile_stage_usecase,
    mock_compiler_search_usecase,
):
    """SettingEditHandlerのインスタンス"""
    return SettingEditHandler(
        view=mock_view,
        navigator=mock_navigator,
        setting_get_usecase=mock_setting_get_usecase,
        setting_put_usecase=mock_setting_put_usecase,
        test_compile_stage_usecase=mock_test_compile_stage_usecase,
        compiler_search_usecase=mock_compiler_search_usecase,
    )


@pytest.fixture
def compiler_existing_path(tmp_path):
    """存在するコンパイラパスのfixture"""
    path = tmp_path / "VsDevCmd.bat"
    path.touch()
    return str(path)


@pytest.fixture
def compiler_non_existing_path(tmp_path):
    """存在しないコンパイラパスのfixture"""
    path = tmp_path / "non_existent" / "VsDevCmd.bat"
    path.parent.mkdir(parents=True, exist_ok=True)
    # ファイルは作成しない（存在しない状態）
    return str(path)


@pytest.fixture
def initial_dto(tmp_path):
    """初期DTO（存在する絶対パスを含む）"""
    initial_file = tmp_path / "initial" / "VsDevCmd.bat"
    initial_file.parent.mkdir()
    initial_file.touch()
    return SettingEditDTO(
        compiler_tool_fullpath=str(initial_file),
        compile_timeout=60.0,
        max_workers=4,
        backup_before_export=True,
        show_editing_symbols_in_stream_content=False,
        show_editing_symbols_in_source_code=False,
        enable_line_wrap_in_stream_content=False,
        enable_line_wrap_in_source_code=False,
    )


@pytest.fixture
def changed_dto(tmp_path):
    """変更後のDTO（存在する絶対パスを含む）"""
    changed_file = tmp_path / "changed" / "VsDevCmd.bat"
    changed_file.parent.mkdir()
    changed_file.touch()
    return SettingEditDTO(
        compiler_tool_fullpath=str(changed_file),
        compile_timeout=90.0,
        max_workers=8,
        backup_before_export=False,
        show_editing_symbols_in_stream_content=True,
        show_editing_symbols_in_source_code=True,
        enable_line_wrap_in_stream_content=True,
        enable_line_wrap_in_source_code=True,
    )


@pytest.fixture
def invalid_dto():
    """無効なDTO（バリデーションエラー用）"""
    return SettingEditDTO(
        compiler_tool_fullpath="dummy/path",
        compile_timeout=60.0,
        max_workers=4,
        backup_before_export=True,
        show_editing_symbols_in_stream_content=False,
        show_editing_symbols_in_source_code=False,
        enable_line_wrap_in_stream_content=False,
        enable_line_wrap_in_source_code=False,
    )


def test_on_view_initialized_set_all_fields_correctly(
    handler,
    mock_view,
    mock_setting_get_usecase,
    sample_setting,
):
    """各フィールドが正しくViewに設定されているか"""
    # Setup
    mock_setting_get_usecase.execute.return_value = sample_setting

    # Execute
    handler.on_view_initialized()

    # Verify
    mock_setting_get_usecase.execute.assert_called_once()
    mock_view.set_settings.assert_called_once()
    
    # DTOが正しく設定されているか確認
    call_args = mock_view.set_settings.call_args[0][0]
    # パスは正規化して比較（Windowsではバックスラッシュになる可能性がある）
    assert Path(call_args.compiler_tool_fullpath) == Path("C:/test/path/VsDevCmd.bat")
    assert call_args.compile_timeout == 60.0
    assert call_args.max_workers == 4
    assert call_args.backup_before_export is True
    assert call_args.show_editing_symbols_in_stream_content is False
    assert call_args.show_editing_symbols_in_source_code is False
    assert call_args.enable_line_wrap_in_stream_content is False
    assert call_args.enable_line_wrap_in_source_code is False


def test_on_view_initialized_compiler_tool_fullpath_none(
    handler,
    mock_view,
    mock_setting_get_usecase,
):
    """compiler_tool_fullpathがNoneの場合"""
    # Setup
    setting = Setting(
        compiler_tool_fullpath=None,
        compile_timeout=60.0,
        max_workers=4,
        backup_before_export=True,
        show_editing_symbols_in_stream_content=False,
        show_editing_symbols_in_source_code=False,
        enable_line_wrap_in_stream_content=False,
        enable_line_wrap_in_source_code=False,
    )
    mock_setting_get_usecase.execute.return_value = setting

    # Execute
    handler.on_view_initialized()

    # Verify
    call_args = mock_view.set_settings.call_args[0][0]
    assert call_args.compiler_tool_fullpath is None


@pytest.mark.parametrize(
    [
        "compiler_tool_fullpath",
        "expected_exception",
    ],
    [
        # 例外なしのケース
        (None, None),
        ("", None),
        ("__compiler_existing_path__", None),
        # 例外が発生するケース
        ("relative/path/VsDevCmd.bat", PathNotAbsoluteError),
        ("__compiler_non_existing_path__", PathNotExistsError),
    ],
)
def test_validate_dto(
    handler,
    compiler_existing_path,
    compiler_non_existing_path,
    compiler_tool_fullpath,
    expected_exception,
):
    """DTOと例外のペアでテスト"""
    # fixtureのパスを置き換え
    if compiler_tool_fullpath == "__compiler_existing_path__":
        compiler_tool_fullpath = compiler_existing_path
    elif compiler_tool_fullpath == "__compiler_non_existing_path__":
        compiler_tool_fullpath = compiler_non_existing_path
    
    # DTOを作成
    dto = SettingEditDTO(
        compiler_tool_fullpath=compiler_tool_fullpath,
        compile_timeout=60.0,
        max_workers=4,
        backup_before_export=True,
        show_editing_symbols_in_stream_content=False,
        show_editing_symbols_in_source_code=False,
        enable_line_wrap_in_stream_content=False,
        enable_line_wrap_in_source_code=False,
    )
    
    if expected_exception is None:
        # 例外が投げられないことを確認
        handler.validate_dto(dto)
    else:
        with pytest.raises(expected_exception):
            handler.validate_dto(dto)


@pytest.mark.parametrize(
    [
        "initial_dto_name",
        "current_dto_name",
    ],
    [
        ("initial_dto", "initial_dto"),  # 変更なし
        ("initial_dto", "changed_dto"),  # 変更あり
    ],
)
def test_on_save_button_clicked_success(
    handler,
    mock_view,
    mock_setting_put_usecase,
    request,
    initial_dto_name,
    current_dto_name,
):
    """保存成功 → True（変更の有無に関わらず）"""
    # fixture名から実際のDTOを取得
    initial = request.getfixturevalue(initial_dto_name)
    current = request.getfixturevalue(current_dto_name)
    
    # Setup
    handler._initial_dto = initial
    mock_view.get_settings_dto.return_value = current
    mock_setting_put_usecase.execute.return_value = None

    # Execute
    result = handler.on_save_button_clicked()

    # Verify
    assert result is True
    mock_setting_put_usecase.execute.assert_called_once()
    # 保存されたSettingを確認
    saved_setting = mock_setting_put_usecase.execute.call_args[0][0]
    assert saved_setting.compiler_tool_fullpath == Path(current.compiler_tool_fullpath)
    assert saved_setting.compile_timeout == current.compile_timeout
    assert saved_setting.max_workers == current.max_workers
    assert saved_setting.backup_before_export == current.backup_before_export
    # エラーメッセージは表示されない（成功ケース）
    mock_view.show_validation_error.assert_not_called()


@pytest.mark.parametrize(
    [
        "exception_class",
    ],
    [
        (PathNotAbsoluteError,),
        (PathNotExistsError,),
    ],
)
def test_on_save_button_clicked_validation_failed(
    handler,
    mock_view,
    mock_setting_put_usecase,
    sample_dto,
    invalid_dto,
    exception_class,
):
    """変更あり → バリデーション失敗 → False"""
    # Setup: validate_dtoが例外を投げるようにモック
    handler._initial_dto = sample_dto
    mock_view.get_settings_dto.return_value = invalid_dto

    # Execute: validate_dtoが例外を投げるようにモック
    with patch.object(handler, 'validate_dto', side_effect=exception_class("エラーメッセージ")):
        result = handler.on_save_button_clicked()

    # Verify
    # 1. ウィンドウを閉じる命令が送られていない（Falseが返される）
    assert result is False
    
    # 2. 値が書き込まれていない（UseCaseが呼ばれていない）
    mock_setting_put_usecase.execute.assert_not_called()
    
    # 3. バリデーションエラーが表示されたか確認（Viewのメソッドが呼ばれたか）
    mock_view.show_validation_error.assert_called_once()
    # エラーメッセージ（文字列）が渡されたか確認
    call_args = mock_view.show_validation_error.call_args[0][0]
    assert isinstance(call_args, str)


@pytest.mark.parametrize(
    [
        "initial_dto_name",
        "current_dto_name",
        "confirm_result",
        "expected_result",
        "should_show_dialog",
    ],
    [
        ("sample_dto", "sample_dto", None, True, False),  # 変更なし → ダイアログなし → True
        ("sample_dto", "changed_dto", True, True, True),  # 変更あり → ダイアログでYes → True
        ("sample_dto", "changed_dto", False, False, True),  # 変更あり → ダイアログでNo → False
    ],
)
def test_on_cancel_requested(
    handler,
    mock_view,
    request,
    initial_dto_name,
    current_dto_name,
    confirm_result,
    expected_result,
    should_show_dialog,
):
    """初期DTOと現在のDTOの関係に応じて動作を確認"""
    # fixture名から実際のDTOを取得
    initial = request.getfixturevalue(initial_dto_name)
    current = request.getfixturevalue(current_dto_name)
    
    # Setup
    handler._initial_dto = initial
    mock_view.get_settings_dto.return_value = current
    if confirm_result is not None:
        mock_view.confirm_discard_changes.return_value = confirm_result

    # Execute
    result = handler.on_cancel_requested()

    # Verify
    assert result is expected_result
    if should_show_dialog:
        # 確認ダイアログが表示されたか確認（Viewのメソッドが呼ばれたか）
        mock_view.confirm_discard_changes.assert_called_once()
    else:
        # 確認ダイアログは表示されない
        mock_view.confirm_discard_changes.assert_not_called()


@pytest.mark.parametrize(
    [
        "initial_dto_name",
        "current_dto_name",
        "confirm_result",
        "expected_result",
        "should_show_dialog",
    ],
    [
        ("sample_dto", "sample_dto", None, True, False),  # 変更なし → ダイアログなし → True
        ("sample_dto", "changed_dto", True, True, True),  # 変更あり → ダイアログでYes → True
        ("sample_dto", "changed_dto", False, False, True),  # 変更あり → ダイアログでNo → False
    ],
)
def test_on_close_requested(
    handler,
    mock_view,
    request,
    initial_dto_name,
    current_dto_name,
    confirm_result,
    expected_result,
    should_show_dialog,
):
    """初期DTOと現在のDTOの関係に応じて動作を確認"""
    # fixture名から実際のDTOを取得
    initial = request.getfixturevalue(initial_dto_name)
    current = request.getfixturevalue(current_dto_name)
    
    # Setup
    handler._initial_dto = initial
    mock_view.get_settings_dto.return_value = current
    if confirm_result is not None:
        mock_view.confirm_discard_changes.return_value = confirm_result

    # Execute
    result = handler.on_close_requested()

    # Verify
    assert result is expected_result
    if should_show_dialog:
        # 確認ダイアログが表示されたか確認（Viewのメソッドが呼ばれたか）
        mock_view.confirm_discard_changes.assert_called_once()
    else:
        # 確認ダイアログは表示されない
        mock_view.confirm_discard_changes.assert_not_called()

