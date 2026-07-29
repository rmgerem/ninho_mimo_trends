from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ninho_mimo_trends.models.customer import Customer


class CustomerRepository:
    """Repositorio para acessar dados dos clientes."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, customer: Customer) -> Customer:
        self.session.add(customer)
        return customer

    def get_by_grafana_username(self, username: str) -> Customer | None:
        return self.session.scalar(select(Customer).where(Customer.grafana_username == username))
