import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Conversational BI Dashboard",
  description:
    "Ask questions in plain English and get instant, interactive business intelligence charts powered by AI.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
