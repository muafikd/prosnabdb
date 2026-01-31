/**
 * Hosts that return 403 when loading images in <img> from our origin (e.g. Google Drive).
 * For these we use our backend proxy so the browser loads the image from our domain.
 */
const PROXY_HOSTS = [
  'drive.google.com',
  'www.drive.google.com',
  'lh3.googleusercontent.com',
  'lh4.googleusercontent.com',
  'lh5.googleusercontent.com',
  'lh6.googleusercontent.com',
  'disk.yandex.ru',
  'disk.yandex.com',
  'yadi.sk',
]

function getHost(url: string): string | null {
  try {
    const u = new URL(url)
    return u.hostname.toLowerCase()
  } catch {
    return null
  }
}

/**
 * Returns URL suitable for <img src>.
 * - Local /media/...: use current page origin so images load from same host (works in Docker with nginx /media/).
 * - Google Drive / Yandex Disk: use backend proxy to avoid 403.
 * - Other URLs: return as-is.
 */
export function getImageSrc(url: string | undefined | null): string {
  if (!url || typeof url !== 'string') return ''
  const trimmed = url.trim()
  // Local media (after import): load from same origin so nginx serves /media/ from volume
  if (trimmed.startsWith('/media/')) {
    if (typeof window !== 'undefined' && window.location?.origin) {
      return window.location.origin + trimmed
    }
    const apiBase = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')
    const origin = apiBase.replace(/\/api\/?$/, '')
    return origin ? `${origin}${trimmed}` : trimmed
  }
  const host = getHost(trimmed)
  if (!host || !PROXY_HOSTS.some((h) => host === h)) return trimmed
  const base = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')
  return `${base}/proxy-image/?url=${encodeURIComponent(trimmed)}`
}
