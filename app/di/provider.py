from functools import cache

from app.di.path_config import get_global_path_provider
from app.di.system import get_global_core_io
from shared.infra.provider.app_name import StaticAppNameProvider
from shared.infra.provider.app_version import JsonAppVersionProvider


@cache
def get_app_name_provider():
    """アプリケーション名プロバイダーを取得"""
    return StaticAppNameProvider()


@cache
def get_app_version_provider():
    """アプリケーションバージョンプロバイダーを取得"""
    return JsonAppVersionProvider(
        global_path_provider=get_global_path_provider(),
        global_core_io=get_global_core_io(),
    )
