"""Comando de seed: popula categorias, faixas etarias e fontes iniciais."""

from __future__ import annotations

from ninho_mimo_trends.configuration.json_loader import load_json_config
from ninho_mimo_trends.database.unit_of_work import UnitOfWork
from ninho_mimo_trends.enums.source_status import SourceType


def run_seed() -> dict[str, int]:
    """Popula o banco com categorias, faixas etarias e fontes (idempotente).

    Seguro para ser executado multiplas vezes: usa ``get_or_create`` em
    todos os repositorios, portanto nunca duplica registros.
    """
    categories_config = load_json_config("categories.json")
    sources_config = load_json_config("sources.json")

    created = {"categories": 0, "age_ranges": 0, "sources": 0}

    with UnitOfWork() as uow:
        for category_data in categories_config["categories"]:
            parent, parent_created = uow.categories.get_or_create(
                slug=category_data["slug"], name=category_data["name"]
            )
            created["categories"] += int(parent_created)
            for child_data in category_data.get("children", []):
                _, child_created = uow.categories.get_or_create(
                    slug=child_data["slug"], name=child_data["name"], parent_id=parent.id
                )
                created["categories"] += int(child_created)

        for age_range_data in categories_config["age_ranges"]:
            _, age_range_created = uow.age_ranges.get_or_create(
                code=age_range_data["code"],
                defaults={
                    "name": age_range_data["name"],
                    "minimum_age_months": age_range_data["minimum_age_months"],
                    "maximum_age_months": age_range_data["maximum_age_months"],
                    "is_pregnancy": age_range_data["is_pregnancy"],
                },
            )
            created["age_ranges"] += int(age_range_created)

        for source_data in sources_config["sources"]:
            _, source_created = uow.sources.get_or_create(
                code=source_data["code"],
                defaults={
                    "name": source_data["name"],
                    "base_url": source_data["base_url"],
                    "country": source_data["country"],
                    "source_type": SourceType(source_data["source_type"]),
                    "is_active": source_data["is_active"],
                    "requires_authentication": source_data["requires_authentication"],
                    "collection_interval_minutes": source_data["collection_interval_minutes"],
                    "terms_url": source_data["terms_url"],
                },
            )
            created["sources"] += int(source_created)

        uow.commit()

    return created
