from util.app_logging import create_logger

_logger = create_logger()


def invalidate_cached_providers():
    from . import cache
    from . import core_io
    from . import external_io
    from . import path_provider
    from . import repository
    from . import service
    from . import task
    from . import usecase

    modules = [
        cache,
        core_io,
        external_io,
        path_provider,
        repositories,
        services,
        tasks,
        usecases,
    ]

    cached_providers = []
    for module in modules:
        for name in dir(module):
            func = getattr(module, name)
            if not callable(func):
                continue
            if func.__module__ != module.__name__:
                continue
            if not name.startswith("get_"):
                continue
            if not hasattr(func, "cache_info"):
                continue
            cached_providers.append(func)

    for cached_provider in cached_providers:
        cached_provider.cache_clear()

    _logger.info(
        "Provider cache invalidated: \n" + "\n".join(
            map(lambda x: f" - {x.__module__}.{x.__name__}()", cached_providers)
        )
    )
