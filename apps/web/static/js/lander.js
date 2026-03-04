  // Theme toggle
const themeBtn = document.getElementById('themeBtn');
const html = document.documentElement;

// Get saved theme
let theme = localStorage.getItem('theme');

// If no saved theme, use device preference
if (!theme) {
  theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

html.setAttribute('data-theme', theme);
updateIcons(theme);

themeBtn.addEventListener('click', () => {
  const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';

  html.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);

  updateIcons(next);
});

function updateIcons(mode) {
  themeBtn.querySelector('.icon-moon').style.display = mode === 'dark' ? 'flex' : 'none';
  themeBtn.querySelector('.icon-sun').style.display  = mode === 'light' ? 'flex' : 'none';
}

  // Live timer
  let secs = 42 * 60 + 17;
  const rpm = 5.0;
  const clockEl  = document.getElementById('clockDisplay');
  const amountEl = document.getElementById('amountDue');
  setInterval(() => {
    secs++;
    const m = String(Math.floor(secs / 60)).padStart(2, '0');
    const s = String(secs % 60).padStart(2, '0');
    if (clockEl)  clockEl.innerHTML = `${m}<span>:</span>${s}`;
    if (amountEl) amountEl.textContent = `KES ${((secs / 60) * rpm).toFixed(2)}`;
  }, 1000);

  // Scroll reveal
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.style.opacity = '0';
        e.target.style.animation = 'fadeUp 0.65s ease forwards';
        obs.unobserve(e.target);
      }
    });
  }, { threshold: 0.1 });
  document.querySelectorAll('.step, .feat, .pay-card, .ussd-point').forEach(el => {
    el.style.opacity = '0';
    obs.observe(el);
  });