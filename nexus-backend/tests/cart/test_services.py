import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from nexus_backend.cart.application.services import CartService
from nexus_backend.cart.domain.entities import Cart, CartItem, CartStatus
from nexus_backend.catalog.domain.entities import Product
from nexus_backend.shared.domain.exceptions import BusinessRuleViolationException, ResourceNotFoundException


@pytest.fixture
def cart_service(mock_cart_repo: AsyncMock, mock_product_repo: AsyncMock) -> CartService:
    return CartService(cart_repo=mock_cart_repo, product_repo=mock_product_repo)


@pytest.mark.asyncio
async def test_add_item_success_verifies_stock_and_contract(
    cart_service: CartService, mock_cart_repo: AsyncMock, mock_product_repo: AsyncMock, dummy_cart: Cart, dummy_product: Product
):
    # Arrange
    # Edge case: Exactly enough stock
    dummy_product.stock = 2
    dummy_product.price = 1500.50
    mock_product_repo.get_by_id.return_value = dummy_product
    mock_cart_repo.get_or_create_cart.return_value = dummy_cart
    
    # Simulate DB adding the item
    dummy_cart.items.append(CartItem(product_id=dummy_product.id, quantity=2, unit_price=dummy_product.price))
    mock_cart_repo.add_item.return_value = dummy_cart

    user_id = dummy_cart.user_id

    # Act
    cart = await cart_service.add_item(user_id=user_id, product_id=dummy_product.id, quantity=2)

    # Assert - Contract & State Mutations
    # 1. Product lookup is exact
    mock_product_repo.get_by_id.assert_called_once_with(dummy_product.id)
    
    # 2. Cart fetching is exact
    mock_cart_repo.get_or_create_cart.assert_called_once_with(user_id)
    
    # 3. Add item payload is exact and extracts the exact float price from the Decimal Product price
    mock_cart_repo.add_item.assert_called_once_with(
        cart_id=dummy_cart.id,
        product_id=dummy_product.id,
        quantity=2,
        unit_price=1500.50,
    )
    
    # 4. Verify properties mathematically (Simulating real integration checks)
    assert len(cart.items) == 2  # Originally had 1 from fixture + 1 added
    assert cart.items[-1].subtotal == 3001.00  # 1500.50 * 2


@pytest.mark.asyncio
async def test_add_item_product_not_found_aborts_transaction(
    cart_service: CartService, mock_cart_repo: AsyncMock, mock_product_repo: AsyncMock
):
    # Arrange
    mock_product_repo.get_by_id.return_value = None
    uid = uuid4()
    pid = uuid4()

    # Act & Assert
    with pytest.raises(ResourceNotFoundException, match="Product not found"):
        await cart_service.add_item(uid, pid, 1)

    # Verify short-circuit: cart is never created/fetched if product doesn't exist
    mock_cart_repo.get_or_create_cart.assert_not_called()
    mock_cart_repo.add_item.assert_not_called()


@pytest.mark.asyncio
async def test_add_item_insufficient_stock_aborts_transaction(
    cart_service: CartService, mock_cart_repo: AsyncMock, mock_product_repo: AsyncMock, dummy_product: Product
):
    # Arrange
    dummy_product.stock = 4
    mock_product_repo.get_by_id.return_value = dummy_product
    uid = uuid4()

    # Act & Assert
    with pytest.raises(BusinessRuleViolationException, match="Insufficient stock. Available: 4"):
        await cart_service.add_item(uid, dummy_product.id, 5)

    # Verify short-circuit
    mock_cart_repo.get_or_create_cart.assert_not_called()
    mock_cart_repo.add_item.assert_not_called()


@pytest.mark.asyncio
async def test_checkout_success_deducts_inventory_and_changes_status(
    cart_service: CartService, mock_cart_repo: AsyncMock, mock_product_repo: AsyncMock, dummy_cart: Cart
):
    # Arrange
    mock_cart_repo.get_or_create_cart.return_value = dummy_cart
    mock_product_repo.update_stock.return_value = True
    
    # We mutate the mock output to simulate what the DB checkout function does
    dummy_cart.status = CartStatus.CHECKED_OUT
    mock_cart_repo.checkout.return_value = dummy_cart

    # Act
    cart = await cart_service.checkout(dummy_cart.user_id)

    # Assert - Contract & Flow
    mock_cart_repo.get_or_create_cart.assert_called_once_with(dummy_cart.user_id)
    
    # Check that update_stock was called for EACH item with NEGATIVE quantity
    # Our dummy cart has 1 item with quantity 2
    mock_product_repo.update_stock.assert_called_once_with(dummy_cart.items[0].product_id, -2)
    
    # Check final checkout confirmation
    mock_cart_repo.checkout.assert_called_once_with(dummy_cart.id)
    assert cart.status == CartStatus.CHECKED_OUT


@pytest.mark.asyncio
async def test_checkout_empty_cart_aborts_transaction(
    cart_service: CartService, mock_cart_repo: AsyncMock, mock_product_repo: AsyncMock, dummy_cart: Cart
):
    # Arrange
    dummy_cart.items = []
    mock_cart_repo.get_or_create_cart.return_value = dummy_cart

    # Act & Assert
    with pytest.raises(BusinessRuleViolationException, match="Cart is empty"):
        await cart_service.checkout(dummy_cart.user_id)

    # Ensure no inventory was touched
    mock_product_repo.update_stock.assert_not_called()
    mock_cart_repo.checkout.assert_not_called()


@pytest.mark.asyncio
async def test_checkout_inventory_race_condition_aborts_transaction(
    cart_service: CartService, mock_cart_repo: AsyncMock, mock_product_repo: AsyncMock, dummy_cart: Cart
):
    # Arrange
    dummy_cart.items[0].product_name = "RTX 5090"
    mock_cart_repo.get_or_create_cart.return_value = dummy_cart
    
    # Simulate DB reporting that stock update failed (e.g. optimistic locking failed or check constraint hit)
    mock_product_repo.update_stock.return_value = False

    # Act & Assert
    with pytest.raises(BusinessRuleViolationException, match="Insufficient stock for product RTX 5090"):
        await cart_service.checkout(dummy_cart.user_id)

    # Ensure the cart was NOT checked out if inventory failed
    mock_cart_repo.checkout.assert_not_called()
