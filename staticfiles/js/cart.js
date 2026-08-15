/**
 * Shopping Cart Manager
 * Handles cart operations: add, remove, update, display
 */

class CartManager {
  constructor(tableNumber) {
    this.tableNumber = tableNumber;
    this.cartData = {};
    this.cartSidebar = document.querySelector('.cart-sidebar');
    this.cartBadge = document.querySelector('.cart-badge');
    this.modal = document.querySelector('.modal');
    this.modalOverlay = document.querySelector('.modal-overlay');
    this.init();
  }

  init() {
    this.setupEventListeners();
    this.loadCart();
  }

  setupEventListeners() {
    // Cart sidebar close button
    const closeBtn = document.querySelector('.cart-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.closeSidebar());
    }

    // Modal close button
    const modalCloseBtn = document.querySelector('.modal-close');
    if (modalCloseBtn) {
      modalCloseBtn.addEventListener('click', () => this.closeModal());
    }

    // Modal overlay click
    if (this.modalOverlay) {
      this.modalOverlay.addEventListener('click', () => this.closeModal());
    }

    // Add to cart buttons
    document.querySelectorAll('[data-add-to-cart]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const itemId = btn.getAttribute('data-item-id');
        this.addToCart(itemId);
      });
    });

    // Quantity controls in cart
    this.setupQuantityControls();
  }

  setupQuantityControls() {
    const cartBody = document.querySelector('.cart-body');
    if (!cartBody) return;

    cartBody.addEventListener('click', (e) => {
      if (e.target.classList.contains('quantity-btn')) {
        const btn = e.target;
        const action = btn.getAttribute('data-action');
        const itemId = btn.closest('.cart-item').getAttribute('data-item-id');
        this.updateQuantity(itemId, action);
      }

      if (e.target.classList.contains('cart-item-remove')) {
        const itemId = e.target.closest('.cart-item').getAttribute('data-item-id');
        this.removeFromCart(itemId);
      }
    });
  }

  async addToCart(itemId) {
    try {
      const response = await fetch(`/table/${this.tableNumber}/add/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          menu_item_id: itemId,
          quantity: 1,
          special_requests: ''
        })
      });

      const data = await response.json();
      if (data.success) {
        this.showToast(data.message, 'success');
        this.loadCart();
        this.openSidebar();
      } else {
        this.showToast(data.message || 'Failed to add item', 'error');
      }
    } catch (error) {
      console.error('Error adding to cart:', error);
      this.showToast('Error adding item to cart', 'error');
    }
  }

  async updateQuantity(itemId, action) {
    const cartItem = document.querySelector(`[data-item-id="${itemId}"]`);
    const quantityDisplay = cartItem.querySelector('.quantity-display');
    let newQuantity = parseInt(quantityDisplay.textContent);

    if (action === 'increase') {
      newQuantity++;
    } else if (action === 'decrease' && newQuantity > 1) {
      newQuantity--;
    }

    try {
      const response = await fetch(`/table/${this.tableNumber}/update/${itemId}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          quantity: newQuantity
        })
      });

      const data = await response.json();
      if (data.success) {
        this.loadCart();
      }
    } catch (error) {
      console.error('Error updating quantity:', error);
      this.showToast('Error updating item quantity', 'error');
    }
  }

  async removeFromCart(itemId) {
    if (!confirm('Remove this item from cart?')) return;

    try {
      const response = await fetch(`/table/${this.tableNumber}/remove/${itemId}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      this.loadCart();
      this.showToast('Item removed from cart', 'success');
    } catch (error) {
      console.error('Error removing from cart:', error);
      this.showToast('Error removing item', 'error');
    }
  }

  async loadCart() {
    // Fetch current cart from server (you may need to create an API endpoint)
    // For now, we'll update the UI based on what's returned from other endpoints
    this.updateCartDisplay();
  }

  updateCartDisplay() {
    const cartBody = document.querySelector('.cart-body');
    const cartTotal = document.querySelector('.cart-total');
    const cartItems = document.querySelectorAll('.cart-item');

    if (cartItems.length === 0) {
      cartBody.innerHTML = `
        <div class="cart-empty">
          <div class="cart-empty-icon">🛒</div>
          <p>Your cart is empty</p>
          <small class="text-muted">Add items from the menu to get started</small>
        </div>
      `;
      if (this.cartBadge) this.cartBadge.textContent = '0';
      return;
    }

    if (this.cartBadge) {
      const totalItems = Array.from(cartItems).reduce((sum, item) => {
        const qty = parseInt(item.querySelector('.quantity-display').textContent);
        return sum + qty;
      }, 0);
      this.cartBadge.textContent = totalItems;
    }

    // Update total price
    if (cartTotal) {
      const total = Array.from(cartItems).reduce((sum, item) => {
        const priceText = item.querySelector('.cart-item-price').textContent;
        const price = parseFloat(priceText.replace('$', ''));
        return sum + price;
      }, 0);
      cartTotal.textContent = `$${total.toFixed(2)}`;
    }

    this.setupQuantityControls();
  }

  openSidebar() {
    if (this.cartSidebar) {
      this.cartSidebar.classList.add('open');
    }
  }

  closeSidebar() {
    if (this.cartSidebar) {
      this.cartSidebar.classList.remove('open');
    }
  }

  openModal(title, content) {
    if (!this.modal) return;

    const header = this.modal.querySelector('.modal-header h2');
    const body = this.modal.querySelector('.modal-body');

    if (header) header.textContent = title;
    if (body) body.innerHTML = content;

    this.modal.classList.add('show');
    this.modalOverlay.classList.add('show');
  }

  closeModal() {
    this.modal.classList.remove('show');
    this.modalOverlay.classList.remove('show');
  }

  showToast(message, type = 'info') {
    const container = document.querySelector('.toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
      success: '✓',
      error: '✕',
      info: 'ℹ'
    };

    toast.innerHTML = `
      <div class="toast-icon">${icons[type]}</div>
      <div class="toast-message">${message}</div>
      <button class="toast-close">×</button>
    `;

    container.appendChild(toast);

    toast.querySelector('.toast-close').addEventListener('click', () => {
      toast.remove();
    });

    // Auto-remove after 3 seconds
    setTimeout(() => {
      toast.remove();
    }, 3000);
  }

  async checkout() {
    const specialInstructions = document.getElementById('special_instructions')?.value || '';

    try {
      const response = await fetch(`/table/${this.tableNumber}/submit/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          special_instructions: specialInstructions
        })
      });

      const data = await response.json();
      if (data.success) {
        this.showToast('Order placed successfully!', 'success');
        setTimeout(() => {
          window.location.href = data.redirect_url;
        }, 1500);
      } else {
        this.showToast(data.message || 'Failed to place order', 'error');
      }
    } catch (error) {
      console.error('Error placing order:', error);
      this.showToast('Error placing order', 'error');
    }
  }
}

// Initialize cart manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const tableNumber = document.body.getAttribute('data-table');
  if (tableNumber) {
    window.cartManager = new CartManager(tableNumber);
  }
});
