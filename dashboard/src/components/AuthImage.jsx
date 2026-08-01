import { useEffect, useState } from 'react'
import { authHeader } from '../auth.js'

/**
 * An <img> for endpoints behind the bearer token. The browser won't attach an
 * Authorization header to a plain src, so the bytes are fetched and handed over
 * as an object URL instead.
 */
export default function AuthImage({ src, alt, className }) {
  const [url, setUrl] = useState(null)

  useEffect(() => {
    if (!src) return undefined
    let objectUrl = null
    let cancelled = false

    fetch(src, { headers: authHeader() })
      .then((r) => (r.ok ? r.blob() : Promise.reject(new Error(String(r.status)))))
      .then((blob) => {
        if (cancelled) return
        objectUrl = URL.createObjectURL(blob)
        setUrl(objectUrl)
      })
      .catch(() => setUrl(null))

    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [src])

  if (!url) return <span className="insp-thumb-placeholder" />
  return <img src={url} alt={alt} className={className} />
}
