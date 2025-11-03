import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "YouTube Analytics",
  description: "YouTube channel and video analytics platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
