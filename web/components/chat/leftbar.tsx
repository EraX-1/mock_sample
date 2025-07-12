'use client';

import { FC, useEffect, useState } from 'react';
import {
  Box,
  Tooltip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  OutlinedInput,
  Chip,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  IconButton,
} from '@mui/material';
import SplitScreenIcon from '@/components/icon/splitScreenIcon';
import EditIcon from '@/components/icon/editIcon';
import DeleteIcon from '@mui/icons-material/Delete';
import ChatHistoryItem from './chat-history-item';
import {
  getChatChatRoomsApi,
  createChatRoomsApi,
  deleteChatMessagesApi,
  logoutApi,
  dropoutApi,
  getUserInfoApi,
  getMaintenanceStatusApi,
  getSearchIndexTypesForUserApi,
} from '@/services/apiService';
import { ChatIndexType } from '@/types/chat';
import { useRouter, usePathname } from 'next/navigation';
type ChatRoom = {
  id: string;
  name: string;
  prompt?: string;
  created_at: string;
};

export type LeftbarProps = {
  isLeftbarOpen: boolean;
  setIsLeftbarOpen: (open: boolean) => void;
  sendChatroomName: (chat_room_id: string, name: string) => void;
  isMobile: boolean;
};

const Leftbar: FC<LeftbarProps> = ({
  setIsLeftbarOpen,
  isLeftbarOpen,
  sendChatroomName,
  isMobile,
}) => {
  const router = useRouter();
  const pathname = usePathname();
  const [isLoading, setIsLoading] = useState<any>(true);
  const [error, setError] = useState<any>();
  const [chatRooms, setChatRooms] = useState<ChatRoom[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [userInfo, setUserInfo] = useState<any>();
  const [indexTypeOptions, setIndexTypeOptions] = useState<
    { value: string; label: string }[]
  >([]);
  const [isSelectMode, setIsSelectMode] = useState<boolean>(false);
  const [selectedChatRooms, setSelectedChatRooms] = useState<string[]>([]);
  const [bulkDeleteDialogOpen, setBulkDeleteDialogOpen] =
    useState<boolean>(false);
  const [gptDialogOpen, setGptDialogOpen] = useState<boolean>(false);

  useEffect(() => {
    (async () => {
      // メンテナンスモードのチェック
      const { response: maintenanceResponse, error: maintenanceError } =
        await getMaintenanceStatusApi();
      console.log(maintenanceResponse);
      if (maintenanceResponse?.maintenance) {
        const maintenanceMessage = encodeURIComponent(
          maintenanceResponse.message || ''
        );
        router.push(`/maintenance?message=${maintenanceMessage}`);
        return;
      }

      // インデックスタイプの取得
      const { response: indexTypesResponse, error: indexTypesError } =
        await getSearchIndexTypesForUserApi();
      if (indexTypesResponse) {
        const options = indexTypesResponse.map((indexType: any) => ({
          value: indexType.id,
          label: indexType.folder_name,
        }));
        setIndexTypeOptions(options);
      }

      // チャットルームの取得
      const { response, error: resError } = await getChatChatRoomsApi();
      setIsLoading(false);
      if (response) {
        setChatRooms(
          response.map((_chatRoom: any) => ({
            id: _chatRoom.id,
            name: _chatRoom.name,
            prompt: _chatRoom.prompt ?? '',
            created_at: _chatRoom.created_at,
          }))
        );
      }
      setError(resError);
    })();

    (async () => {
      const { response, error: resError } = await getUserInfoApi();
      setIsLoading(false);
      if (response) {
        setUserInfo(response);
        console.log(response);
      }
      setError(resError);
    })();
  }, [router]);

  const toggleSidebar = () => {
    setIsLeftbarOpen(!isLeftbarOpen);
  };

  const createChatRoom = async () => {
    try {
      const { response } = await createChatRoomsApi();

      // APIレスポンスを使って正確なデータに更新
      const createdChatRoom = {
        id: response.id,
        name: response.name,
        prompt: response.prompt ?? '',
        created_at: response.created_at,
      };

      setChatRooms(prevChatRooms => [...prevChatRooms, createdChatRoom]);

      // Linkを使用して遷移するための状態を設定
      return createdChatRoom;
    } catch (error) {
      throw error;
    }
  };

  const deleteChatRoom = async (id: string) => {
    // 現在のチャットルームIDを取得
    const currentChatRoomId = getCurrentChatRoomId();

    // 削除前のセッションを保存（ロールバック用）
    const chatRoomToDelete = chatRooms.find(chatRoom => chatRoom.id === id);

    // 楽観的更新: APIレスポンス待たずに即座にUIを更新
    setChatRooms(prevChatRooms =>
      prevChatRooms.filter(chatRoom => chatRoom.id !== id)
    );

    try {
      const params = {
        chat_room_id: id,
      };
      await deleteChatMessagesApi(params);

      // 削除が成功した場合、現在開いているルームが削除されたかチェック
      if (currentChatRoomId === id) {
        router.push('/chat');
      }
    } catch (error) {
      // エラー時は削除をロールバック
      if (chatRoomToDelete) {
        setChatRooms(prevChatRooms => [...prevChatRooms, chatRoomToDelete]);
      }
      throw error;
    }
  };

  const handleLogout = async () => {
    const { response } = await logoutApi();
    if (response) {
      router.push('/signin');
    }
  };

  const handleDropout = async () => {
    if (window.confirm('本当に退会しますか？この操作は取り消せません。')) {
      const { response } = await dropoutApi();
      if (response) {
        router.push('/signin');
      }
    }
  };

  // フィルタリングされたチャットルームを取得する関数
  const filteredChatRooms = chatRooms.filter(chatRoom =>
    chatRoom.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // 現在のチャットルームIDを取得する関数
  const getCurrentChatRoomId = () => {
    const match = pathname.match(/^\/chat\/(.+)$/);
    return match ? match[1] : null;
  };

  // 一括削除処理
  const handleBulkDelete = async () => {
    // 現在のチャットルームIDを取得
    const currentChatRoomId = getCurrentChatRoomId();

    // 削除前の状態を保存（復元用）
    const chatRoomsBeforeDelete = [...chatRooms];

    // 楽観的更新: 選択されたチャットルームを即座にUIから削除
    setChatRooms(prevChatRooms =>
      prevChatRooms.filter(chatRoom => !selectedChatRooms.includes(chatRoom.id))
    );

    // エラーフラグ
    let hasError = false;

    // 選択されたチャットルームを順番に削除
    for (const chatRoomId of selectedChatRooms) {
      try {
        const params = {
          chat_room_id: chatRoomId,
        };
        await deleteChatMessagesApi(params);
      } catch (error) {
        console.error(
          `チャットルーム ${chatRoomId} の削除に失敗しました:`,
          error
        );
        hasError = true;
        break;
      }
    }

    // エラーが発生した場合は状態を復元
    if (hasError) {
      setChatRooms(chatRoomsBeforeDelete);
      alert('一部のチャットルームの削除に失敗しました。');
    } else {
      // 削除が成功した場合、現在開いているルームが削除対象に含まれているかチェック
      if (currentChatRoomId && selectedChatRooms.includes(currentChatRoomId)) {
        router.push('/chat');
      }
    }

    // 選択モードを終了し、選択をクリア
    setIsSelectMode(false);
    setSelectedChatRooms([]);
    setBulkDeleteDialogOpen(false);
  };

  // チャットルーム選択の切り替え
  const toggleChatRoomSelection = (chatRoomId: string) => {
    setSelectedChatRooms(prev => {
      if (prev.includes(chatRoomId)) {
        return prev.filter(id => id !== chatRoomId);
      } else {
        return [...prev, chatRoomId];
      }
    });
  };

  // 一括選択モードの切り替え
  const toggleSelectMode = () => {
    setIsSelectMode(!isSelectMode);
    if (isSelectMode) {
      // 選択モードを終了する時は選択をクリア
      setSelectedChatRooms([]);
    }
  };

  return (
    <>
      {/* モバイル時のオーバーレイ背景 */}
      {isMobile && isLeftbarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={() => setIsLeftbarOpen(false)}
        />
      )}

      {/* サイドバー */}
      <aside
        className={`
          ${isMobile ? 'fixed' : 'relative'}
          self-stretch w-60 min-h-screen bg-gray flex flex-col items-center px-3 py-4 gap-3 font-sans
          transition-transform duration-300 ease-in-out
          ${isMobile ? 'z-50' : ''}
          ${isLeftbarOpen ? 'translate-x-0' : '-translate-x-full'}
          ${isMobile ? 'left-0 top-0' : ''}
        `}
        style={{
          backgroundColor: '#f5f5f5',
        }}
      >
        <div className="flex flex-col w-full flex-grow overflow-auto">
          <div className="flex items-center justify-between w-full pb-4">
            <Tooltip title="サイドバーを閉じる" arrow placement="right">
              <button className="cursor-pointer border-none p-0 bg-transparent">
                <SplitScreenIcon
                  className="w-6 h-6 text-slategray hover:brightness-50 hover:contrast-200"
                  onClick={toggleSidebar}
                />
              </button>
            </Tooltip>
            <div className="flex">
              {isSelectMode ? (
                <>
                  <Tooltip title="選択モードを終了" arrow placement="top">
                    <button
                      className="cursor-pointer border-none p-0 bg-transparent mr-2"
                      onClick={toggleSelectMode}
                    >
                      キャンセル
                    </button>
                  </Tooltip>
                  <Tooltip title="選択したチャットを削除" arrow placement="top">
                    <span>
                      <Button
                        size="small"
                        variant="outlined"
                        color="error"
                        disabled={selectedChatRooms.length === 0}
                        onClick={() => setBulkDeleteDialogOpen(true)}
                        startIcon={<DeleteIcon />}
                        sx={{
                          fontSize: '0.7rem',
                          py: 0.5,
                          borderRadius: '4px',
                        }}
                      >
                        削除{' '}
                        {selectedChatRooms.length > 0 &&
                          `(${selectedChatRooms.length})`}
                      </Button>
                    </span>
                  </Tooltip>
                </>
              ) : (
                <>
                  <Tooltip title="チャットを選択して削除" arrow placement="top">
                    <Button
                      size="small"
                      variant="text"
                      startIcon={<DeleteIcon fontSize="small" />}
                      onClick={toggleSelectMode}
                      sx={{
                        mr: 1,
                        fontSize: '0.7rem',
                        color: 'text.secondary',
                        py: 0.5,
                      }}
                    >
                      選択削除
                    </Button>
                  </Tooltip>
                  <Tooltip title="新しいチャット" arrow placement="left">
                    <Button
                      variant="contained"
                      size="small"
                      startIcon={<EditIcon />}
                      onClick={createChatRoom}
                      sx={{
                        fontSize: '0.7rem',
                        py: 0.5,
                        bgcolor: '#f0f0f0',
                        color: 'text.primary',
                        boxShadow: 'none',
                        '&:hover': {
                          bgcolor: '#e0e0e0',
                          boxShadow: 'none',
                        },
                      }}
                    >
                      新規作成
                    </Button>
                  </Tooltip>
                </>
              )}
            </div>
          </div>

          {/* 検索フィールドを追加 */}
          <TextField
            fullWidth
            size="small"
            placeholder="チャットルームを検索"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            sx={{ mt: 2, mb: 2 }}
          />

          <div className="flex flex-col pt-2 items-center justify-start overflow-y-auto">
            {isLoading ? (
              <div>読み込み中...</div>
            ) : error ? (
              <div>エラーが発生しました: {error.message}</div>
            ) : (
              filteredChatRooms
                .slice()
                .reverse()
                .map((chatRoom: ChatRoom) => (
                  <ChatHistoryItem
                    key={chatRoom.id}
                    id={chatRoom.id}
                    title={chatRoom.name}
                    deleteChatRoom={() => deleteChatRoom(chatRoom.id)}
                    sendChatroomName={sendChatroomName}
                    isSelectMode={isSelectMode}
                    isSelected={selectedChatRooms.includes(chatRoom.id)}
                    onToggleSelect={() => toggleChatRoomSelection(chatRoom.id)}
                  />
                ))
            )}
          </div>
        </div>

        {/* 一括削除確認ダイアログ */}
        <Dialog
          open={bulkDeleteDialogOpen}
          onClose={() => setBulkDeleteDialogOpen(false)}
          aria-labelledby="bulk-delete-dialog-title"
          aria-describedby="bulk-delete-dialog-description"
        >
          <DialogTitle id="bulk-delete-dialog-title">
            複数のチャットルームを削除
          </DialogTitle>
          <DialogContent>
            <DialogContentText id="bulk-delete-dialog-description">
              選択した {selectedChatRooms.length}{' '}
              件のチャットルームを削除してもよろしいですか？この操作は取り消せません。
            </DialogContentText>
          </DialogContent>
          <DialogActions>
            <Button
              onClick={() => setBulkDeleteDialogOpen(false)}
              color="primary"
            >
              キャンセル
            </Button>
            <Button onClick={handleBulkDelete} color="error" autoFocus>
              削除
            </Button>
          </DialogActions>
        </Dialog>

        {/* GPTメニュー */}
        <div className="flex flex-col text-center gap-2 flex-shrink-0 border-t border-gray-300 pt-2 mb-2">
          <button
            className="cursor-pointer bg-transparent border-none hover:bg-gray-200 py-2 px-4 rounded"
            onClick={() => setGptDialogOpen(true)}
          >
            GPT
          </button>
        </div>

        {/* GPTダイアログ */}
        <Dialog
          open={gptDialogOpen}
          onClose={() => setGptDialogOpen(false)}
          aria-labelledby="gpt-dialog-title"
          aria-describedby="gpt-dialog-description"
        >
          <DialogTitle id="gpt-dialog-title">
            GPT
          </DialogTitle>
          <DialogContent>
            <DialogContentText id="gpt-dialog-description">
              指示、追加の知識、複数のスキルを組み合わせた ChatGPT のカスタム バージョンの検索・作成を行います。
            </DialogContentText>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setGptDialogOpen(false)} color="primary">
              閉じる
            </Button>
          </DialogActions>
        </Dialog>

        <div className="flex flex-col text-center gap-2 flex-shrink-0">
          {userInfo?.role === 'admin' && (
            <button
              className="cursor bg-transparent border-none"
              onClick={() => {
                router.push('/admin');
              }}
            >
              管理画面
            </button>
          )}
          {/* <button
          className="cursor bg-transparent border-none"
          onClick={handleDropout}
        >
          アカウント削除
        </button> */}
          <div>
            <button
              className="cursor bg-transparent border-none"
              onClick={handleLogout}
            >
              ログアウト
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Leftbar;
