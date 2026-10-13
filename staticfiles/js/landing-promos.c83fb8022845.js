/*
 * Landing page promotions: a looping slideshow (5s per slide) with arrows,
 * counter and pause button, a live "ends in" countdown, and removal of any
 * promotion that ends while the page is open. The server already leaves
 * ended promotions out of the page.
 */
(function () {
    const section = document.querySelector('[data-promos]');
    if (!section) return;

    const INTERVAL = 5000;

    const track = section.querySelector('[data-promos-track]');
    const controls = section.querySelector('.promos-controls');
    const prev = section.querySelector('[data-promos-prev]');
    const next = section.querySelector('[data-promos-next]');
    const playButton = section.querySelector('[data-promos-play]');
    const counter = section.querySelector('.promos-count');
    const current = section.querySelector('[data-promos-current]');
    const total = section.querySelector('[data-promos-total]');
    const progressWrap = section.querySelector('.promos-progress');
    const progress = section.querySelector('[data-promos-progress]');

    const slides = () => Array.from(track.querySelectorAll('.promo-slide'));

    function activeIndex() {
        const width = track.clientWidth || 1;
        return Math.min(Math.round(track.scrollLeft / width), slides().length - 1);
    }

    function updateControls() {
        const count = slides().length;
        controls.hidden = count < 2;
        progressWrap.hidden = count < 2;
        current.textContent = activeIndex() + 1;
        total.textContent = count;
    }

    // Steps wrap around, so "next" on the last slide goes back to the first.
    function go(step) {
        const count = slides().length;
        if (count < 2) return;
        const target = (activeIndex() + step + count) % count;
        track.scrollTo({ left: target * track.clientWidth, behavior: 'smooth' });
    }

    /* ---- Autoplay ------------------------------------------------------
       Runs only while it makes sense to: not paused by the visitor, not
       being hovered or keyboard-focused, page visible and section on screen.
       Visitors who prefer reduced motion start paused. */

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let userPaused = reduceMotion;
    let hovering = false;
    let focused = false;
    let onScreen = true;
    let autoplayTimer = null;

    progress.style.setProperty('--promos-interval', `${INTERVAL / 1000}s`);

    function shouldRun() {
        return !userPaused && !hovering && !focused && onScreen
            && !document.hidden && slides().length > 1;
    }

    function restartProgress(running) {
        progress.classList.remove('is-running');
        if (!running) return;
        void progress.offsetWidth; // reflow so the fill animation starts over
        progress.classList.add('is-running');
    }

    function schedule() {
        window.clearTimeout(autoplayTimer);
        const running = shouldRun();
        restartProgress(running);
        if (running) {
            autoplayTimer = window.setTimeout(() => {
                go(1);
                schedule();
            }, INTERVAL);
        }
    }

    function renderPlayButton() {
        playButton.setAttribute('aria-label', userPaused ? 'Play slideshow' : 'Pause slideshow');
        playButton.setAttribute('aria-pressed', String(userPaused));
        playButton.innerHTML = `<i class="fas fa-${userPaused ? 'play' : 'pause'}" aria-hidden="true"></i>`;
        // Announce slide changes only when the visitor is driving them.
        counter.setAttribute('aria-live', userPaused ? 'polite' : 'off');
    }

    playButton.addEventListener('click', () => {
        userPaused = !userPaused;
        renderPlayButton();
        schedule();
    });

    prev.addEventListener('click', () => { go(-1); schedule(); });
    next.addEventListener('click', () => { go(1); schedule(); });

    // A swipe counts as the visitor taking over this slide: give them a fresh 5s.
    track.addEventListener('pointerdown', schedule, { passive: true });
    track.addEventListener('scroll', () => window.requestAnimationFrame(updateControls), { passive: true });
    window.addEventListener('resize', updateControls);

    // Mouse only: a tap on a phone fires a "hover" that never ends.
    section.addEventListener('pointerenter', (event) => {
        if (event.pointerType !== 'mouse') return;
        hovering = true;
        schedule();
    });
    section.addEventListener('pointerleave', (event) => {
        if (event.pointerType !== 'mouse') return;
        hovering = false;
        schedule();
    });
    // Keyboard focus only, so clicking an arrow doesn't leave the show stuck.
    section.addEventListener('focusin', (event) => {
        if (!event.target.matches(':focus-visible')) return;
        focused = true;
        schedule();
    });
    section.addEventListener('focusout', (event) => {
        if (section.contains(event.relatedTarget)) return;
        focused = false;
        schedule();
    });
    document.addEventListener('visibilitychange', schedule);

    if ('IntersectionObserver' in window) {
        new IntersectionObserver((entries) => {
            onScreen = entries[entries.length - 1].isIntersecting;
            schedule();
        }, { threshold: 0.35 }).observe(section);
    }

    /* ---- Countdown and expiry ----------------------------------------- */

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
        let removed = false;
        slides().forEach((slide) => {
            const endsAt = Date.parse(slide.dataset.endsAt);
            if (Number.isNaN(endsAt)) return;
            const left = endsAt - now;
            if (left <= 0) {
                slide.remove();
                removed = true;
                return;
            }
            const text = slide.querySelector('[data-countdown]');
            if (text) text.textContent = label(left);
        });

        if (!slides().length) {
            section.remove();
            window.clearInterval(countdownTimer);
            window.clearTimeout(autoplayTimer);
            return;
        }
        updateControls();
        if (removed) schedule();
    }

    const countdownTimer = window.setInterval(tick, 30000);
    renderPlayButton();
    tick();
    schedule();
})();
