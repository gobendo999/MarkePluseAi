from django.db import migrations
from django.contrib.postgres.operations import TrigramExtension, BtreeGinExtension, UnaccentExtension


class Migration(migrations.Migration):
    """
    Topic 18: Enable PostgreSQL native extensions for:
    1. TrigramExtension: Typo-tolerant fuzzy string matching (pg_trgm)
    2. BtreeGinExtension: Fast multi-column GIN index creation (btree_gin)
    3. UnaccentExtension: Accent-insensitive text search (unaccent)
    """

    dependencies = [
        ('products', '0002_pricehistory_currency_product_currency'),
    ]

    operations = [
        TrigramExtension(),
        BtreeGinExtension(),
        UnaccentExtension(),
    ]
