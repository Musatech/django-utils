from enum import IntEnum

# ====== MÓDULOS ======

class Modules(IntEnum):
    USERS = 1
    ROUTES = 2
    COLLECTS = 3
    BILLING = 4
    AUDIT = 5


# ====== PERMISSÕES POR MÓDULO ======

class PermissionsUsers(IntEnum):
    ALL = 1
    READ = 2
    CREATE = 3
    EDIT = 4
    DELETE = 5


class PermissionsRoutes(IntEnum):
    ALL = 1
    READ = 2
    CREATE = 3
    EDIT = 4
    DELETE = 5

class PermissionsCollects(IntEnum):
    ALL = 1
    READ = 2
    CREATE = 3
    EDIT = 4
    DELETE = 5

class PermissionsBilling(IntEnum):
    ALL = 1
    READ = 2
    CREATE = 3
    EDIT = 4
    DELETE = 5

class PermissionsAudit(IntEnum):
    READ = 1