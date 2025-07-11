'use client';

import { useEffect } from 'react';
import { Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  handleAuthCallbackApi,
  createChatRoomsApi,
} from '@/services/apiService';

function CallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code');
      if (!code) {
        router.push('/signin');
        return;
      }

      const { response, error } = await handleAuthCallbackApi(code);
      if (error) {
        console.error(error);
        router.push('/signin');
        return;
      }
      router.push('/chat');
      // const { response: createChatroomRes } = await createChatRoomsApi();
      // if (createChatroomRes?.id) {
      //   router.push(`/chat/${createChatroomRes.id}`);
      // } else {
      //   router.push("/chat");
      // }
    };

    handleCallback();
  }, [router, searchParams]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="p-8 space-y-6 bg-white rounded-lg">
        <h2 className="text-xl font-bold text-center mb-12">認証中...</h2>
      </div>
    </div>
  );
}

export default function CallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center min-h-screen bg-gray-100">
          <div className="p-8 space-y-6 bg-white rounded-lg">
            <h2 className="text-xl font-bold text-center mb-12">
              読み込み中...
            </h2>
          </div>
        </div>
      }
    >
      <CallbackContent />
    </Suspense>
  );
}
