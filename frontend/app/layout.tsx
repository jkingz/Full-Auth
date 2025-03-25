import { Footer, Navbar } from '@/components/common';
import '@/styles/globals.css';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
const inter = Inter({
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: 'Full Auth',
  description: 'Full authentication with Next.js',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Navbar />
        <div>{children}</div>
        <Footer />
      </body>
    </html>
  );
}
