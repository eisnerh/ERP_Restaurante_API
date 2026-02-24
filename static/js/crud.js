/* Helpers para CRUD contra la API. Si el servidor devuelve HTML (ej. 404), no se intenta parsear como JSON. */
var API_TIMEOUT_MS = 20000;

function fetchWithTimeout(url, opts, timeout) {
  timeout = timeout || API_TIMEOUT_MS;
  var controller = new AbortController();
  var tid = setTimeout(function() { controller.abort(); }, timeout);
  var p = fetch(url, Object.assign({}, opts || {}, { signal: controller.signal }));
  return p.finally(function() { clearTimeout(tid); });
}

function safeJson(r) {
  return r.text().then(function(t) {
    if (!r.ok) {
      if (t && t.trim().startsWith('<')) throw new Error(r.status + ' ' + r.statusText + ' (respuesta HTML)');
      try { var j = JSON.parse(t); throw new Error(j.error || j.message || r.statusText); } catch (e) {
        if (e instanceof SyntaxError) throw new Error(t || r.statusText);
        throw e;
      }
    }
    if (r.status === 204 || !t) return {};
    if (t.trim().startsWith('<')) throw new Error('La API devolvió HTML en lugar de JSON. Comprueba la URL.');
    return JSON.parse(t);
  });
}
function apiGet(url) {
  return fetchWithTimeout(url).then(safeJson).catch(function(e) {
    if (e.name === 'AbortError') throw new Error('Tiempo de espera agotado. Verifica la conexión.');
    throw e;
  });
}
function apiPost(url, data) {
  return fetchWithTimeout(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data || {}),
  }).then(safeJson).catch(function(e) {
    if (e.name === 'AbortError') throw new Error('Tiempo de espera agotado. Verifica la conexión.');
    throw e;
  });
}
function apiPut(url, data) {
  return fetchWithTimeout(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data || {}),
  }).then(safeJson).catch(function(e) {
    if (e.name === 'AbortError') throw new Error('Tiempo de espera agotado. Verifica la conexión.');
    throw e;
  });
}
function apiDelete(url) {
  return fetchWithTimeout(url, { method: 'DELETE' }).then(safeJson).catch(function(e) {
    if (e.name === 'AbortError') throw new Error('Tiempo de espera agotado. Verifica la conexión.');
    throw e;
  });
}
function showMsg(el, text, type) {
  if (!el) return;
  el.textContent = text;
  el.className = 'msg alert ' + (type === 'error' ? 'alert-danger' : type === 'success' ? 'alert-success' : 'alert-info');
  el.style.display = 'block';
}
function hideMsg(el) {
  if (el) el.style.display = 'none';
}
function modalShow(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add('show');
}
function modalHide(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove('show');
}
