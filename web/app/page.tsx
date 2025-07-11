'use client';

import type { NextPage } from 'next';
import { useRouter } from 'next/navigation';
import { CircularProgress } from '@mui/material';
import { useEffect, useState } from 'react';

const Frame: NextPage = () => {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false);
      router.push('/chat');
    }, 100);
    return () => clearTimeout(timer);
  }, [router]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <CircularProgress />
      </div>
    );
  }

  return null;
};

export default Frame;
