/**
 * Burger Bills - new order alarm for the staff panel
 * Copyright © 2026 Charlie Ah Kuoi. All rights reserved.
 *
 * Polls for orders a customer has just submitted. When one shows up the alarm
 * beeps on a loop and an overlay blocks the board until a staff member clicks
 * OK, so an order cannot slip past a busy counter. The panel only reloads when
 * the board actually changed - and never while the alarm is up, because a
 * reload would silence it.
 */
(() => {
    const POLL_MS = 5000;
    const BEEP_MS = 1400;
    const ACK_KEY = 'bb-acknowledged-orders';
    const ACK_LIMIT = 200;

    const overlay = document.getElementById('new-order-alert');
    const listEl = document.getElementById('new-order-alert-list');
    const countEl = document.getElementById('new-order-alert-count');
    const okButton = document.getElementById('new-order-alert-ok');
    const soundHint = document.getElementById('new-order-sound-hint');
    const feed = document.getElementById('staff-order-feed');
    if (!overlay || !feed) return;

    const feedUrl = feed.dataset.feedUrl;
    let signature = feed.dataset.signature || '';
    let alarmOrders = [];
    let beepTimer = null;
    let pollTimer = null;
    let inFlight = false;
    let reloadPending = false;
    let audioCtx = null;
    const originalTitle = document.title;
    let titleTimer = null;

    /* ---------- acknowledged orders survive the reload that follows OK ---------- */

    function readAcknowledged() {
        try {
            const raw = window.localStorage.getItem(ACK_KEY);
            return raw ? JSON.parse(raw) : [];
        } catch (error) {
            return [];
        }
    }

    function acknowledge(ids) {
        try {
            const merged = readAcknowledged().concat(ids);
            const trimmed = merged.slice(-ACK_LIMIT);
            window.localStorage.setItem(ACK_KEY, JSON.stringify(trimmed));
        } catch (error) {
            /* Private browsing - the alarm still works, it may just repeat. */
        }
    }

    /* ---------- sound ---------- */

    function audioContext() {
        if (audioCtx) return audioCtx;
        const Ctx = window.AudioContext || window.webkitAudioContext;
        if (!Ctx) return null;
        audioCtx = new Ctx();
        return audioCtx;
    }

    // Browsers refuse to play audio until the page has been interacted with, so
    // take the first click or key press as permission and warm the context up.
    function unlockAudio() {
        const ctx = audioContext();
        if (ctx && ctx.state === 'suspended') ctx.resume();
        updateSoundHint();
    }

    function updateSoundHint() {
        if (!soundHint) return;
        const blocked = !audioCtx || audioCtx.state !== 'running';
        soundHint.hidden = !blocked;
    }

    function beep() {
        const ctx = audioContext();
        if (!ctx || ctx.state !== 'running') {
            updateSoundHint();
            return;
        }
        // Two short rising tones - carries over kitchen noise without being a siren.
        [[880, 0], [1180, 0.22]].forEach(([frequency, offset]) => {
            const start = ctx.currentTime + offset;
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'square';
            osc.frequency.value = frequency;
            gain.gain.setValueAtTime(0.0001, start);
            gain.gain.exponentialRampToValueAtTime(0.25, start + 0.02);
            gain.gain.exponentialRampToValueAtTime(0.0001, start + 0.19);
            osc.connect(gain).connect(ctx.destination);
            osc.start(start);
            osc.stop(start + 0.2);
        });
    }

    /* ---------- alarm ---------- */

    function startAlarm(orders) {
        alarmOrders = orders;
        countEl.textContent = orders.length === 1 ? '1 new order' : orders.length + ' new orders';
        listEl.innerHTML = orders.map((order) => `
            <li>
                <span class="new-order-alert-table">${order.table ? 'Table ' + order.table : 'Takeaway'}</span>
                <span class="new-order-alert-number">${order.order_number}</span>
                <span class="new-order-alert-total">$${order.total}</span>
            </li>
        `).join('');

        if (overlay.hidden) {
            overlay.hidden = false;
            document.body.classList.add('has-order-alarm');
            updateSoundHint();
            beep();
            beepTimer = window.setInterval(beep, BEEP_MS);
            titleTimer = window.setInterval(() => {
                document.title = document.title.startsWith('🔔') ? originalTitle : '🔔 NEW ORDER';
            }, 900);
        }
        okButton.focus();
    }

    function stopAlarm() {
        acknowledge(alarmOrders.map((order) => order.id));
        alarmOrders = [];
        overlay.hidden = true;
        document.body.classList.remove('has-order-alarm');
        window.clearInterval(beepTimer);
        window.clearInterval(titleTimer);
        beepTimer = null;
        titleTimer = null;
        document.title = originalTitle;

        // The board moved on while the alarm was up - show the real state now.
        if (reloadPending) window.location.reload();
    }

    /* ---------- polling ---------- */

    async function poll() {
        if (inFlight) return;
        inFlight = true;
        try {
            const response = await fetch(feedUrl, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                credentials: 'same-origin',
                cache: 'no-store',
            });
            if (response.status === 403 || response.redirected || !response.ok) return;

            const data = await response.json();
            const acknowledged = readAcknowledged();
            const unseen = (data.new_orders || []).filter((order) => !acknowledged.includes(order.id));

            if (unseen.length) {
                startAlarm(unseen);
            } else if (!overlay.hidden) {
                // Someone else took them on another screen.
                stopAlarm();
            }

            if (data.signature !== signature) {
                signature = data.signature;
                if (overlay.hidden) {
                    window.location.reload();
                } else {
                    reloadPending = true;
                }
            }
        } catch (error) {
            /* Offline for a tick - the next poll picks it back up. */
        } finally {
            inFlight = false;
        }
    }

    okButton.addEventListener('click', stopAlarm);
    document.addEventListener('click', unlockAudio, { once: false });
    document.addEventListener('keydown', unlockAudio, { once: false });
    if (soundHint) soundHint.addEventListener('click', unlockAudio);

    // Keep polling in a background tab: the whole point is to be heard when
    // nobody is looking at the screen.
    pollTimer = window.setInterval(poll, POLL_MS);
    poll();
})();
