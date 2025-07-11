'use client';

import './global.css';
import '@cyntler/react-doc-viewer/dist/index.css';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

// Create a client
const queryClient = new QueryClient();

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  useEffect(() => {
    const handleAuthError = () => {
      router.push('/signin');
    };
    window.addEventListener('authError', handleAuthError);
  }, [router]);

  return (
    <html lang="ja">
      <head>
        <title>{process.env.NEXT_PUBLIC_CORE_NAME}</title>
        <meta
          name="viewport"
          content="minimum-scale=1, initial-scale=1, width=device-width"
        />
      </head>
      <body>
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </body>
    </html>
  );
}
