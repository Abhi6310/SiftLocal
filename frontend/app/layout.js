import './globals.css'

export const metadata = {
  title: 'SiftLocal',
  description: 'Local-first prompt engineering workbench',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
