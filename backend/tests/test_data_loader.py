from app.data_loader import product_text
from app.models import Product


def test_product_text_includes_title_description_and_category():
    product = Product(
        id=1,
        title="Mechanical Keyboard",
        description="Clicky RGB switches",
        category="Gaming Keyboards",
        price=3999,
    )

    text = product_text(product)

    assert "Mechanical Keyboard" in text
    assert "Clicky RGB switches" in text
    assert "Gaming Keyboards" in text
