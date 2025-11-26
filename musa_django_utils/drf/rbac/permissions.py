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
    CREATE = 1
    READ = 2
    UPDATE = 3
    DELETE = 4

class PermissionsRoutes(IntEnum):
    CREATE = 1
    READ = 2
    UPDATE = 3
    DELETE = 4

class PermissionsCollects(IntEnum):
    CREATE = 1
    READ = 2
    UPDATE = 3
    DELETE = 4

class PermissionsBilling(IntEnum):
    CREATE = 1
    READ = 2
    UPDATE = 3
    DELETE = 4

class PermissionsAudit(IntEnum):
    READ = 1