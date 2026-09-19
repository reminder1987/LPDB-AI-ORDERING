from enum import Enum


class Role(str, Enum):
    """
    Roles administrativos disponibles dentro de un tenant.
    """

    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    VIEWER = "viewer"


class Permission(str, Enum):
    """
    Permisos administrativos disponibles en la plataforma.
    """

    VIEW_DASHBOARD = "view_dashboard"

    VIEW_ORDERS = "view_orders"
    VIEW_CUSTOMERS = "view_customers"
    VIEW_CATALOG = "view_catalog"
    VIEW_LOCATIONS = "view_locations"

    MANAGE_CATALOG = "manage_catalog"
    MANAGE_AVAILABILITY = "manage_availability"
    MANAGE_ORDERS = "manage_orders"

    MANAGE_LOCATIONS = "manage_locations"
    MANAGE_INTEGRATIONS = "manage_integrations"
    MANAGE_CHANNELS = "manage_channels"

    MANAGE_USERS = "manage_users"
    ASSIGN_ROLES = "assign_roles"

    MANAGE_BUSINESS_SETTINGS = "manage_business_settings"

    MANAGE_TENANT = "manage_tenant"
    TRANSFER_OWNERSHIP = "transfer_ownership"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.OWNER: frozenset(
        Permission,
    ),

    Role.ADMIN: frozenset(
        {
            Permission.VIEW_DASHBOARD,
            Permission.VIEW_ORDERS,
            Permission.VIEW_CUSTOMERS,
            Permission.VIEW_CATALOG,
            Permission.VIEW_LOCATIONS,
            Permission.MANAGE_CATALOG,
            Permission.MANAGE_AVAILABILITY,
            Permission.MANAGE_ORDERS,
            Permission.MANAGE_LOCATIONS,
            Permission.MANAGE_INTEGRATIONS,
            Permission.MANAGE_CHANNELS,
            Permission.MANAGE_USERS,
            Permission.ASSIGN_ROLES,
            Permission.MANAGE_BUSINESS_SETTINGS,
        }
    ),

    Role.MANAGER: frozenset(
        {
            Permission.VIEW_DASHBOARD,
            Permission.VIEW_ORDERS,
            Permission.VIEW_CUSTOMERS,
            Permission.VIEW_CATALOG,
            Permission.VIEW_LOCATIONS,
            Permission.MANAGE_CATALOG,
            Permission.MANAGE_AVAILABILITY,
            Permission.MANAGE_ORDERS,
        }
    ),

    Role.VIEWER: frozenset(
        {
            Permission.VIEW_DASHBOARD,
            Permission.VIEW_ORDERS,
            Permission.VIEW_CUSTOMERS,
            Permission.VIEW_CATALOG,
            Permission.VIEW_LOCATIONS,
        }
    ),
}


def role_has_permission(
    role: str | Role,
    permission: Permission,
) -> bool:
    """
    Determina si un rol posee un permiso determinado.
    """

    try:
        normalized_role = Role(role)
    except ValueError:
        return False

    return permission in ROLE_PERMISSIONS.get(
        normalized_role,
        frozenset(),
    )