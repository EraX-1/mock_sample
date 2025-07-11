'use client';

import { useEffect, useState } from 'react';
import ChatSection from '@/components/chat/chat-section';
import SidebarProvider from '@/components/navigation/sidebar-provider';
import {
  getChatRoomApi,
  putChatRoomsApi,
  getSearchIndexTypesForUserApi,
} from '@/services/apiService';
import { ChatIndexType } from '@/types/chat';
import { useParams } from 'next/navigation';

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { id } = useParams(); // useParamsを使用してparamsを取得
  const [chatRoomData, setChatRoomData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [indexType, setIndexType] = useState<ChatIndexType[]>([]);

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        // インデックスタイプの取得
        const { response: indexTypesResponse, error: indexTypesError } =
          await getSearchIndexTypesForUserApi();
        if (indexTypesResponse && indexTypesResponse.length > 0) {
          // 最初のインデックスタイプを初期値として設定
          setIndexType([indexTypesResponse[0].id] as ChatIndexType[]);
        }

        // チャットルームデータの取得
        if (id) {
          const response = await getChatRoomApi({ chat_room_id: id });
          setChatRoomData(response);
        }
      } catch (err) {
        setError('データの取得中にエラーが発生しました。');
      } finally {
        setIsLoading(false);
      }
    };

    fetchInitialData();
  }, [id]);

  const sendChatroomName = async (chatRoomId: string, name: string) => {
    try {
      await putChatRoomsApi({ chat_room_id: chatRoomId, name });
    } catch (error) {
      console.error('Failed to send chatroom name:', error);
    }
  };

  if (isLoading) {
    return (
      <SidebarProvider>
        <div className="flex items-center justify-center h-screen w-full">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </SidebarProvider>
    );
  }

  if (error) {
    return (
      <SidebarProvider>
        <div className="flex items-center justify-center h-screen w-full">
          <div className="text-red-600">{error}</div>
        </div>
      </SidebarProvider>
    );
  }

  return (
    <SidebarProvider>
      <div className="w-full h-full bg-white">
        <ChatSection
          key={Array.isArray(id) ? id[0] : id}
          chatRoomId={Array.isArray(id) ? id[0] : id || ''}
          indexType={indexType}
          setIndexType={setIndexType}
          sendChatroomName={sendChatroomName}
        />
        {children} {/* 子コンポーネントを表示 */}
      </div>
    </SidebarProvider>
  );
}
