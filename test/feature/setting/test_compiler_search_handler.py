"""
CompilerSearchHandlerの統合テスト
テスト範囲: Handler層（CompilerSearchHandler）+ UseCase層（CompilerSearchUseCase）+ Gateway層（VSFindCompilerPathGateway）+ ファイルシステム
依存関係: PyQt5（QThread、シグナル）、ファイルシステム
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from feature.setting.handler.compiler_search_handler import CompilerSearchHandler
from feature.setting.handler.interface import ICompilerSearchView
from feature.setting.usecase.compiler_search import CompilerSearchUseCase
from feature.setting.infra.gateway.compiler_location import VSFindCompilerPathGateway
from feature.setting.domain.interface.gateway import IFindCompilerPathGateway


def create_fake_environment(tmp_path, has_correct_files: bool = True) -> list[Path]:
    """テスト用の一時ディレクトリに検索対象のファイル構造を作成（正解ファイル2個）"""
    correct_files = []

    for folder_idx in range(1, 3):
        folder = tmp_path / f"folder{folder_idx}"

        for subfolder_idx in range(1, 4):
            subfolder = folder / f"subfolder{subfolder_idx}"
            subfolder.mkdir(parents=True)

            files_per_subfolder = 100
            for file_idx in range(files_per_subfolder):
                file_path = subfolder / f"file_{file_idx:03d}.txt"
                file_path.touch()

            if has_correct_files:
                if folder_idx == 1 and subfolder_idx == 1:
                    correct_file = subfolder / "VsDevCmd.bat"
                    correct_file.touch()
                    correct_files.append(correct_file)
                elif folder_idx == 2 and subfolder_idx == 1:
                    correct_file = subfolder / "VsDevCmd.bat"
                    correct_file.touch()
                    correct_files.append(correct_file)

    if has_correct_files:
        assert len(correct_files) == 2
    else:
        assert len(correct_files) == 0
    return correct_files


@pytest.fixture
def mock_view():
    mock = MagicMock(spec=ICompilerSearchView)
    mock.get_parent_widget.return_value = None
    return mock


@pytest.fixture
def gateway_with_test_path(tmp_path):
    return VSFindCompilerPathGateway(start_locations=[tmp_path])


def test_compiler_search_integration(qtbot, tmp_path, mock_view, gateway_with_test_path):
    """Handler -> UseCase -> Gateway -> FileSystem を一気通貫でテスト"""
    correct_files = create_fake_environment(tmp_path)

    gateway = gateway_with_test_path
    usecase = CompilerSearchUseCase(find_compiler_path_gateway=gateway)
    handler = CompilerSearchHandler(
        view=None,
        compiler_search_usecase=usecase,
    )
    handler.set_view(mock_view)

    handler.on_view_initialized()

    with qtbot.waitSignal(handler._search_worker.progress_finished, timeout=10000) as blocker:
        pass

    found_paths = blocker.args[0]

    assert len(found_paths) >= 2
    for correct_file in correct_files:
        assert correct_file in found_paths

    mock_view.show_path_selection.assert_called_once()
    assert mock_view.set_progress_text.call_count > 0
    mock_view.accept_dialog.assert_called_once()


def test_compiler_search_not_found(qtbot, tmp_path, mock_view):
    """コンパイラが見つからない場合のテスト"""
    create_fake_environment(tmp_path, has_correct_files=False)

    gateway = VSFindCompilerPathGateway(start_locations=[tmp_path])
    usecase = CompilerSearchUseCase(find_compiler_path_gateway=gateway)
    handler = CompilerSearchHandler(
        view=None,
        compiler_search_usecase=usecase,
    )
    handler.set_view(mock_view)

    handler.on_view_initialized()
    assert handler._search_worker is not None

    with qtbot.waitSignal(handler._search_worker.progress_finished, timeout=10000) as blocker:
        pass

    found_paths = blocker.args[0]
    assert len(found_paths) == 0

    mock_view.show_not_found_message.assert_called_once()
    mock_view.accept_dialog.assert_called_once()
    mock_view.show_path_selection.assert_not_called()


def test_compiler_search_cancelled(qtbot, mock_view):
    """検索が中断された場合のテスト"""
    # 無限ループするGatewayのモックを作成
    mock_gateway = MagicMock(spec=IFindCompilerPathGateway)
    mock_gateway.reset.return_value = None
    mock_gateway.has_next.return_value = True  # 常にTrueを返して無限ループ
    mock_gateway.search_next.return_value = []  # 見つからないがループは続く
    mock_gateway.get_current_dir.return_value = Path("C:/test/path")

    usecase = CompilerSearchUseCase(find_compiler_path_gateway=mock_gateway)
    handler = CompilerSearchHandler(
        view=None,
        compiler_search_usecase=usecase,
    )
    handler.set_view(mock_view)

    handler.on_view_initialized()
    assert handler._search_worker is not None

    # 検索が進行中であることを確認（progress_updatedシグナルを受信）
    with qtbot.waitSignal(handler._search_worker.progress_updated, timeout=10000):
        pass

    # progress_finishedシグナルを待機
    with qtbot.waitSignal(handler._search_worker.progress_finished, timeout=10000):
        # 検索が進行中であることが確認できたので、中断する
        handler.on_close_requested()

    mock_view.accept_dialog.assert_called_once()
