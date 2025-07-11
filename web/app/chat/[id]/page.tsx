'use client';

import { useEffect, useState } from 'react';
import { getChatRoomApi } from '@/services/apiService';
import { useParams } from 'next/navigation';
import { CircularProgress } from '@mui/material';

export default function ChatRoomPage() {
  const { id } = useParams();
  const [chatRoomData, setChatRoomData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchChatRoomData = async () => {
      try {
        const response = await getChatRoomApi({ chat_room_id: id });
        setChatRoomData(response);
      } catch (err) {
        setError('チャットルームのデータを取得できませんでした。');
      } finally {
      }
    };

    fetchChatRoomData();
  }, [id]);

  if (error) {
    return <div>{error}</div>;
  }

  return null;
}
