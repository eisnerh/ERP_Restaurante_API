/**
 * Preferencia de casa (localStorage) y toasts Bootstrap.
 */
(function () {
  var KEY = 'erp_preferred_franchisee_id';

  function esc(s) {
    if (!s) return '';
    var d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }

  window.rememberFranchiseePreference = function (fid) {
    try {
      if (fid != null && fid !== '') localStorage.setItem(KEY, String(fid));
    } catch (e) {}
  };

  /** Si la URL no trae franchisee_id, redirige una vez para alinear sesión con la última casa elegida. */
  window.applyPreferredFranchiseeRedirect = function () {
    try {
      var pref = localStorage.getItem(KEY);
      if (!pref || !/^\d+$/.test(pref)) return;
      var url = new URL(window.location.href);
      if (url.searchParams.has('franchisee_id')) return;
      var sel = document.getElementById('navbar-franchisee-select') || document.getElementById('franchisee-select');
      if (!sel) return;
      if (String(sel.value) !== String(pref)) {
        url.searchParams.set('franchisee_id', pref);
        window.location.replace(url.toString());
      }
    } catch (e) {}
  };

  window.showToast = function (message, variant) {
    variant = variant || 'success';
    var wrap = document.getElementById('toast-container');
    if (!wrap) {
      try {
        alert(message);
      } catch (e) {}
      return;
    }
    var bg =
      variant === 'error' || variant === 'danger'
        ? 'danger'
        : variant === 'warning'
          ? 'warning'
          : variant === 'info'
            ? 'info'
            : 'success';
    var extra = bg === 'warning' ? ' text-dark' : '';
    var el = document.createElement('div');
    el.className = 'toast align-items-center text-bg-' + bg + extra + ' border-0';
    el.setAttribute('role', 'alert');
    el.setAttribute('aria-live', 'polite');
    el.innerHTML =
      '<div class="d-flex">' +
      '<div class="toast-body">' +
      esc(message) +
      '</div>' +
      '<button type="button" class="btn-close' +
      (bg === 'warning' ? '' : ' btn-close-white') +
      ' me-2 m-auto" data-bs-dismiss="toast" aria-label="Cerrar"></button>' +
      '</div>';
    wrap.appendChild(el);
    if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
      var t = new bootstrap.Toast(el, { delay: 4000 });
      el.addEventListener('hidden.bs.toast', function () {
        el.remove();
      });
      t.show();
    } else {
      el.classList.add('show');
      setTimeout(function () {
        el.remove();
      }, 4000);
    }
  };
})();
