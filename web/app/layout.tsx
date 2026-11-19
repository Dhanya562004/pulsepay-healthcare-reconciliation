import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "PulsePay — Healthcare Payments Console",
  description: "Billing, payments, and reconciliation management console",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 min-h-screen flex flex-col antialiased selection:bg-sky-500/30 selection:text-sky-200">
        {/* Accessibility: Skip to Content Link */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:rounded-lg focus:bg-sky-500 focus:px-4 focus:py-2.5 focus:text-sm focus:font-semibold focus:text-slate-950 focus:shadow-xl focus:outline-none focus:ring-2 focus:ring-white"
        >
          Skip to content
        </a>

        {/* Global Navigation Header */}
        <header className="sticky top-0 z-40 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <Link
              href="/payments"
              className="flex items-center gap-2.5 font-bold text-lg text-slate-100 hover:text-sky-400 transition-colors focus:outline-none focus:ring-2 focus:ring-sky-500 rounded-md p-1"
            >
              <span className="text-xl" aria-hidden="true">🩺</span>
              <span>PulsePay</span>
              <span className="hidden sm:inline-block text-xs font-normal text-slate-400 border border-slate-700/80 rounded px-2 py-0.5 ml-1">
                Reconciliation Console
              </span>
            </Link>

            <nav aria-label="Main Navigation" className="flex items-center gap-4">
              <Link
                href="/payments"
                className="text-sm font-medium text-slate-200 hover:text-sky-400 transition-colors px-3 py-1.5 rounded-md hover:bg-slate-800/60 focus:outline-none focus:ring-2 focus:ring-sky-500"
              >
                Payments
              </Link>
            </nav>
          </div>
        </header>

        {/* Main Page Landmark */}
        <main id="main-content" className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 focus:outline-none">
          {children}
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-900 bg-slate-950/50 py-6 text-center text-xs text-slate-500">
          <p>PulsePay Healthcare Billing, Payments & Reconciliation Simulation</p>
        </footer>
      </body>
    </html>
  );
}
