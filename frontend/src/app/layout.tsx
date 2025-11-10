import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Alpha Transformer - Your AI Trading Dashboard',
  description: 'Your custom 24/7 AI trading agent made for you.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-mono">{children}</body>
    </html>
  )
}