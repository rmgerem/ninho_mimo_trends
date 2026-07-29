from enum import StrEnum


class CustomerRole(StrEnum):
    """Nivel de acesso do usuario associado ao Grafana."""

    ADMIN = "admin"
    CUSTOMER = "customer"
