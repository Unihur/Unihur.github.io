// 时间/数字格式化工具集合

/**
 * 将 ISO/字符串时间格式化为 YYYY-MM-DD
 * @param {string|number|Date} dateStr
 * @returns {string}
 */
export function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  if (Number.isNaN(d.getTime())) return ''
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/**
 * 秒数格式化为 mm:ss
 * @param {number} time
 * @returns {string}
 */
export function formatDuration(time) {
  if (!time || Number.isNaN(time)) return '00:00'
  const m = Math.floor(time / 60)
    .toString()
    .padStart(2, '0')
  const s = Math.floor(time % 60)
    .toString()
    .padStart(2, '0')
  return `${m}:${s}`
}
