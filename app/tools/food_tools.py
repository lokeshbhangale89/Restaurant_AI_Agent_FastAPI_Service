import requests

BASE_URL = "http://localhost:4000"

# =========================
# ⚡ SIMPLE MENU CACHE (CRITICAL SPEED FIX)
# =========================
MENU_CACHE = None


def get_food_items(query: str = ""):
    global MENU_CACHE

    if MENU_CACHE is None:
        print("📥 Fetching menu from API...")
        try:
            response = requests.get(f"{BASE_URL}/api/fooditems")
            MENU_CACHE = response.json()
        except Exception as e:
            print("❌ MENU ERROR:", e)
            return {}

    data = MENU_CACHE

    if query:
        q = query.lower()
        return {
            "products": [
                item for item in data.get("products", [])
                if q in item.get("name", "").lower()
            ]
        }

    return data


# =========================
# 🛒 ADD TO CART (FAST VERSION)
# =========================
def add_to_cart_api(token: str, product_name: str, quantity: int = 1):
    try:
        items = get_food_items().get("products", [])

        product = next(
            (i for i in items if product_name.lower() in i.get("name", "").lower()),
            None
        )

        if not product:
            return f"❌ Product '{product_name}' not found"

        url = f"{BASE_URL}/api/cart/addtocart"

        response = requests.post(
            url,
            json={
                "productId": product.get("productId"),
                "quantity": quantity
            },
            cookies={"access_token": token}
        )

        if response.status_code != 200:
            return f"❌ Add failed: {response.text}"

        return "✅ Added to cart"

    except Exception as e:
        print("❌ Add error:", e)
        return "❌ Failed to add"


# =========================
# 📦 GET CART (NO EXTRA LOGIC)
# =========================
def get_cart_api(token: str):
    try:
        response = requests.get(
            f"{BASE_URL}/api/cart/getcartitems",
            cookies={"access_token": token}
        )

        if response.status_code != 200:
            return "❌ Cart fetch failed"

        return response.text

    except Exception as e:
        return "❌ Cart error"


# =========================
# ❌ REMOVE CART ITEM (FAST)
# =========================
def remove_from_cart_api(token: str, product_name: str):
    try:
        items = get_food_items().get("products", [])

        product = next(
            (i for i in items if product_name.lower() in i.get("name", "").lower()),
            None
        )

        if not product:
            return "❌ Not found"

        response = requests.delete(
            f"{BASE_URL}/api/cart/remove?productId={product.get('productId')}",
            cookies={"access_token": token}
        )

        return "✅ Removed" if response.status_code == 200 else "❌ Failed"

    except Exception:
        return "❌ Error"


# =========================
# 🧹 CLEAR CART
# =========================
def clear_cart_api(token: str):
    try:
        response = requests.delete(
            f"{BASE_URL}/api/cart/clear",
            cookies={"access_token": token}
        )

        return "✅ Cleared" if response.status_code == 200 else "❌ Failed"

    except Exception:
        return "❌ Error"