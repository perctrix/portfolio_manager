import type { Metadata } from "next";
import localFont from "next/font/local";
import "../globals.css";
import Footer from "@/components/Footer";
import { NextIntlClientProvider } from 'next-intl';
import { getMessages, setRequestLocale } from 'next-intl/server';
import { notFound } from 'next/navigation';
import { locales } from '@/i18n/request';
import LanguageSwitcher from '@/components/LanguageSwitcher';

const geistSans = localFont({
  src: "../../node_modules/geist/dist/fonts/geist-sans/Geist-Regular.woff2",
  variable: "--font-geist-sans",
  weight: "100 900",
  fallback: ['system-ui', 'arial'],
});

const geistMono = localFont({
  src: "../../node_modules/geist/dist/fonts/geist-mono/GeistMono-Regular.woff2",
  variable: "--font-geist-mono",
  weight: "100 900",
  fallback: ['monospace'],
});

export const metadata: Metadata = {
  title: "Portfolio Manager",
  description: "A lightweight, privacy-focused portfolio management and analysis tool with comprehensive performance metrics.",
};

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export default async function LocaleLayout({
  children,
  params
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;

  if (!locales.includes(locale as typeof locales[number])) {
    notFound();
  }

  setRequestLocale(locale);
  const messages = await getMessages();

  return (
    <html lang={locale}>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased flex flex-col min-h-screen`}
      >
        <NextIntlClientProvider messages={messages}>
          <div className="fixed top-4 right-4 z-50">
            <LanguageSwitcher />
          </div>
          {children}
          <Footer />
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
