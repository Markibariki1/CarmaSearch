"use client"

import { useEffect, useRef } from 'react'

interface LogoScrollWheelProps {
  logos: Array<{ src: string; alt: string; href?: string }>
}

export function LogoScrollWheel({ logos }: LogoScrollWheelProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    // Create duplicate logos for seamless loop
    const content = container.innerHTML
    container.innerHTML = content + content + content

    // Reset animation if it gets stuck
    const resetAnimation = () => {
      if (container.scrollLeft >= container.scrollWidth / 3) {
        container.scrollLeft = 0
      }
    }

    const interval = setInterval(resetAnimation, 1000)

    return () => clearInterval(interval)
  }, [logos])

  return (
    <div className="overflow-hidden py-8">
      <div
        ref={containerRef}
        className="flex gap-8 animate-scroll"
        style={{
          animation: 'scroll 30s linear infinite',
        }}
      >
        {logos.map((logo, index) => (
          <div
            key={index}
            className="flex-shrink-0 flex items-center justify-center h-10 opacity-60 hover:opacity-100 transition-opacity duration-300"
          >
            {logo.href ? (
              <a href={logo.href} target="_blank" rel="noopener noreferrer" className="h-full">
                <img
                  src={logo.src}
                  alt={logo.alt}
                  className="h-full w-auto object-contain filter brightness-0 invert"
                />
              </a>
            ) : (
              <img
                src={logo.src}
                alt={logo.alt}
                className="h-full w-auto object-contain filter brightness-0 invert"
              />
            )}
          </div>
        ))}
      </div>
      
      <style jsx global>{`
        @keyframes scroll {
          0% {
            transform: translateX(0);
          }
          100% {
            transform: translateX(-33.333%);
          }
        }
      `}</style>
    </div>
  )
}
