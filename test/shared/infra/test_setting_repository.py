"""
SettingRepositoryのテスト
テスト範囲: Domain層（Setting Value Object）+ Repository層（SettingRepository）
依存関係: GlobalCoreIO、ファイルシステム
"""
import pytest
from pathlib import Path

from shared.domain.value.setting import Setting
from shared.infra.repository.setting import SettingRepository
from shared.infra.system.global_core_io import GlobalCoreIO


@pytest.fixture
def setting_repository(tmp_path):
    """テスト用のSettingRepository（一時ファイルを使用）"""
    settings_json_path = tmp_path / "settings.json"
    return SettingRepository(
        settings_json_fullpath=settings_json_path,
        global_core_io=GlobalCoreIO(),
    )


def test_get_default_when_file_not_exists(setting_repository):
    """ファイルが存在しない場合、get()はデフォルトのSettingを返す"""
    setting = setting_repository.get()
    
    # デフォルトのSettingと比較
    default_setting = Setting.create_default()
    assert setting == default_setting


def test_put_and_get(setting_repository):
    """put()してget()すると、保存したSettingが取得できる"""
    # テスト用のSettingを作成
    test_setting = Setting(
        compiler_tool_fullpath=Path("C:/test/path/to/VsDevCmd.bat"),
        compile_timeout=120.0,
        max_workers=8,
        backup_before_export=False,
        show_editing_symbols_in_stream_content=True,
        show_editing_symbols_in_source_code=True,
        enable_line_wrap_in_stream_content=True,
        enable_line_wrap_in_source_code=True,
    )
    
    # 保存
    setting_repository.put(test_setting)
    
    # 取得
    retrieved_setting = setting_repository.get()
    
    # 比較
    assert retrieved_setting == test_setting


def test_get_caches_result(setting_repository):
    """get()は内部キャッシュを使用する（同じインスタンスを返す）"""
    setting1 = setting_repository.get()
    setting2 = setting_repository.get()
    
    # キャッシュされているため、同じインスタンスを返す
    assert setting1 is setting2


def test_put_clears_cache(setting_repository):
    """put()後、get()は新しい値を返す"""
    # 初期値を取得
    initial_setting = setting_repository.get()
    
    # 新しい値を保存
    new_setting = Setting(
        compiler_tool_fullpath=Path("C:/new/path/VsDevCmd.bat"),
        compile_timeout=180.0,
        max_workers=16,
        backup_before_export=True,
        show_editing_symbols_in_stream_content=False,
        show_editing_symbols_in_source_code=False,
        enable_line_wrap_in_stream_content=False,
        enable_line_wrap_in_source_code=False,
    )
    setting_repository.put(new_setting)
    
    # 新しい値が取得できる
    retrieved_setting = setting_repository.get()
    assert retrieved_setting == new_setting
    assert retrieved_setting != initial_setting


def test_put_and_get_multiple_times(setting_repository):
    """複数回put()とget()を繰り返しても正しく動作する"""
    settings = [
        Setting(
            compiler_tool_fullpath=Path(f"C:/test/path{i}/VsDevCmd.bat"),
            compile_timeout=60.0 + i * 10,
            max_workers=4 + i,
            backup_before_export=i % 2 == 0,
            show_editing_symbols_in_stream_content=i % 2 == 1,
            show_editing_symbols_in_source_code=i % 2 == 0,
            enable_line_wrap_in_stream_content=i % 2 == 1,
            enable_line_wrap_in_source_code=i % 2 == 0,
        )
        for i in range(5)
    ]
    
    for test_setting in settings:
        setting_repository.put(test_setting)
        retrieved_setting = setting_repository.get()
        assert retrieved_setting == test_setting

