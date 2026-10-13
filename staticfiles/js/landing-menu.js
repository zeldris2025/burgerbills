/*
 * Landing page menu showcase: turns the stacked Hot Deals / Combos / Meals
 * panels into tabs and pops the cards in when the section scrolls into view.
 * Without this script every panel simply shows, one under the other.
 */
(function () {
    const section = document.querySelector('[data-landing-menu]');
    if (!section) return;

    const tablist = section.querySelector('.menu-tabs');
    const tabs = Array.from(section.querySelectorAll('.menu-tab'));
    const panels = tabs.map((tab) => document.getElementById(tab.getAttribute('aria-controls')));
    if (!tabs.length) return;

    let inView = false;

    function reveal(panel) {
        panel.classList.remove('is-revealed');
        // Force a reflow so the pop-in animation replays on every tab switch.
        void panel.offsetWidth;
        panel.classList.add('is-revealed');
    }

    function select(index, focus) {
        tabs.forEach((tab, i) => {
            const active = i === index;
            tab.setAttribute('aria-selected', String(active));
            tab.tabIndex = active ? 0 : -1;
            panels[i].hidden = !active;
            if (!active) panels[i].classList.remove('is-revealed');
        });
        if (focus) tabs[index].focus();
        if (inView) reveal(panels[index]);
    }

    tabs.forEach((tab, i) => {
        tab.addEventListener('click', () => select(i, false));
        tab.addEventListener('keydown', (event) => {
            let next = null;
            if (event.key === 'ArrowRight') next = (i + 1) % tabs.length;
            if (event.key === 'ArrowLeft') next = (i - 1 + tabs.length) % tabs.length;
            if (event.key === 'Home') next = 0;
            if (event.key === 'End') next = tabs.length - 1;
            if (next === null) return;
            event.preventDefault();
            select(next, true);
        });
    });

    tablist.hidden = false;
    section.classList.add('is-tabbed');
    select(0, false);

    const showCurrent = () => {
        inView = true;
        const current = tabs.findIndex((tab) => tab.getAttribute('aria-selected') === 'true');
        reveal(panels[current]);
    };

    if (!('IntersectionObserver' in window)) {
        showCurrent();
        return;
    }

    const observer = new IntersectionObserver((entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
            observer.disconnect();
            showCurrent();
        }
    }, { rootMargin: '0px 0px -15% 0px' });
    observer.observe(section);
})();
