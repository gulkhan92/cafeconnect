from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.embeddings import embed_text
from app.models.menu import MenuItem


async def search_menu_items(
    db: AsyncSession, query: str, limit: int = 5
) -> list[tuple[MenuItem, float]]:
    """Semantic search over menu items. Returns (item, cosine_similarity) pairs, best first.

    This is the retrieval step both the public /menu/search endpoint and the
    chatbot use, so a menu question never needs to reach an LLM: the top
    matches can usually be returned to the user directly.
    """
    query_embedding = await embed_text(query)

    distance = MenuItem.embedding.cosine_distance(query_embedding)
    result = await db.execute(
        select(MenuItem, distance.label("distance"))
        .where(MenuItem.embedding.is_not(None))
        .order_by(distance)
        .limit(limit)
    )

    return [(item, 1 - distance_value) for item, distance_value in result.all()]
