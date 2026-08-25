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

    // Order buttons
    document.querySelectorAll('[data-add-to-cart]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const itemId = btn.getAttribute('data-item-id');
        this.addToCart(itemId, btn);
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

  async addToCart(itemId, button) {
    const originalLabel = button.textContent;
    button.disabled = true;
    button.textContent = 'Adding...';

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
        button.textContent = 'Added';
        button.classList.add('is-added');
        this.showToast(data.message, 'success');
        await this.loadCart();
        this.openSidebar();
      } else {
        button.disabled = false;
        button.textContent = originalLabel;
        this.showToast(data.message || 'Failed to add item', 'error');
      }
    } catch (error) {
      button.disabled = false;
      button.textContent = originalLabel;
      console.error('Error adding to orders:', error);
      this.showToast('Error adding item to orders', 'error');
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
    if (!confirm('Cancel this item from your orders?')) return;

    try {
      const response = await fetch(`/table/${this.tableNumber}/remove/${itemId}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      const data = await response.json();
      if (!response.ok || !data.success) {
        throw new Error(data.message || 'Unable to cancel item');
      }

      await this.loadCart();
      this.showToast('Item cancelled', 'success');
    } catch (error) {
      console.error('Error cancelling item:', error);
      this.showToast(error.message || 'Error cancelling item', 'error');
    }
  }

  async loadCart() {
    try {
      const response = await fetch(`/table/${this.tableNumber}/orders/`);
      if (!response.ok) throw new Error('Unable to load orders');

      const data = await response.json();
      this.renderOrders(data);
    } catch (error) {
      console.error('Error loading orders:', error);
      this.showToast('Unable to load your orders', 'error');
    }
  }

  renderOrders(data) {
    const cartBody = document.querySelector('.cart-body');
    const cartTotal = document.querySelector('.cart-total');
    if (!cartBody) return;

    if (data.items.length === 0) {
      cartBody.innerHTML = `
        <div class="cart-empty">
          <div class="cart-empty-icon">🛒</div>
          <p>Your orders are empty</p>
          <small class="text-muted">Choose an item from the menu to get started</small>
        </div>
      `;
    } else {
      cartBody.innerHTML = data.items.map(item => `
        <div class="cart-item" data-item-id="${item.id}" data-menu-item-id="${item.menu_item_id || ''}">
          <div class="cart-item-name">${this.escapeHTML(item.name)}</div>
          <div class="cart-item-footer">
            <div class="quantity-control">
              <button type="button" class="quantity-btn" data-action="decrease" aria-label="Decrease quantity">−</button>
              <span class="quantity-display">${item.quantity}</span>
              <button type="button" class="quantity-btn" data-action="increase" aria-label="Increase quantity">+</button>
            </div>
            <span class="cart-item-price">$${Number(item.subtotal).toFixed(2)}</span>
            <button type="button" class="cart-item-remove" aria-label="Cancel ${this.escapeHTML(item.name)}">Cancel</button>
          </div>
        </div>
      `).join('');
    }

    if (this.cartBadge) this.cartBadge.textContent = data.total_items;
    if (cartTotal) cartTotal.textContent = `$${Number(data.total_amount).toFixed(2)}`;

    const orderedItemIds = new Set(data.items.map(item => String(item.menu_item_id)));
    document.querySelectorAll('[data-add-to-cart]').forEach(button => {
      const isAdded = orderedItemIds.has(button.dataset.itemId);
      button.disabled = isAdded;
      button.classList.toggle('is-added', isAdded);
      button.textContent = isAdded ? 'Added' : 'Order now';
    });
  }

  escapeHTML(value) {
    const element = document.createElement('div');
    element.textContent = value;
    return element.innerHTML;
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

  openCheckout() {
    // Navigate to checkout page
    window.location.href = `/table/${this.tableNumber}/checkout/`;
  }
}

// Initialize cart manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const tableNumber = document.body.getAttribute('data-table');
  if (tableNumber) {
    window.cartManager = new CartManager(tableNumber);
  }
});
