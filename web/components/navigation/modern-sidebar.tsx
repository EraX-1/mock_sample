'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import {
  Box,
  TextField,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Chip,
  IconButton,
  Tooltip,
  Avatar,
  Menu,
  MenuItem,
  Divider,
  Collapse,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
} from '@mui/material';
import {
  Search as SearchIcon,
  Add as AddIcon,
  Chat as ChatIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
  Logout as LogoutIcon,
  AdminPanelSettings as AdminIcon,
  ExpandLess,
  ExpandMore,
  MenuOpen as MenuOpenIcon,
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
  Delete as DeleteIcon,
  AutoAwesome as AutoAwesomeIcon,
} from '@mui/icons-material';
import {
  getChatChatRoomsApi,
  createChatRoomsApi,
  logoutApi,
  getUserInfoApi,
  deleteChatMessagesApi,
} from '@/services/apiService';
import { useSidebar } from './sidebar-provider';

interface ChatRoom {
  id: string;
  name: string;
  created_at: string;
}

const ModernSidebar: React.FC = () => {
  const { isOpen, toggleSidebar, closeSidebar, isMobile } = useSidebar();
  const router = useRouter();
  const pathname = usePathname();
  const [searchQuery, setSearchQuery] = useState('');
  const [chatRooms, setChatRooms] = useState<ChatRoom[]>([]);
  const [userInfo, setUserInfo] = useState<any>(null);
  const [userMenuAnchor, setUserMenuAnchor] = useState<null | HTMLElement>(
    null
  );
  const [isHistoryExpanded, setIsHistoryExpanded] = useState(true);
  const [isMyGPTExpanded, setIsMyGPTExpanded] = useState(true);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [chatToDelete, setChatToDelete] = useState<string | null>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // データ取得
  useEffect(() => {
    fetchData();
  }, []);

  // キーボードショートカット機能は仕様決定後に実装予定
  // useEffect(() => {
  //   const handleKeyDown = (event: KeyboardEvent) => {
  //     if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
  //       event.preventDefault();
  //       searchInputRef.current?.focus();
  //     }
  //   };

  //   document.addEventListener('keydown', handleKeyDown);
  //   return () => document.removeEventListener('keydown', handleKeyDown);
  // }, []);

  const fetchData = async () => {
    try {
      // チャットルーム一覧取得
      const { response: chatResponse } = await getChatChatRoomsApi();
      if (chatResponse) {
        setChatRooms(
          chatResponse.map((room: any) => ({
            id: room.id,
            name: room.name,
            created_at: room.created_at,
          }))
        );
      }

      // ユーザー情報取得
      const { response: userResponse } = await getUserInfoApi();
      if (userResponse) {
        setUserInfo(userResponse);
      }
    } catch (error) {
      console.error('データ取得エラー:', error);
    }
  };

  // フィルタリングされたチャットルーム
  const filteredChatRooms = chatRooms.filter(room =>
    room.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // 新しいチャット作成
  const createNewChat = async () => {
    try {
      const { response } = await createChatRoomsApi();
      if (response) {
        const newChatRoom = {
          id: response.id,
          name: response.name,
          created_at: response.created_at,
        };
        setChatRooms(prev => [...prev, newChatRoom]);
        router.push(`/chat/${response.id}`);
        if (isMobile) closeSidebar();
      }
    } catch (error) {
      console.error('チャット作成エラー:', error);
    }
  };

  // チャットルームに移動
  const navigateToChat = (chatId: string) => {
    router.push(`/chat/${chatId}`);
    if (isMobile) closeSidebar();
  };

  // ログアウト
  const handleLogout = async () => {
    try {
      await logoutApi();
      router.push('/signin');
    } catch (error) {
      console.error('ログアウトエラー:', error);
    }
  };

  // 管理画面に移動
  const navigateToAdmin = () => {
    router.push('/admin');
    if (isMobile) closeSidebar();
  };

  // チャット削除確認
  const handleDeleteChat = (chatId: string, event: React.MouseEvent) => {
    event.stopPropagation(); // 親要素のクリックイベントを防ぐ
    setChatToDelete(chatId);
    setDeleteConfirmOpen(true);
  };

  // チャット削除実行
  const executeDeleteChat = async () => {
    if (!chatToDelete) return;

    try {
      const result = await deleteChatMessagesApi({ chat_room_id: chatToDelete });
      if (result.response?.success === 'true') {
        // チャットリストから削除
        setChatRooms(prev => prev.filter(room => room.id !== chatToDelete));

        // 現在のチャットページにいる場合はリダイレクト
        if (pathname === `/chat/${chatToDelete}`) {
          router.push('/chat');
        }
      } else {
        console.error('チャット削除エラー:', result.error);
      }
    } catch (error) {
      console.error('チャット削除エラー:', error);
    } finally {
      setDeleteConfirmOpen(false);
      setChatToDelete(null);
    }
  };

  // 削除確認ダイアログを閉じる
  const handleCloseDeleteConfirm = () => {
    setDeleteConfirmOpen(false);
    setChatToDelete(null);
  };

  // サイドバーの表示条件：モバイルでは開いている時のみ、デスクトップでは常に表示
  if (isMobile && !isOpen) {
    return null;
  }

  const sidebarClasses = `
    ${isMobile ? 'fixed' : 'relative'}
    ${isMobile ? 'inset-y-0 left-0' : ''}
    ${isOpen ? 'translate-x-0' : (isMobile ? '-translate-x-full' : 'translate-x-0')}
    ${isOpen ? 'w-80' : (isMobile ? 'w-80' : 'w-16')}
    h-full bg-white
    ${isMobile ? 'z-50' : 'z-10'}
    transition-all duration-300 ease-out
    shadow-xl border-r border-gray-200/50
    backdrop-blur-md bg-white/95
    flex flex-col
    ${isMobile ? '' : 'min-w-16'}
  `;

  return (
    <>
      {/* モバイル時のオーバーレイ */}
      {isMobile && isOpen && (
        <div
          className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40"
          onClick={closeSidebar}
        />
      )}

      {/* サイドバー */}
      <aside className={sidebarClasses}>
        {/* ヘッダー */}
        <Box className="p-4 border-b border-gray-200/50 bg-gradient-to-r from-blue-50/50 to-indigo-50/50">
          {isOpen ? (
            <Box className="flex items-center justify-between mb-4">
              <Box className="flex items-center gap-3">
                <Avatar
                  className="cursor-pointer w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600"
                  onClick={e => setUserMenuAnchor(e.currentTarget)}
                >
                  {userInfo?.name?.charAt(0) || 'U'}
                </Avatar>
                <Box>
                  <Box className="font-semibold text-gray-900 text-sm">
                    {userInfo?.name || 'ユーザー'}
                  </Box>
                  <Box className="text-xs text-gray-600">
                    {userInfo?.email || ''}
                  </Box>
                </Box>
              </Box>

              {/* サイドバー折りたたみボタン */}
              <Tooltip title="サイドバーを折りたたむ">
                <IconButton
                  onClick={toggleSidebar}
                  size="small"
                  className="bg-white/50 hover:bg-white/80 backdrop-blur-sm"
                >
                  <ChevronLeftIcon />
                </IconButton>
              </Tooltip>
            </Box>
          ) : (
            <Box className="flex flex-col items-center gap-3">
              {/* サイドバー展開ボタン */}
              <Tooltip title="サイドバーを展開" placement="right">
                <IconButton
                  onClick={toggleSidebar}
                  size="small"
                  className="bg-white/50 hover:bg-white/80 backdrop-blur-sm"
                >
                  <ChevronRightIcon />
                </IconButton>
              </Tooltip>

              {/* ユーザーアバター */}
              <Avatar
                className="cursor-pointer w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600"
                onClick={e => setUserMenuAnchor(e.currentTarget)}
              >
                {userInfo?.name?.charAt(0) || 'U'}
              </Avatar>
            </Box>
          )}

          {/* 検索フィールド - 展開時のみ表示 */}
          {isOpen && (
            <TextField
              ref={searchInputRef}
              fullWidth
              size="small"
              placeholder="チャットを検索"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: (
                  <SearchIcon className="mr-2 w-4 h-4 text-gray-500" />
                ),
              }}
              className="bg-white/50 rounded-xl"
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: '12px',
                  backgroundColor: 'rgba(255, 255, 255, 0.8)',
                  backdropFilter: 'blur(8px)',
                  border: '1px solid rgba(0, 0, 0, 0.08)',
                  '&:hover': {
                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                  },
                  '&.Mui-focused': {
                    backgroundColor: 'rgba(255, 255, 255, 1)',
                  },
                },
              }}
            />
          )}
        </Box>

        {/* クイックアクション */}
        <Box className="p-3 space-y-3">
          {/* GPTボタン */}
          <Tooltip title={isOpen ? '' : 'GPT'} placement="right">
            <ListItemButton
              onClick={() => {
                router.push('/gpt');
                if (isMobile) closeSidebar();
              }}
              className={`rounded-xl bg-gradient-to-r ${
                pathname === '/gpt'
                  ? 'from-purple-100 to-pink-100 border-purple-400'
                  : 'from-purple-50 to-pink-50 hover:from-purple-100 hover:to-pink-100 border-purple-200/50'
              }`}
              sx={{
                justifyContent: isOpen ? 'flex-start' : 'center',
                px: isOpen ? 2 : 1,
              }}
            >
              <ListItemIcon
                sx={{
                  minWidth: isOpen ? 36 : 'auto',
                  justifyContent: 'center'
                }}
              >
                <AutoAwesomeIcon className="text-purple-600" />
              </ListItemIcon>
              {isOpen && (
                <ListItemText
                  primary="GPT"
                  primaryTypographyProps={{
                    className: 'font-medium text-purple-900',
                  }}
                />
              )}
            </ListItemButton>
          </Tooltip>
        </Box>

        {/* マイGPT */}
        <Box className="px-3 mb-2">
          {isOpen ? (
            <ListItemButton
              onClick={() => setIsMyGPTExpanded(!isMyGPTExpanded)}
              className="rounded-lg"
            >
              <ListItemIcon>
                <AutoAwesomeIcon className="text-purple-600" />
              </ListItemIcon>
              <ListItemText
                primary="マイGPT"
                primaryTypographyProps={{
                  className: 'font-medium text-gray-700 text-sm',
                }}
              />
              {isMyGPTExpanded ? <ExpandLess /> : <ExpandMore />}
            </ListItemButton>
          ) : (
            <Tooltip title="マイGPT" placement="right">
              <Box className="flex justify-center w-full py-2">
                <IconButton size="small">
                  <AutoAwesomeIcon className="text-purple-600" />
                </IconButton>
              </Box>
            </Tooltip>
          )}
        </Box>

        <Collapse in={isOpen && isMyGPTExpanded} timeout="auto" unmountOnExit>
          <Box className="px-3 pb-3">
            <List dense>
              <ListItem>
                <ListItemText
                  primary="GPTが見つかりません"
                  secondary="新しいGPTを作成してください"
                  className="text-center text-gray-500 py-8"
                />
              </ListItem>
            </List>
          </Box>
        </Collapse>

        {/* クイックアクション - 新しいチャットボタン */}
        <Box className="p-3 pt-0">
          {/* 新しいチャットボタン */}
          <Tooltip title={isOpen ? '' : '新しいチャット'} placement="right">
            <ListItemButton
              onClick={createNewChat}
              className="rounded-xl bg-gradient-to-r from-blue-50 to-indigo-50 hover:from-blue-100 hover:to-indigo-100 border border-blue-200/50"
              sx={{
                justifyContent: isOpen ? 'flex-start' : 'center',
                px: isOpen ? 2 : 1,
              }}
            >
              <ListItemIcon
                sx={{
                  minWidth: isOpen ? 36 : 'auto',
                  justifyContent: 'center'
                }}
              >
                <AddIcon className="text-blue-600" />
              </ListItemIcon>
              {isOpen && (
                <ListItemText
                  primary="新しいチャット"
                  primaryTypographyProps={{
                    className: 'font-medium text-blue-900',
                  }}
                />
              )}
            </ListItemButton>
          </Tooltip>
        </Box>

        {/* チャット履歴 */}
        <Box className="flex-1 overflow-hidden flex flex-col">
          <Box className="px-3">
            {isOpen ? (
              <ListItemButton
                onClick={() => setIsHistoryExpanded(!isHistoryExpanded)}
                className="rounded-lg"
              >
                <ListItemIcon>
                  <HistoryIcon className="text-gray-600" />
                </ListItemIcon>
                <ListItemText
                  primary="最近のチャット"
                  primaryTypographyProps={{
                    className: 'font-medium text-gray-700 text-sm',
                  }}
                />
                {filteredChatRooms.length > 0 && (
                  <Chip
                    label={filteredChatRooms.length}
                    size="small"
                    className="bg-gray-100 text-gray-700 text-xs mx-2"
                  />
                )}
                {isHistoryExpanded ? <ExpandLess /> : <ExpandMore />}
              </ListItemButton>
            ) : (
              <Tooltip title="最近のチャット" placement="right">
                <Box className="flex justify-center w-full py-2">
                  <IconButton size="small">
                    <HistoryIcon className="text-gray-600" />
                  </IconButton>
                </Box>
              </Tooltip>
            )}
          </Box>

          <Collapse in={isOpen && isHistoryExpanded} timeout="auto" unmountOnExit>
            <Box className="flex-1 overflow-y-auto px-3 pb-3">
              <List dense>
                {filteredChatRooms.length === 0 ? (
                  <ListItem>
                    <ListItemText
                      primary="チャットが見つかりません"
                      secondary="新しいチャットを作成してください"
                      className="text-center text-gray-500 py-8"
                    />
                  </ListItem>
                ) : (
                  filteredChatRooms
                    .slice()
                    .reverse()
                    .map(room => (
                      <ListItem key={room.id} disablePadding className="mb-1 group">
                        <ListItemButton
                          onClick={() => navigateToChat(room.id)}
                          selected={pathname === `/chat/${room.id}`}
                          className="rounded-lg transition-all duration-200"
                          sx={{
                            '&:hover': {
                              backgroundColor: 'rgba(59, 130, 246, 0.08)',
                              transform: 'translateX(2px)',
                            },
                            '&.Mui-selected': {
                              backgroundColor: 'rgba(59, 130, 246, 0.12)',
                              borderLeft: '3px solid rgb(59, 130, 246)',
                              '&:hover': {
                                backgroundColor: 'rgba(59, 130, 246, 0.16)',
                              },
                            },
                          }}
                        >
                          <ListItemIcon>
                            <ChatIcon className="w-4 h-4 text-gray-600" />
                          </ListItemIcon>
                          <ListItemText
                            primary={room.name}
                            secondary={new Date(
                              room.created_at
                            ).toLocaleDateString('ja-JP')}
                            primaryTypographyProps={{
                              className:
                                'text-sm font-medium text-gray-900 truncate',
                            }}
                            secondaryTypographyProps={{
                              className: 'text-xs text-gray-500',
                            }}
                          />

                          {/* 削除ボタン - ホバー時に表示 */}
                          <Box className="opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                            <Tooltip title="チャットを削除" placement="top">
                              <IconButton
                                size="small"
                                onClick={(e) => handleDeleteChat(room.id, e)}
                                className="text-red-500 hover:text-red-700 hover:bg-red-50"
                                sx={{
                                  ml: 1,
                                  '&:hover': {
                                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                                  }
                                }}
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </ListItemButton>
                      </ListItem>
                    ))
                )}
              </List>
            </Box>
          </Collapse>
        </Box>

        {/* フッター部分（管理画面とログアウトボタン） */}
        <Box className="p-3 border-t border-gray-200/50">
          {userInfo?.role === 'admin' && (
            <Tooltip title={isOpen ? '' : '管理画面'} placement="right">
              <ListItemButton
                onClick={navigateToAdmin}
                className="rounded-xl hover:bg-gray-100 mb-2"
                sx={{
                  justifyContent: isOpen ? 'flex-start' : 'center',
                  px: isOpen ? 2 : 1,
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: isOpen ? 36 : 'auto',
                    justifyContent: 'center'
                  }}
                >
                  <AdminIcon className="text-gray-600" />
                </ListItemIcon>
                {isOpen && (
                  <ListItemText
                    primary="管理画面"
                    primaryTypographyProps={{
                      className: 'font-medium text-gray-700',
                    }}
                  />
                )}
              </ListItemButton>
            </Tooltip>
          )}
          <Tooltip title={isOpen ? '' : 'ログアウト'} placement="right">
            <ListItemButton
              onClick={handleLogout}
              className="rounded-xl hover:bg-gray-100"
              sx={{
                justifyContent: isOpen ? 'flex-start' : 'center',
                px: isOpen ? 2 : 1,
              }}
            >
              <ListItemIcon
                sx={{
                  minWidth: isOpen ? 36 : 'auto',
                  justifyContent: 'center'
                }}
              >
                <LogoutIcon className="text-gray-600" />
              </ListItemIcon>
              {isOpen && (
                <ListItemText
                  primary="ログアウト"
                  primaryTypographyProps={{
                    className: 'font-medium text-gray-700',
                  }}
                />
              )}
            </ListItemButton>
          </Tooltip>
        </Box>

        {/* ユーザーメニュー */}
        <Menu
          anchorEl={userMenuAnchor}
          open={Boolean(userMenuAnchor)}
          onClose={() => setUserMenuAnchor(null)}
          PaperProps={{
            className:
              'rounded-xl shadow-xl border border-gray-200/50 backdrop-blur-md bg-white/95',
          }}
        >
          {userInfo?.role === 'admin' && (
            <MenuItem
              onClick={navigateToAdmin}
              className="rounded-lg mx-2 my-1"
            >
              <AdminIcon className="mr-3 text-gray-600" />
              管理画面
            </MenuItem>
          )}
          <MenuItem className="rounded-lg mx-2 my-1">
            <SettingsIcon className="mr-3 text-gray-600" />
            設定
          </MenuItem>
        </Menu>

        {/* 削除確認ダイアログ */}
        <Dialog
          open={deleteConfirmOpen}
          onClose={handleCloseDeleteConfirm}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle className="font-semibold text-gray-900">
            チャットを削除
          </DialogTitle>
          <DialogContent>
            <Typography className="text-gray-600">
              このチャットを削除してもよろしいですか？
              <br />
              <span className="text-red-600 font-medium">
                この操作は元に戻すことができません。
              </span>
            </Typography>
          </DialogContent>
          <DialogActions className="px-6 pb-4">
            <Button
              onClick={handleCloseDeleteConfirm}
              variant="outlined"
              className="text-gray-600 border-gray-300 hover:bg-gray-50"
            >
              キャンセル
            </Button>
            <Button
              onClick={executeDeleteChat}
              variant="contained"
              color="error"
              className="bg-red-600 hover:bg-red-700"
            >
              削除
            </Button>
          </DialogActions>
        </Dialog>
      </aside>
    </>
  );
};

export default ModernSidebar;
