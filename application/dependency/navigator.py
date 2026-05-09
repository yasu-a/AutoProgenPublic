from functools import cache

from control.interface_navigator import INavigator


@cache
def get_navigator() -> INavigator:
    from control.navigator import Navigator
    return Navigator()
