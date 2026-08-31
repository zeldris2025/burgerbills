/**
 * Burger Bills - hero orbit menu
 * Copyright © 2026 Charlie Ah Kuoi. All rights reserved.
 *
 * Opens the Home / About / Location / Order ring around the animated burger
 * while it is hovered, focused, or tapped, and closes it again on the way out.
 */
(() => {
    const orbit = document.getElementById('hero-orbit');
    if (!orbit) return;

    const open = () => orbit.classList.add('is-open');
    const close = () => orbit.classList.remove('is-open');

    orbit.addEventListener('mouseenter', open);
    orbit.addEventListener('mouseleave', close);

    // Keyboard users tabbing into a link get the same ring.
    orbit.addEventListener('focusin', open);
    orbit.addEventListener('focusout', (event) => {
        if (!orbit.contains(event.relatedTarget)) close();
    });

    // Touch and pen have no hover, so the first tap on the burger opens the ring.
    orbit.addEventListener('pointerdown', (event) => {
        if (event.pointerType === 'mouse') return;
        if (event.target.closest('.orbit-link')) return;
        orbit.classList.toggle('is-open');
    });

    document.addEventListener('pointerdown', (event) => {
        if (!orbit.contains(event.target)) close();
    });

    document.addEventListener('keydown', (event) => {
        if (event.key !== 'Escape' || !orbit.classList.contains('is-open')) return;
        close();
        const focused = document.activeElement;
        if (focused && orbit.contains(focused)) focused.blur();
    });
})();
