/** Iconos de categoría (API: icon, icon_emoji). */
function catIconHtml(c) {
  var ic = (c && c.icon) ? String(c.icon).replace(/^bi-/, '') : 'tag';
  return '<i class="bi bi-' + ic + ' category-icon" aria-hidden="true"></i>';
}
function categoryOptionLabel(c) {
  var em = c.icon_emoji ? c.icon_emoji + ' ' : '';
  return em + (c.name || '');
}
