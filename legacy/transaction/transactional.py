# transactional_withに要求する機能
# @transactional_with(
#    # local-lock: mode=LockMode.READONLY, id_type=type(args["student_id"]), id_value=args["student_id"]
#    readonly("student_id"),
#    # local-lock: mode=LockMode.READONLY, id_type=type(λ()), id_value=λ()
#    readonly(lambda args: args["student"].student_id),
#    # global-lock: mode=LockMode.READONLY, id_type=type(StudentID), id_value=None
#    readonly(StudentID),
#    # local-lock: mode=LockMode.WRITABLE, id_type=type(args["student_id"]), id_value=args["student_id"]
#    writable("student_id"),
#    # local-lock: mode=LockMode.WRITABLE, id_type=type(λ()), id_value=λ()
#    writable(lambda args: args["student"].student_id),
#    # global-lock: mode=LockMode.WRITABLE, id_type=type(StudentID), id_value=None
#    writable(StudentID),
# )
import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import wraps, cache
from typing import Callable, Any, Hashable

from transaction.common import ResourceIDType, LockRequest
from transaction.resource_lock_server import LockMode, LockTicket, get_lock_server_factory

ResourceIDLocatorParamType = str | type[ResourceIDType] | Callable[[dict], ResourceIDType]


@dataclass(frozen=True)
class NamedFuncArgs:
    mapping: tuple[tuple[str, Hashable], ...]

    @classmethod
    def from_dict(cls, arg_dct: dict[str, Hashable]):
        return cls(
            mapping=tuple(arg_dct.items()),
        )

    def __getitem__(self, arg_name: str) -> Any:
        for name, value in self.mapping:
            if name == arg_name:
                return value
        raise KeyError(f"Argument '{arg_name}' not found in function arguments")


def __name_func_args(fn, args, kwargs) -> NamedFuncArgs:
    fn_signature = inspect.signature(fn)
    bound_args = fn_signature.bind(*args, **kwargs)
    bound_args.apply_defaults()
    return NamedFuncArgs.from_dict(bound_args.arguments)


class AbstractResourceIDLocator(ABC):
    def __init__(self, param: ResourceIDLocatorParamType):
        self._param = param

    @abstractmethod
    def _get_mode(self) -> LockMode:
        raise NotImplementedError()

    @cache
    def _get_id_type_and_value(self, func_args: NamedFuncArgs) \
            -> tuple[type[ResourceIDType], ResourceIDType | None]:
        if isinstance(self._param, str):
            id_value = func_args[self._param]
            return type(id_value), id_value
        elif isinstance(self._param, type) and issubclass(self._param, ResourceIDType):
            id_value_type = self._param
            return id_value_type, None
        elif callable(self._param):
            id_value = self._param(func_args)
            return type(id_value), id_value
        else:
            raise ValueError(f"Invalid id-locator: {self._param}")

    def get_id_type(self, func_args: NamedFuncArgs) -> type[ResourceIDType]:
        return self._get_id_type_and_value(func_args)[0]

    def get_lock_request(self, func_args: NamedFuncArgs) -> LockRequest:
        return LockRequest(
            mode=self._get_mode(),
            id_value=self._get_id_type_and_value(func_args)[1],
        )


class ReadonlyIDLocator(AbstractResourceIDLocator):
    def _get_mode(self) -> LockMode:
        return LockMode.READONLY


readonly = ReadonlyIDLocator


class WritableIDLocator(AbstractResourceIDLocator):
    def _get_mode(self) -> LockMode:
        return LockMode.WRITABLE


writable = WritableIDLocator


def __acquire_resources(id_locators: list[AbstractResourceIDLocator], func_args) \
        -> list[LockTicket]:
    lock_tickets = []
    for id_locator in id_locators:
        id_type = id_locator.get_id_type(func_args)
        req = id_locator.get_lock_request(func_args)
        lock_ticket = get_lock_server_factory(id_type).lock(req)
        lock_tickets.append(lock_ticket)
    return lock_tickets


def __release_resources(lock_tickets: list[LockTicket]) -> None:
    for lock_ticket in lock_tickets:



def transactional_with(*id_locators: AbstractResourceIDLocator):
    assert isinstance(id_locators, AbstractResourceIDLocator)

    def decorator(f: Callable):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # スタックフレームに侵入
            #  - セッションIDを取得
            #  - トランザクションを
            #  - トランザクション
            # リソースをロック

            try:
                return f(*args, **kwargs)
            finally:
                # スタックフレームを抜け出す
                pass

        return wrapper

    return decorator
