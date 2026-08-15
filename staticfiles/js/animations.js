/**
 * Smooth Animations & Interactions
 * Handles page load animations, smooth scrolling, and micro-interactions
 */

class MenuAnimations {
  constructor() {
    this.init();
  }

  init() {
    this.animatePageLoad();
    this.setupCategoryScroll();
    this.setupSmoothScroll();
    this.setupHoverEffects();
    this.setupButtonAnimations();
  }

  /**
   * Fade-in animation on page load
   */
  animatePageLoad() {
    // Fade in main content
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 600ms ease-out';
    
    setTimeout(() => {
      document.body.style.opacity = '1';
    }, 100);

    // Stagger animate menu items
    this.staggerAnimateElements('.menu-item', 'stagger-item');
  }

  /**
   * Stagger animate a list of elements
   */
  staggerAnimateElements(selector, animationClass) {
    const elements = document.querySelectorAll(selector);
    elements.forEach((el, index) => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(20px)';
      el.style.transition = `all 300ms ease-out ${index * 50}ms`;
      
      setTimeout(() => {
        el.classList.add(animationClass);
        el.style.opacity = '1';
        el.style.transform = 'translateY(0)';
      }, index * 50);
    });
  }

  /**
   * Setup smooth category scroll and highlight
   */
  setupCategoryScroll() {
    const categoryTabs = document.querySelectorAll('.category-tab');
    const menuSections = document.querySelectorAll('[data-category]');

    if (categoryTabs.length === 0) return;

    categoryTabs.forEach(tab => {
      tab.addEventListener('click', (e) => {
        e.preventDefault();
        
        const categoryId = tab.getAttribute('data-category');
        const section = document.querySelector(`[data-category="${categoryId}"]`);

        if (section) {
          // Update active tab
          categoryTabs.forEach(t => t.classList.remove('active'));
          tab.classList.add('active');

          // Smooth scroll to section
          const headerHeight = document.querySelector('header').offsetHeight;
          const targetTop = section.offsetTop - headerHeight - 20;
          
          window.scrollTo({
            top: targetTop,
            behavior: 'smooth'
          });

          // Scroll tab into view
          tab.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
        }
      });
    });

    // Update active tab on scroll
    window.addEventListener('scroll', () => {
      const headerHeight = document.querySelector('header').offsetHeight;
      const scrollTop = window.scrollY + headerHeight + 100;

      menuSections.forEach(section => {
        const categoryId = section.getAttribute('data-category');
        const tab = document.querySelector(`[data-category="${categoryId}"]`);
        
        if (!tab) return;

        const sectionTop = section.offsetTop;
        const sectionBottom = sectionTop + section.offsetHeight;

        if (scrollTop >= sectionTop && scrollTop < sectionBottom) {
          categoryTabs.forEach(t => t.classList.remove('active'));
          tab.classList.add('active');
          
          // Auto-scroll tab into view
          tab.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
        }
      });
    });
  }

  /**
   * Setup smooth scroll behavior
   */
  setupSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
          target.scrollIntoView({ behavior: 'smooth' });
        }
      });
    });
  }

  /**
   * Setup hover effects on menu items
   */
  setupHoverEffects() {
    const menuItems = document.querySelectorAll('.menu-item');

    menuItems.forEach(item => {
      const image = item.querySelector('.menu-item-image img');
      
      item.addEventListener('mouseenter', () => {
        // Scale image
        if (image) {
          image.style.transform = 'scale(1.08)';
        }
        
        // Lift card
        item.style.transform = 'translateY(-8px)';
        item.style.boxShadow = 'var(--shadow-lg)';
      });

      item.addEventListener('mouseleave', () => {
        // Reset image
        if (image) {
          image.style.transform = 'scale(1)';
        }
        
        // Reset card
        item.style.transform = 'translateY(0)';
        item.style.boxShadow = 'var(--shadow-sm)';
      });
    });
  }

  /**
   * Setup button press animations
   */
  setupButtonAnimations() {
    const buttons = document.querySelectorAll('.btn');

    buttons.forEach(btn => {
      btn.addEventListener('mousedown', () => {
        btn.style.transform = 'scale(0.98)';
      });

      btn.addEventListener('mouseup', () => {
        btn.style.transform = 'scale(1)';
      });

      btn.addEventListener('mouseleave', () => {
        btn.style.transform = 'scale(1)';
      });
    });
  }

  /**
   * Animate success checkmark
   */
  static showSuccessAnimation(element) {
    const originalContent = element.innerHTML;
    element.innerHTML = '✓';
    element.classList.add('bounce');
    
    setTimeout(() => {
      element.innerHTML = originalContent;
      element.classList.remove('bounce');
    }, 1500);
  }

  /**
   * Pulse animation for badges
   */
  static startPulse(element) {
    element.style.animation = 'pulse 2s ease-in-out infinite';
  }

  /**
   * Stop pulse animation
   */
  static stopPulse(element) {
    element.style.animation = 'none';
  }
}

// Initialize animations when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new MenuAnimations();
});

// Reveal elements on scroll (lazy animation)
const setupScrollReveal = () => {
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('fade-in');
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  document.querySelectorAll('[data-scroll-reveal]').forEach(el => {
    observer.observe(el);
  });
};

document.addEventListener('DOMContentLoaded', setupScrollReveal);
