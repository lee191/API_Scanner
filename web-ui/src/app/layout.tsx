import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Shadow API Scanner",
  description: "Web API Discovery and Security Vulnerability Scanner",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
