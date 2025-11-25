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
    READ = 1
    CREATE = 2
    EDIT = 3
    DELETE = 4

class PermissionsRoutes(IntEnum):
    READ = 1
    CREATE = 2
    EDIT = 3
    DELETE = 4

class PermissionsCollects(IntEnum):
    READ = 1
    CREATE = 2
    EDIT = 3
    DELETE = 4

class PermissionsBilling(IntEnum):
    READ = 1
    CREATE = 2
    EDIT = 3
    DELETE = 4

class PermissionsAudit(IntEnum):
    READ = 1