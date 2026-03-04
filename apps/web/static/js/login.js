  // Theme
    const themeBtn = document.getElementById('themeBtn');
    const html = document.documentElement;

    // Get saved theme
    let savedTheme = localStorage.getItem('theme');

    // If none saved, use device preference
    if (!savedTheme) {
    savedTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    html.setAttribute('data-theme', savedTheme);
    updateIcons(savedTheme);

    themeBtn.addEventListener('click', () => {
    const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';

    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next); // remember user choice

    updateIcons(next);
    });

    function updateIcons(theme) {
    themeBtn.querySelector('.icon-moon').style.display = theme === 'dark' ? 'flex' : 'none';
    themeBtn.querySelector('.icon-sun').style.display  = theme === 'light' ? 'flex' : 'none';
    }

  // Password toggle
  const pwdInput  = document.getElementById('password');
  const pwdToggle = document.getElementById('pwdToggle');
  const eyeIcon   = document.getElementById('eyeIcon');
  const eyeOpen   = `<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>`;
  const eyeClosed = `<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>`;
  let shown = false;
  pwdToggle.addEventListener('click', () => {
    shown = !shown;
    pwdInput.type = shown ? 'text' : 'password';
    eyeIcon.innerHTML = shown ? eyeClosed : eyeOpen;
  });

  // Custom checkbox
  document.getElementById('remember').addEventListener('change', function() {
    // visual handled by CSS :checked sibling
  });

  // Form submit
  const form      = document.getElementById('loginForm');
  const submitBtn = document.getElementById('submitBtn');
  const toast     = document.getElementById('toast');

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    let valid = true;

    const idField  = document.getElementById('field-identifier');
    const pwdField = document.getElementById('field-password');
    const idVal    = document.getElementById('identifier').value.trim();
    const pwdVal   = document.getElementById('password').value.trim();

    // reset
    idField.classList.remove('error');
    pwdField.classList.remove('error');

    if (!idVal)  { idField.classList.add('error');  valid = false; }
    if (!pwdVal) { pwdField.classList.add('error'); valid = false; }

    if (!valid) return;

    // simulate loading
    submitBtn.classList.add('loading');
    setTimeout(() => {
      submitBtn.classList.remove('loading');
      toast.classList.add('show');
      setTimeout(() => toast.classList.remove('show'), 3000);
    }, 1800);
  });

  // Clear errors on input
  document.getElementById('identifier').addEventListener('input', () =>
    document.getElementById('field-identifier').classList.remove('error'));
  document.getElementById('password').addEventListener('input', () =>
    document.getElementById('field-password').classList.remove('error'));
