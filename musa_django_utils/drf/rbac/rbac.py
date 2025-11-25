# core/rbac.py
from enum import IntEnum
from dataclasses import dataclass
from typing import Iterable, Dict, List, Any

from .permissions import Modules


# ====== SPEC USADO PELA VIEW ======

@dataclass(frozen=True)
class PermissionSpec:
    """
    Representa uma "regra" de acesso:
    - module: Modules.USER, Modules.VEHICLES, etc.
    - permissions: lista de permissões deste módulo (OR entre elas)
    """
    module: Modules
    permissions: Iterable[IntEnum]


# ====== FUNÇÕES DE CHECAGEM ======

def _get_module_permissions_from_payload(
        payload_permissions: Dict[Any, List[int]],
        module: Modules,
) -> List[int]:
    """
    Pega a lista de permissões do usuário para um módulo específico
    do payload, tratando chave como string ou int.
    """
    module_id_str = str(int(module))
    module_id_int = int(module)

    return (
            payload_permissions.get(module_id_str)
            or payload_permissions.get(module_id_int)
            or []
    )


def user_has_permission_for_spec(
        payload_permissions: Dict[Any, List[int]],
        spec: PermissionSpec,
) -> bool:
    """
    Retorna True se o usuário atender a UMA spec:
    - Se tiver permissão ALL (id 1) para o módulo, libera tudo
    - Senão, se tiver QUALQUER uma das permissions listadas na spec (OR)
    """
    user_perms = set(_get_module_permissions_from_payload(payload_permissions, spec.module))

    if not user_perms:
        return False

    # 1 = ALL em todos os módulos, pelo seu design
    if 1 in user_perms:
        return True

    required_ids = {int(p) for p in spec.permissions}
    return bool(required_ids & user_perms)  # interseção não vazia = pelo menos 1 permisão


def user_has_any_of_specs(
        payload_permissions: Dict[Any, List[int]],
        specs: Iterable[PermissionSpec],
) -> bool:
    """
    Considera OR entre múltiplas specs:
    - Se atender qualquer uma das specs, retorna True.
      Ex: spec1 (USER.READ) OR spec2 (VEHICLE.READ)
    """
    return any(user_has_permission_for_spec(payload_permissions, spec) for spec in specs)
