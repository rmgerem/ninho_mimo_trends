"""Pacote de modelos SQLAlchemy do dominio Ninho & Mimo Trends."""

from ninho_mimo_trends.models.age_range import AgeRange
from ninho_mimo_trends.models.base import Base
from ninho_mimo_trends.models.category import Category
from ninho_mimo_trends.models.collection_error import CollectionError
from ninho_mimo_trends.models.collection_run import CollectionRun
from ninho_mimo_trends.models.customer import Customer
from ninho_mimo_trends.models.external_product_signal import ExternalProductSignal
from ninho_mimo_trends.models.product import Product
from ninho_mimo_trends.models.product_click import ProductClick
from ninho_mimo_trends.models.product_history import ProductHistory
from ninho_mimo_trends.models.product_indication import ProductIndication
from ninho_mimo_trends.models.product_score import ProductScore
from ninho_mimo_trends.models.product_source import ProductSource
from ninho_mimo_trends.models.publication_status import PublicationStatus
from ninho_mimo_trends.models.source import Source

__all__ = [
    "Base",
    "AgeRange",
    "Category",
    "CollectionError",
    "CollectionRun",
    "ExternalProductSignal",
    "Product",
    "ProductClick",
    "ProductHistory",
    "ProductIndication",
    "ProductScore",
    "ProductSource",
    "PublicationStatus",
    "Source",
    "Customer",
]
