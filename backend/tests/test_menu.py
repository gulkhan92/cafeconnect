import pytest

from tests.conftest import get_access_token

pytestmark = pytest.mark.asyncio


async def _create_item(client, staff_headers, **overrides):
    payload = {
        "category_id": overrides.pop("category_id"),
        "name": overrides.pop("name", "Cappuccino"),
        "description": overrides.pop("description", "Rich espresso with steamed milk foam"),
        "price": overrides.pop("price", "4.50"),
        "is_available": overrides.pop("is_available", True),
    }
    return await client.post("/menu/items", json=payload, headers=staff_headers)


async def test_list_menu_returns_categories_with_nested_items(
    client, staff_user, sample_category
):
    staff_headers = {"Authorization": f"Bearer {await get_access_token(client, staff_user)}"}
    await _create_item(client, staff_headers, category_id=str(sample_category.id))

    response = await client.get("/menu")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "Beverages"
    assert len(body[0]["items"]) == 1
    assert body[0]["items"][0]["name"] == "Cappuccino"


async def test_create_menu_item_requires_staff_role(client, customer_user, sample_category):
    customer_headers = {
        "Authorization": f"Bearer {await get_access_token(client, customer_user)}"
    }
    response = await _create_item(client, customer_headers, category_id=str(sample_category.id))
    assert response.status_code == 403


async def test_create_menu_item_generates_embedding(client, staff_user, sample_category):
    staff_headers = {"Authorization": f"Bearer {await get_access_token(client, staff_user)}"}
    response = await _create_item(client, staff_headers, category_id=str(sample_category.id))
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Cappuccino"
    assert "embedding" not in body


async def test_search_menu_finds_semantically_similar_item(client, staff_user, sample_category):
    staff_headers = {"Authorization": f"Bearer {await get_access_token(client, staff_user)}"}
    await _create_item(
        client,
        staff_headers,
        category_id=str(sample_category.id),
        name="Iced Chocolate Fudge Brownie",
        description="A cold, rich chocolate dessert topped with fudge",
    )
    await _create_item(
        client,
        staff_headers,
        category_id=str(sample_category.id),
        name="Grilled Chicken Sandwich",
        description="Savory grilled chicken breast with lettuce and tomato",
    )

    response = await client.get("/menu/search", params={"q": "something cold and chocolatey"})
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 2
    assert results[0]["item"]["name"] == "Iced Chocolate Fudge Brownie"
    assert results[0]["score"] > results[1]["score"]


async def test_update_menu_item_regenerates_embedding_on_name_change(
    client, staff_user, sample_category
):
    staff_headers = {"Authorization": f"Bearer {await get_access_token(client, staff_user)}"}
    create_response = await _create_item(client, staff_headers, category_id=str(sample_category.id))
    item_id = create_response.json()["id"]

    update_response = await client.put(
        f"/menu/items/{item_id}",
        json={"name": "Iced Latte", "price": "5.00"},
        headers=staff_headers,
    )
    assert update_response.status_code == 200
    body = update_response.json()
    assert body["name"] == "Iced Latte"
    assert body["price"] == "5.00"

    search_response = await client.get("/menu/search", params={"q": "iced latte"})
    assert search_response.json()[0]["item"]["name"] == "Iced Latte"


async def test_delete_menu_item(client, staff_user, sample_category):
    staff_headers = {"Authorization": f"Bearer {await get_access_token(client, staff_user)}"}
    create_response = await _create_item(client, staff_headers, category_id=str(sample_category.id))
    item_id = create_response.json()["id"]

    delete_response = await client.delete(f"/menu/items/{item_id}", headers=staff_headers)
    assert delete_response.status_code == 204

    menu_response = await client.get("/menu")
    assert menu_response.json()[0]["items"] == []
