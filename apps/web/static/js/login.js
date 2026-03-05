(() => {
  const API_URL = "/auth/v1/login";
  const DASHBOARD_URL = "/dashboard";

  const usernameEl = document.getElementById("username");
  const pinEl = document.getElementById("pin");
  const btn = document.getElementById("loginBtn");

  // Default category (per your comment). Change to "employee" if needed.
  const DEFAULT_CATEGORY = "owner";

  // ---- Flash message UI (JS-only) ----
  function ensureFlashHost() {
    let host = document.getElementById("flashHost");
    if (host) return host;

    host = document.createElement("div");
    host.id = "flashHost";
    host.setAttribute(
      "style",
      [
        "position: fixed",
        "top: 18px",
        "right: 18px",
        "z-index: 9999",
        "display: flex",
        "flex-direction: column",
        "gap: 10px",
        "max-width: min(420px, calc(100vw - 36px))",
      ].join(";")
    );
    document.body.appendChild(host);
    return host;
  }

  function flash(message, type = "info") {
    const host = ensureFlashHost();

    const el = document.createElement("div");
    const bg =
      type === "success"
        ? "#0ea5e9"
        : type === "error"
        ? "#ef4444"
        : "#111827";

    el.setAttribute(
      "style",
      [
        `background: ${bg}`,
        "color: #fff",
        "padding: 12px 14px",
        "border-radius: 12px",
        "box-shadow: 0 10px 25px rgba(0,0,0,.18)",
        "font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif",
        "font-size: 14px",
        "line-height: 1.35",
        "opacity: 0",
        "transform: translateY(-6px)",
        "transition: opacity .18s ease, transform .18s ease",
        "word-wrap: break-word",
      ].join(";")
    );

    el.textContent = message;
    host.appendChild(el);

    // animate in
    requestAnimationFrame(() => {
      el.style.opacity = "1";
      el.style.transform = "translateY(0)";
    });

    // auto-dismiss
    const ttl = type === "success" ? 1800 : 3200;
    setTimeout(() => {
      el.style.opacity = "0";
      el.style.transform = "translateY(-6px)";
      setTimeout(() => el.remove(), 220);
    }, ttl);
  }

  // ---- Button loading state ----
  function setLoading(isLoading) {
    if (!btn) return;
    btn.disabled = isLoading;
    btn.setAttribute("aria-busy", String(isLoading));

    if (isLoading) {
      btn.dataset.originalText = btn.textContent;
      btn.textContent = "Signing in…";
      btn.style.opacity = "0.85";
      btn.style.cursor = "not-allowed";
    } else {
      btn.textContent = btn.dataset.originalText || "CONTINUE";
      btn.style.opacity = "";
      btn.style.cursor = "";
      delete btn.dataset.originalText;
    }
  }

  function validateInputs(username, pin) {
    if (!username) return "Please enter your username/email.";
    if (!pin) return "Please enter your PIN.";
    return null;
  }

  async function safeReadJson(res) {
    // Handles cases where backend returns non-JSON or empty body
    try {
      return await res.json();
    } catch {
      return null;
    }
  }

  async function login() {
    if (!usernameEl || !pinEl || !btn) {
      console.error("Missing required elements (#username, #pin, #loginBtn).");
      return;
    }

    const username = usernameEl.value.trim().toLowerCase();
    const pin = pinEl.value; // keep as-is (could be numeric string)
    const category = DEFAULT_CATEGORY;

    const validationError = validateInputs(username, pin);
    if (validationError) {
      flash(validationError, "error");
      return;
    }

    setLoading(true);

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include", // IMPORTANT: allow auth cookies to be set/used
        body: JSON.stringify({ username, pin, category }),
      });

      const data = await safeReadJson(res);
      const msg =
        (data && (data.detail || data.message)) ||
        (res.ok ? "Login successful." : "Request failed.");

      if (res.ok) {
        flash(msg, "success");
        // redirect after a tiny beat so user sees the toast
        setTimeout(() => {
          window.location.assign(DASHBOARD_URL);
        }, 350);
      } else {
        flash(msg, "error");
      }
    } catch (err) {
      console.error(err);
      flash("Network error. Please try again.", "error");
    } finally {
      setLoading(false);
    }
  }

  // Click to login
  if (btn) btn.addEventListener("click", login);

  // Enter key to login (from either input)
  function onEnter(e) {
    if (e.key === "Enter") login();
  }
  if (usernameEl) usernameEl.addEventListener("keydown", onEnter);
  if (pinEl) pinEl.addEventListener("keydown", onEnter);
})();