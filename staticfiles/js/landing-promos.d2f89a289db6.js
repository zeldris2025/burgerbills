/*
 * Landing page promotions: arrows and counter for the slide track, a live
 * "ends in" countdown, and removal of any promotion that ends while the page
 * is open. The server already leaves ended promotions out of the page.
 */
(function () {
    const section = document.querySelector('[data-promos]');
    if (!section) return;

    const track = section.querySelector('[data-promos-track]');
    const controls = section.querySelector('.promos-controls');
    const prev = section.querySelector('[data-promos-prev]');
    const next = section.querySelector('[data-promos-next]');
    const current = section.querySelector('[data-promos-current]');
    const total = section.querySelector('[data-promos-total]');

    const slides = () => Array.from(track.querySelectorAll('.promo-slide'));

    function activeIndex() {
        const width = track.clientWidth || 1;
        return Math.round(track.scrollLeft / width);
    }

    function updateControls() {
        const count = slides().length;
        controls.hidden = count < 2;
        const index = Math.min(activeIndex(), count - 1);
        current.textContent = index + 1;
        total.textContent = count;
        prev.disabled = index <= 0;
        next.disabled = index >= count - 1;
    }

    function go(step) {
        track.scrollBy({ left: step * track.clientWidth, behavior: 'smooth' });
    }

    prev.addEventListener('click', () => go(-1));
    next.addEventListener('click', () => go(1));
    track.addEventListener('scroll', () => window.requestAnimationFrame(updateControls), { passive: true });
    window.addEventListener('resize', updateControls);

    function label(msLeft) {
        const minutes = Math.floor(msLeft / 60000);
        const days = Math.floor(minutes / 1440);
        const hours = Math.floor((minutes % 1440) / 60);
        const mins = minutes % 60;
        if (days >= 2) return `Ends in ${days} days`;
        if (days === 1) return `Ends in 1 day ${hours}h`;
        if (hours >= 1) return `Ends in ${hours}h ${mins}m`;
        if (mins >= 1) return `Ends in ${mins} min`;
        return 'Ending now';
    }

    function tick() {
        const now = Date.now();
        slides().forEach((slide) => {
            const endsAt = Date.parse(slide.dataset.endsAt);
            if (Number.isNaN(endsAt)) return;
            const left = endsAt - now;
            if (left <= 0) {
                slide.remove();
                return;
            }
            const text = slide.querySelector('[data-countdown]');
            if (text) text.textContent = label(left);
        });

        if (!slides().length) {
            section.remove();
            window.clearInterval(timer);
            return;
        }
        updateControls();
    }

    const timer = window.setInterval(tick, 30000);
    tick();
})();
