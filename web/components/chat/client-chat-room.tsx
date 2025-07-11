'use client';

import { useEffect, useState } from 'react';
import ChatSection from '@/components/chat/chat-section';
import SidebarProvider from '@/components/navigation/sidebar-provider';
import { putChatRoomsApi } from '@/services/apiService';
import { ChatIndexType } from '@/types/chat';

export default function ClientChatRoom({ chatRoomId }: { chatRoomId: string }) {
  const defaultIndex = JSON.parse(
    process.env.NEXT_PUBLIC_SEARCH_INDEX_NAME_ID_LIST ?? '[]'
  )[0] as ChatIndexType;
  const [indexType, setIndexType] = useState<ChatIndexType[]>([defaultIndex]);

  const sendChatroomName = async (chatRoomId: string, name: string) => {
    try {
      await putChatRoomsApi({ chat_room_id: chatRoomId, name });
    } catch (error) {
      console.error('Failed to send chatroom name:', error);
    }
  };

  return (
    <SidebarProvider>
      <div className="w-full h-full bg-white">
        <ChatSection
          key={chatRoomId}
          chatRoomId={chatRoomId}
          indexType={indexType}
          setIndexType={setIndexType}
          sendChatroomName={sendChatroomName}
        />
      </div>
    </SidebarProvider>
  );
}
