// ── Helpers ──────────────────────────────────────────────────
function getShopId() {
// Expects route like /session/<shop_id>
const parts = window.location.pathname.split('/').filter(Boolean);
return parts[parts.length - 1] || null;
}

function formatDatetime(dt) {
if (!dt) return '—';
const d = new Date(dt);
if (isNaN(d)) return dt;
return d.toLocaleString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit', hour12: false
});
}

function escapeHtml(str) {
return String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── Render ───────────────────────────────────────────────────
function buildRow(s, index) {
const isOngoing = s.duration === 'ongoing';
const photo = escapeHtml(s.photo || '/static/imgs/avatar.png');
const customer = escapeHtml(s.customer);
const phone = escapeHtml(s.phone);
const bike = escapeHtml(s.bike);
const startFmt = formatDatetime(s.start);
const stopFmt = s.stop ? formatDatetime(s.stop) : isOngoing ? '<span style="color:var(--volt);font-family:\'Space Mono\',monospace;font-size:10px;letter-spacing:1px;">LIVE</span>' : '—';

const durationBadge = isOngoing
    ? `<span class="badge-duration badge-ongoing"></span>`
    : `<span class="badge-duration badge-done">${escapeHtml(s.duration)}</span>`;

const amountHtml = isOngoing
    ? `<div class="amount-value ongoing">ongoing</div>`
    : `<div class="amount-value">KES ${Number(s.amount).toLocaleString()}</div>`;

const actionBtn = s.action === 'print'
    ? `<button class="btn-action btn-print" onclick="handlePrint('${escapeHtml(s.id)}')">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
        Print
        </button>`
    : `<button class="btn-action btn-stop" onclick="handleStop('${escapeHtml(s.id)}')">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
            <rect x="5" y="5" width="14" height="14" rx="1"/>
        </svg>
        Details
        </button>`;

return `
    <div class="session-row${isOngoing ? ' ongoing' : ''}" style="animation-delay:${index * 40}ms">
    <img class="avatar" src="${photo}" alt="${customer}" onerror="this.src='/static/imgs/avatar.png'">
    <div class="cell-customer">
        <div class="customer-name">${customer}</div>
        <div class="customer-phone">${phone}</div>
    </div>
    <div class="cell-bike">
        <div class="bike-name">${bike.split(' ')[0]}</div>
        <div class="bike-id">${bike.split(' ').slice(1).join(' ')}</div>
    </div>
    <div class="cell-time start-col">
        <div class="time-label">Start</div>
        <div class="time-value">${startFmt}</div>
    </div>
    <div class="cell-time stop-col">
        <div class="time-label">Stop</div>
        <div class="time-value">${stopFmt}</div>
    </div>
    <div class="cell-duration">
        ${durationBadge}
        <div style="margin-top:6px">${amountHtml}</div>
    </div>
    <div class="cell-action">${actionBtn}</div>
    </div>`;
}

// ── Fetch ────────────────────────────────────────────────────
async function loadSessions() {
const shopId = getShopId();

document.getElementById('shop-id-display').textContent =
    `SHOP — ${shopId || 'unknown'}`;

if (!shopId) {
    showError('No shop ID found in URL.');
    hideSkeleton();
    return;
}

try {
    const res = await fetch(`/queries/v1/sessions/${shopId}/all`, {
    credentials: 'include',
    headers: { 'Accept': 'application/json' }
    });

    if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}`);
    }

    const sessions = await res.json();
    hideSkeleton();
    renderSessions(sessions);

} catch (err) {
    hideSkeleton();
    showError(err.message || 'Failed to load sessions.');
}
}

function renderSessions(sessions) {
const list = document.getElementById('sessions-list');
const header = document.getElementById('table-header');
const chip = document.getElementById('count-chip');
const countText = document.getElementById('count-text');
const liveDot = document.getElementById('live-dot');
const headerMeta = document.getElementById('header-meta');

if (!sessions || sessions.length === 0) {
    document.getElementById('empty-state').classList.add('visible');
    headerMeta.textContent = '0 sessions';
    return;
}

const ongoingCount = sessions.filter(s => s.duration === 'ongoing').length;

// Update header
headerMeta.textContent = `${sessions.length} session${sessions.length !== 1 ? 's' : ''}${ongoingCount ? ` · ${ongoingCount} live` : ''}`;
countText.textContent = sessions.length;
chip.style.display = 'inline-flex';
if (ongoingCount > 0) {
    liveDot.classList.add('active');
}

// Render rows
list.innerHTML = sessions.map((s, i) => buildRow(s, i)).join('');
header.style.display = 'grid';
list.style.display = 'block';
}

function hideSkeleton() {
document.getElementById('skeleton-list').style.display = 'none';
}

function showError(msg) {
const el = document.getElementById('error-state'); 
el.textContent = `Error: ${msg}`;
el.classList.add('visible');
document.getElementById('header-meta').textContent = 'Failed to load';
}

// ── Action stubs ─────────────────────────────────────────────
function handlePrint(sessionId) {
console.log('Print session:', sessionId);
window.location.href="/session/" + sessionId;
}

function handleStop(sessionId) {
console.log('Stop session:', sessionId);
window.location.href="/session/" + sessionId;
}

// ── Init ─────────────────────────────────────────────────────
loadSessions();