import inspect
from functools import wraps
from typing import TypeVar, Callable

from transaction.common import TransactionID
from transaction.session_manager import ResourceID, sess_man as _sess_man
from transaction.transaction_manager import tx_man as _tx_man

_C = TypeVar("_C", bound=Callable)


def _get_current_transaction_id() -> TransactionID:
    tx_id = _tx_man.get_current()
    if tx_id is None:
        raise ValueError("Transaction not entered")
    return tx_id


def _release_all_resources() -> None:
    current_tx_id = _get_current_transaction_id()
    _sess_man.release_all_resources(current_tx_id)


def acquire(resource_id: ResourceID) -> None:
    current_tx_id = _get_current_transaction_id()
    _sess_man.acquire_resource(current_tx_id, resource_id)


def transactional(fn: _C) -> _C:
    return fn

    _tx_man.put_transactional(fn)

    @wraps(fn)
    def wrapper(*args, **kwargs):
        _tx_man.put_transactional(fn)
        try:
            return fn(*args, **kwargs)
        finally:
            _release_all_resources()
            _tx_man.leave_transactional(fn)

    return wrapper


def transactional_with(*arg_names, **arg_mappers) -> Callable[[_C], _C]:
    def decorator(fn: _C) -> _C:
        return fn

        @transactional
        @wraps(fn)
        def wrapper(*args, **kwargs):
            fn_signature = inspect.signature(fn)
            bound_args = fn_signature.bind(*args, **kwargs)
            bound_args.apply_defaults()
            # acquire resources directly referred by arg_names
            for arg_name in arg_names:
                arg_value = bound_args.arguments[arg_name]
                acquire(arg_value)
            # acquire resources referred by arg_mappers
            for arg_name, arg_mapper in arg_mappers.items():
                mapped_value = arg_mapper(bound_args.arguments)
                acquire(mapped_value)
            return fn(*args, **kwargs)

        return wrapper

    return decorator
