import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";
import "./globals.css";
import "./app-shell.css";

export const metadata: Metadata = {
  title: "Revenue Intelligence OS",
  description: "Production-shaped operator console for causal revenue memory."
};

const navItems = [
  ["Deals", "/deals"],
  ["Accounts", "/accounts"],
  ["Calls", "/calls"],
  ["Forecast", "/forecast"],
  ["Coaching", "/coaching"],
  ["Engage", "/engage"],
  ["Assistant", "/assistant"],
  ["Admin", "/admin"],
  ["Ingestion", "/ingestion"]
] as const;

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <div className="root-frame">
          <header className="global-nav">
            <Link className="global-brand" href="/deals">
              <span>Revenue Intelligence OS</span>
              <code>HydraDB memory</code>
            </Link>
            <nav className="global-nav-links" aria-label="Primary">
              {navItems.map(([label, href]) => (
                <Link href={href} key={href}>
                  {label}
                </Link>
              ))}
            </nav>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
