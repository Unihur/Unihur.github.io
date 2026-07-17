export function parseList(raw) {
  if (!raw) return []
  const s = String(raw).trim()
  if (s.startsWith('{') && s.endsWith('}')) {
    return s
      .slice(1, -1)
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean)
  }
  return s
    .split(/[,，]/)
    .map((t) => t.trim())
    .filter(Boolean)
}
