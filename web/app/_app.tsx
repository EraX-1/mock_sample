import { Fragment } from 'react';
import Head from 'next/head';
import type { AppProps } from 'next/app';
import './global.css';
import '@cyntler/react-doc-viewer/dist/index.css';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

// Create a client
const queryClient = new QueryClient();

function MyApp({ Component, pageProps }: AppProps) {
  const router = useRouter();
  useEffect(() => {
    const handleAuthError = () => {
      // 認証エラー発生時にリダイレクト
      router.push('/signin');
    };
    window.addEventListener('authError', handleAuthError);
  }, [router]);
  return (
    <Fragment>
      <Head>
        <title>jmu</title>
        <meta
          name="viewport"
          content="minimum-scale=1, initial-scale=1, width=device-width"
        />
      </Head>
      <QueryClientProvider client={queryClient}>
        <Component {...pageProps} />
      </QueryClientProvider>
    </Fragment>
  );
}

export default MyApp;
