import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Pulsecheck — API load-testing observatory",
  description:
    "Fire a burst at any HTTP endpoint; get a latency heatmap, failure breakdown, and an AI-written health report.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
