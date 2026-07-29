from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, text
from sqlalchemy.orm import Mapped, mapped_column

from ninho_mimo_trends.models.base import Base


class Customer(Base):
    """Representa um cliente/afiliado que assina a plataforma."""

    __tablename__ = "tb_customers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    grafana_username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    shopee_app_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    shopee_app_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("TIMEZONE('utc', CURRENT_TIMESTAMP)")
    )
