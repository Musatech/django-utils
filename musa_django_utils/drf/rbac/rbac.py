from enum import IntEnum
from dataclasses import dataclass
from typing import Iterable

from .permissions import Modules
from typing import TypedDict, List


class PermCheckResult(TypedDict):
    status: bool
    missing: List[str]


@dataclass(frozen=True)
class PermissionSpec:
    """
    Representa uma "regra" de acesso:
    - module: Modules.USER, Modules.VEHICLES, etc.
    - permissions: lista de permissões deste módulo (OR entre elas)
    """
    module: Modules
    permissions: Iterable[IntEnum]


def user_has_specs(
        payload_permissions: List[str],
        specs: Iterable[PermissionSpec],
) -> PermCheckResult:
    req_specs = parse_req_specs(specs)
    result = has_all_required_perms(req_specs, payload_permissions)

    return result

def parse_req_specs(specs: Iterable[PermissionSpec]) -> list[str]:
    req_specs = []
    for spec in specs:
        for perm in spec.permissions:
            req_specs.append(
                str(spec.module) + ':' + str(perm)
            )

    return req_specs

def has_all_required_perms(
        required: list[str],
        user: list[str]
) -> PermCheckResult:
    status = True
    user_set = set(user)
    missing = [p for p in required if p not in user_set]

    if missing:
        status = False

    return {
        "status": status,
        "missing": missing,
    }