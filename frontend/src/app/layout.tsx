import './globals.css'

export const metadata = {
  title: 'Email AI Assistant',
  description: 'AI-powered email management and response system',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
} 