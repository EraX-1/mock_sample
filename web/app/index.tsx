import type { NextPage } from 'next';
import { useRouter } from 'next/router';
import { CircularProgress } from '@mui/material';
import { useEffect, useState } from 'react';

const Frame: NextPage = () => {
  const router = useRouter();
  const isReady = router.isReady;
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsLoading(false);
  }, [isReady]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <CircularProgress />
      </div>
    );
  }

  router.push('/chat');

  return null;
};

export default Frame;
