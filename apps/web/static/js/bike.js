  // ── BIKE CODE GENERATOR ──────────────────────────────────
  const CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';

  function randomSegment(len) {
    let s = '';
    for (let i = 0; i < len; i++) s += CHARS[Math.floor(Math.random() * CHARS.length)];
    return s;
  }

  function generateBikeCode() {
    return randomSegment(3) + '-' + randomSegment(3);
  }

  let currentBikeCode = generateBikeCode();

  function renderCode() {
    document.getElementById('bikeCodeDisplay').textContent = currentBikeCode;
  }

  function regenCode(silent = false) {
    currentBikeCode = generateBikeCode();
    const display = document.getElementById('bikeCodeDisplay');
    const btn     = document.getElementById('regenBtn');

    if (!silent) {
      display.classList.add('refreshing');
      btn.classList.add('spinning');
      setTimeout(() => {
        renderCode();
        display.classList.remove('refreshing');
        // Remove class to allow re-trigger on next click
        btn.classList.remove('spinning');
      }, 350);
    } else {
      renderCode();
    }
  }

  // Init
  renderCode();

  // ── SHOP ID FROM URL ─────────────────────────────────────
  // Reads the last numeric path segment — matches /bikes/v1/bikes/{shop_id}
  function getShopIdFromUrl() {
    const parts = window.location.pathname.split('/').filter(Boolean);
    for (let i = parts.length - 1; i >= 0; i--) {
      if (/^\d+$/.test(parts[i])) return parts[i];
    }
    return null;
  }

  const shopId = getShopIdFromUrl();

  // ── VALIDATION ───────────────────────────────────────────
  function setError(fieldId, errId, show) {
    const input = document.getElementById(fieldId);
    const err   = document.getElementById(errId);
    if (show) { input.classList.add('error'); err.classList.add('visible'); }
    else       { input.classList.remove('error'); err.classList.remove('visible'); }
  }

  function clearErrors() {
    setError('nickname', 'err_nickname', false);
    setError('rpm',      'err_rpm',      false);
  }

  function validate() {
    clearErrors();
    const nickname = document.getElementById('nickname').value.trim();
    const rpm      = document.getElementById('rpm').value.trim();
    let ok = true;
    if (!nickname)                    { setError('nickname', 'err_nickname', true); ok = false; }
    if (!rpm || isNaN(parseInt(rpm))) { setError('rpm',      'err_rpm',      true); ok = false; }
    return ok;
  }

  // ── SUBMIT FLOW ──────────────────────────────────────────
  function handleSubmit() {
    if (!validate()) return;

    document.getElementById('s_bike_id').textContent  = currentBikeCode;
    document.getElementById('s_nickname').textContent = document.getElementById('nickname').value.trim();
    document.getElementById('s_shop_id').textContent  = shopId ? '#' + shopId : 'From URL';
    document.getElementById('s_rpm').textContent      = parseInt(document.getElementById('rpm').value) + ' / min';

    openModal();
  }

  function openModal()  { document.getElementById('confirmModal').classList.add('open'); }
  function closeModal() { document.getElementById('confirmModal').classList.remove('open'); }

  async function confirmCreate() {
    const btn       = document.getElementById('confirmBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    const label     = document.getElementById('confirmLabel');
    const spinner   = document.getElementById('confirmSpinner');

    btn.disabled = true;
    cancelBtn.disabled = true;
    btn.classList.add('loading');

    const payload = {
      bike_id:  currentBikeCode,
      nickname: document.getElementById('nickname').value.trim(),
      shop_id:  document.getElementById("shopIdHiddenInput").value,
      rpm:      parseInt(document.getElementById('rpm').value),
    };

    try {
      const res  = await fetch('/bikes/v1/create-bike', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      closeModal();

      if (res.ok) {
        showToast('success', 'Bike Added', `${payload.nickname} · ${data.bike_code ?? currentBikeCode} is now live in your fleet.`);
        resetForm();
      } else {
        // Always rotate code on failure
        regenCode();

        if (res.status === 409) {
          showToast('error', 'Already Exists', 'A bike with these details exists. A fresh code has been assigned — try again.');
        } else if (res.status === 422) {
          const d = data.detail;
          const msg = (typeof d === 'object' && d.missing_fields)
            ? 'Missing: ' + d.missing_fields.join(', ')
            : (typeof d === 'string' ? d : 'Please check your inputs.');
          showToast('error', 'Validation Error', msg);
        } else if (res.status === 401 || res.status === 403) {
          showToast('error', 'Unauthorized', "You don't have permission to add bikes to this shop.");
        } else {
          showToast('error', 'Server Error', 'Something went wrong. A new code is ready — try again.');
        }
      }
    } catch (e) {
      closeModal();
      regenCode();
      showToast('error', 'Network Error', 'Could not reach the server. A fresh code is ready whenever you retry.');
    } finally {
      btn.disabled = false;
      cancelBtn.disabled = false;
      btn.classList.remove('loading');
    }
  }

  function resetForm() {
    clearErrors();
  }

  // ── TOAST (SweetAlert2) ──────────────────────────────────
  const SwalToast = Swal.mixin({
    toast: true,
    position: 'bottom-end',
    showConfirmButton: false,
    timer: 5500,
    timerProgressBar: true,
    background: '#1C1E26',
    color: '#F0F0F5',
    customClass: {
      popup:         'swal-toast-popup',
      title:         'swal-toast-title',
      htmlContainer: 'swal-toast-html',
      timerProgressBar: 'swal-toast-progress',
    },
    didOpen: (toast) => {
      toast.addEventListener('mouseenter', Swal.stopTimer);
      toast.addEventListener('mouseleave', Swal.resumeTimer);
    }
  });

  function showToast(type, title, msg) {
    const iconColor = type === 'success' ? '#38B6FF' : '#FF4D1C';
    SwalToast.fire({
      icon: type === 'success' ? 'success' : 'error',
      title: title,
      html: `<span style="font-size:12px;color:#8A8FA8;line-height:1.5">${msg}</span>`,
      iconColor: iconColor,
    });
  }

  // Backdrop close
  document.getElementById('confirmModal').addEventListener('click', function(e) {
    if (e.target === this) closeModal();
  });

  // Clear errors on input
  document.getElementById('nickname').addEventListener('input', () => setError('nickname', 'err_nickname', false));
  document.getElementById('rpm').addEventListener('input',      () => setError('rpm',      'err_rpm',      false));

