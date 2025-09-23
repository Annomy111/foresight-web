import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Toaster } from 'react-hot-toast'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Foresight Analyzer | AI-Powered Probabilistic Forecasting',
  description: 'Advanced ensemble forecasting using multiple AI models for accurate predictions',
  keywords: 'AI forecasting, probabilistic prediction, ensemble methods, geopolitical analysis',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-dark-bg text-gray-100`}>
        {children}
        <Toaster
          position="top-right"
          toastOptions={{
            className: 'bg-dark-card text-white border border-gray-700',
            duration: 4000,
          }}
        />
      </body>
    </html>
  )
}