/**
 * Burger Bills - auto-refresh for the All Orders table
 * Copyright © 2026 Charlie Ah Kuoi. All rights reserved.
 *
 * Re-fetches only the orders table every 5 seconds and swaps it in. The rest of
 * the page - filters, scroll position, the header - is never touched.
 */
(() => {
    const REFRESH_MS = 5000;

    const region = document.getElementById('orders-table-region');
    const status = document.getElementById('refresh-status');
    const note = document.querySelector('.table-refresh-note');
    if (!region) return;

    const url = new URL(region.dataset.refreshUrl, window.location.origin);
    if (region.dataset.status) url.searchParams.set('status', region.dataset.status);

    let timer = null;
    let inFlight = false;
    let lastHtml = region.innerHTML;
    let failures = 0;

    function setStatus(text, stale) {
        if (status) status.textContent = text;
        if (note) note.classList.toggle('is-stale', Boolean(stale));
    }

    function timeNow() {
        return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }

    async function refresh() {
        // One request at a time: a slow response must not stack up behind itself.
        if (inFlight || document.hidden) return;
        inFlight = true;

        try {
            const response = await fetch(url, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                credentials: 'same-origin',
                cache: 'no-store',
            });

            if (response.status === 403 || response.redirected) {
                // Signed out or no longer staff - stop rather than paste a login page in.
                stop();
                setStatus('Auto-refresh stopped - please sign in again', true);
                return;
            }
            if (!response.ok) throw new Error('HTTP ' + response.status);

            const html = await response.text();
            failures = 0;

            // Only touch the DOM when something actually changed, so hover and
            // text selection survive the ticks where nothing happened.
            if (html !== lastHtml) {
                region.innerHTML = html;
                lastHtml = html;
            }
            setStatus('Updated ' + timeNow() + ' · refreshing every 5 seconds');
        } catch (error) {
            failures += 1;
            setStatus('Reconnecting… last update ' + timeNow(), failures > 1);
        } finally {
            inFlight = false;
        }
    }

    function start() {
        if (timer === null) timer = window.setInterval(refresh, REFRESH_MS);
    }

    function stop() {
        window.clearInterval(timer);
        timer = null;
    }

    // Polling a hidden tab is wasted work; catch up as soon as it is looked at.
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            stop();
        } else {
            start();
            refresh();
        }
    });

    start();
})();
