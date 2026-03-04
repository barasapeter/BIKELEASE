const themeBtn = document.getElementById('themeBtn');
const html = document.documentElement;

let savedTheme = localStorage.getItem('theme');
if (!savedTheme) {
  savedTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}
html.setAttribute('data-theme', savedTheme);
updateIcons(savedTheme);

themeBtn.addEventListener('click', () => {
  const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
  updateIcons(next);
});

function updateIcons(theme) {
  themeBtn.querySelector('.icon-moon').style.display = theme === 'dark' ? 'flex' : 'none';
  themeBtn.querySelector('.icon-sun').style.display = theme === 'light' ? 'flex' : 'none';
}

const pwdInput = document.getElementById('password');
const pwdToggle = document.getElementById('pwdToggle');
const eyeIcon = document.getElementById('eyeIcon');
const eyeOpen = `<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>`;
const eyeClosed = `<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>`;
let shown = false;

pwdToggle.addEventListener('click', () => {
  shown = !shown;
  pwdInput.type = shown ? 'text' : 'password';
  eyeIcon.innerHTML = shown ? eyeClosed : eyeOpen;
});

document.getElementById('remember').addEventListener('change', function () {});

const form = document.getElementById('loginForm');
const submitBtn = document.getElementById('submitBtn');
const toast = document.getElementById('toast');

function setLoading(on) {
  submitBtn.classList.toggle('loading', !!on);
  submitBtn.disabled = !!on;
}

function setToast(text, show) {
  if (!toast) return;
  if (typeof text === 'string') toast.textContent = text;
  toast.classList.toggle('show', !!show);
}

function setFieldError(fieldId, on) {
  const el = document.getElementById(fieldId);
  if (!el) return;
  el.classList.toggle('error', !!on);
}

function normalizeCategory(v) {
  const x = (v || '').trim().toLowerCase();
  if (x === 'owner' || x === 'employee') return x;
  return '';
}

function resolveCategory() {
  const params = new URLSearchParams(window.location.search);
  const fromQuery = normalizeCategory(params.get('category'));
  if (fromQuery) return fromQuery;
  const fromData = normalizeCategory(html.getAttribute('data-category'));
  if (fromData) return fromData;
  return 'owner';
}

function nextUrl() {
  const params = new URLSearchParams(window.location.search);
  return params.get('next') || '/dashboard';
}

function persistRemember(remember, username, category) {
  const key = 'auth_last_login';
  const value = JSON.stringify({ username, category, ts: Date.now() });
  if (remember) {
    localStorage.setItem(key, value);
    sessionStorage.removeItem(key);
  } else {
    sessionStorage.setItem(key, value);
    localStorage.removeItem(key);
  }
}

async function loginRequest(username, pin, category) {
  const res = await fetch('/auth/v1/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ username, pin, category })
  });

  let data = null;
  try {
    data = await res.json();
  } catch (_) {}

  return { res, data };
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const idVal = document.getElementById('identifier').value.trim();
  const pwdVal = document.getElementById('password').value.trim();
  const remember = !!document.getElementById('remember')?.checked;
  const category = resolveCategory();

  setFieldError('field-identifier', false);
  setFieldError('field-password', false);

  let valid = true;
  if (!idVal) {
    setFieldError('field-identifier', true);
    valid = false;
  }
  if (!pwdVal) {
    setFieldError('field-password', true);
    valid = false;
  }
  if (!valid) return;

  setLoading(true);
  setToast('Logging you in…', true);

  try {
    const { res, data } = await loginRequest(idVal.toLowerCase(), pwdVal, category);

    if (res.ok) {
      persistRemember(remember, idVal.toLowerCase(), category);
      setToast((data && data.detail) || 'Login successful.', true);
      window.location.href = nextUrl();
      return;
    }

    if (res.status === 401) {
      setFieldError('field-identifier', true);
      setFieldError('field-password', true);
      setToast((data && data.detail) || 'The sign in details are incorrect.', true);
      setTimeout(() => setToast('', false), 3000);
      return;
    }

    setToast((data && data.detail) || 'Something went wrong.', true);
    setTimeout(() => setToast('', false), 3000);
  } catch (_) {
    setToast('Network error. Please try again.', true);
    setTimeout(() => setToast('', false), 3000);
  } finally {
    setLoading(false);
  }
});

document.getElementById('identifier').addEventListener('input', () => setFieldError('field-identifier', false));
document.getElementById('password').addEventListener('input', () => setFieldError('field-password', false));