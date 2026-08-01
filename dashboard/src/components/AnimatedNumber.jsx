import { useEffect, useRef, useState } from 'react'

const prefersReduced =
  typeof window !== 'undefined' &&
  window.matchMedia &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches

/**
 * Counts up from 0 to `value` on mount (and whenever `value` changes).
 * `format` maps the current numeric value to display text.
 */
export default function AnimatedNumber({ value, format = (v) => Math.round(v).toString(), duration = 900 }) {
  const [display, setDisplay] = useState(prefersReduced ? value : 0)
  const raf = useRef(null)

  useEffect(() => {
    if (prefersReduced) {
      setDisplay(value)
      return
    }
    const start = performance.now()
    const from = 0
    const tick = (now) => {
      const t = Math.min((now - start) / duration, 1)
      const eased = 1 - Math.pow(1 - t, 3) // easeOutCubic
      setDisplay(from + (value - from) * eased)
      if (t < 1) raf.current = requestAnimationFrame(tick)
    }
    raf.current = requestAnimationFrame(tick)

    // rAF is paused in a background tab, which would otherwise leave every
    // headline number frozen at 0 until the tab is focused. Snap to the real
    // value once the animation window has passed; a no-op if it already ran.
    const settle = setTimeout(() => setDisplay(value), duration + 50)

    return () => {
      cancelAnimationFrame(raf.current)
      clearTimeout(settle)
    }
  }, [value, duration])

  return <>{format(display)}</>
}
