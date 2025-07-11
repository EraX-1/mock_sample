'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import {
  Box,
  Dialog,
  DialogContent,
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
} from '@mui/material';
import {
  Search as SearchIcon,
  Add as AddIcon,
  Chat as ChatIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
  Logout as LogoutIcon,
  AdminPanelSettings as AdminIcon,
  Close as CloseIcon,
  KeyboardCommandKey as CmdIcon,
} from '@mui/icons-material';
import {
  getChatChatRoomsApi,
  createChatRoomsApi,
  logoutApi,
  getUserInfoApi,
} from '@/services/apiService';

interface ChatRoom {
  id: string;
  name: string;
  created_at: string;
}

interface ModernNavigationProps {
  isOpen: boolean;
  onClose: () => void;
}

const ModernNavigation: React.FC<ModernNavigationProps> = ({
  isOpen,
  onClose,
}) => {
  const router = useRouter();
  const pathname = usePathname();
  const [searchQuery, setSearchQuery] = useState('');
  const [chatRooms, setChatRooms] = useState<ChatRoom[]>([]);
  const [userInfo, setUserInfo] = useState<any>(null);
  const [userMenuAnchor, setUserMenuAnchor] = useState<null | HTMLElement>(
    null
  );
  const searchInputRef = useRef<HTMLInputElement>(null);

  // データ取得
  useEffect(() => {
    if (isOpen) {
      fetchData();
      // ダイアログが開いたら検索フィールドにフォーカス
      setTimeout(() => {
        searchInputRef.current?.focus();
      }, 100);
    }
  }, [isOpen]);

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
        router.push(`/chat/${response.id}`);
        onClose();
      }
    } catch (error) {
      console.error('チャット作成エラー:', error);
    }
  };

  // チャットルームに移動
  const navigateToChat = (chatId: string) => {
    router.push(`/chat/${chatId}`);
    onClose();
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
    onClose();
  };

  // キーボードショートカット
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, onClose]);

  return (
    <Dialog
      open={isOpen}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 3,
          maxHeight: '80vh',
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          boxShadow: '0 24px 48px rgba(0, 0, 0, 0.12)',
        },
      }}
      BackdropProps={{
        sx: {
          backgroundColor: 'rgba(0, 0, 0, 0.3)',
          backdropFilter: 'blur(8px)',
        },
      }}
    >
      <DialogContent sx={{ p: 0 }}>
        {/* ヘッダー */}
        <Box sx={{ p: 3, borderBottom: '1px solid rgba(0, 0, 0, 0.08)' }}>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              mb: 2,
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Avatar
                sx={{ width: 40, height: 40, bgcolor: 'primary.main' }}
                onClick={e => setUserMenuAnchor(e.currentTarget)}
              >
                {userInfo?.name?.charAt(0) || 'U'}
              </Avatar>
              <Box>
                <Box sx={{ fontWeight: 600, fontSize: '1.1rem' }}>
                  {userInfo?.name || 'ユーザー'}
                </Box>
                <Box sx={{ fontSize: '0.85rem', color: 'text.secondary' }}>
                  {userInfo?.email || ''}
                </Box>
              </Box>
            </Box>
            <Tooltip title="閉じる (Esc)">
              <IconButton onClick={onClose} size="small">
                <CloseIcon />
              </IconButton>
            </Tooltip>
          </Box>

          {/* 検索フィールド */}
          <TextField
            ref={searchInputRef}
            fullWidth
            placeholder="チャットを検索... "
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: (
                <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
              ),
              endAdornment: (
                <Chip
                  label={
                    <Box
                      sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
                    >
                      <CmdIcon sx={{ fontSize: '0.8rem' }} />
                      <span>K</span>
                    </Box>
                  }
                  size="small"
                  variant="outlined"
                  sx={{ height: 24, fontSize: '0.75rem' }}
                />
              ),
            }}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
                backgroundColor: 'rgba(0, 0, 0, 0.02)',
              },
            }}
          />
        </Box>

        {/* クイックアクション */}
        <Box sx={{ p: 2 }}>
          <Box
            sx={{
              fontSize: '0.875rem',
              fontWeight: 600,
              color: 'text.secondary',
              mb: 1,
            }}
          >
            クイックアクション
          </Box>
          <List dense>
            <ListItem disablePadding>
              <ListItemButton
                onClick={createNewChat}
                sx={{
                  borderRadius: 2,
                  '&:hover': { backgroundColor: 'rgba(0, 0, 0, 0.04)' },
                }}
              >
                <ListItemIcon>
                  <AddIcon />
                </ListItemIcon>
                <ListItemText primary="新しいチャット" />
                <Chip label="N" size="small" variant="outlined" />
              </ListItemButton>
            </ListItem>
          </List>
        </Box>

        {/* チャット履歴 */}
        <Box sx={{ px: 2, pb: 2 }}>
          <Box
            sx={{
              fontSize: '0.875rem',
              fontWeight: 600,
              color: 'text.secondary',
              mb: 1,
              display: 'flex',
              alignItems: 'center',
              gap: 1,
            }}
          >
            <HistoryIcon sx={{ fontSize: '1rem' }} />
            最近のチャット
            {filteredChatRooms.length > 0 && (
              <Chip label={filteredChatRooms.length} size="small" />
            )}
          </Box>

          <List dense sx={{ maxHeight: 300, overflow: 'auto' }}>
            {filteredChatRooms.length === 0 ? (
              <ListItem>
                <ListItemText
                  primary="チャットが見つかりません"
                  secondary="新しいチャットを作成してください"
                  sx={{ textAlign: 'center', color: 'text.secondary' }}
                />
              </ListItem>
            ) : (
              filteredChatRooms
                .slice()
                .reverse()
                .slice(0, 10)
                .map(room => (
                  <ListItem key={room.id} disablePadding>
                    <ListItemButton
                      onClick={() => navigateToChat(room.id)}
                      selected={pathname === `/chat/${room.id}`}
                      sx={{
                        borderRadius: 2,
                        '&:hover': { backgroundColor: 'rgba(0, 0, 0, 0.04)' },
                        '&.Mui-selected': {
                          backgroundColor: 'rgba(25, 118, 210, 0.08)',
                          '&:hover': {
                            backgroundColor: 'rgba(25, 118, 210, 0.12)',
                          },
                        },
                      }}
                    >
                      <ListItemIcon>
                        <ChatIcon />
                      </ListItemIcon>
                      <ListItemText
                        primary={room.name}
                        secondary={new Date(room.created_at).toLocaleDateString(
                          'ja-JP'
                        )}
                        primaryTypographyProps={{
                          sx: {
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                          },
                        }}
                      />
                    </ListItemButton>
                  </ListItem>
                ))
            )}
          </List>
        </Box>

        {/* ユーザーメニュー */}
        <Menu
          anchorEl={userMenuAnchor}
          open={Boolean(userMenuAnchor)}
          onClose={() => setUserMenuAnchor(null)}
          PaperProps={{
            sx: {
              borderRadius: 2,
              mt: 1,
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
            },
          }}
        >
          {userInfo?.role === 'admin' && (
            <MenuItem onClick={navigateToAdmin}>
              <AdminIcon sx={{ mr: 2 }} />
              管理画面
            </MenuItem>
          )}
          <MenuItem>
            <SettingsIcon sx={{ mr: 2 }} />
            設定
          </MenuItem>
          <Divider />
          <MenuItem onClick={handleLogout}>
            <LogoutIcon sx={{ mr: 2 }} />
            ログアウト
          </MenuItem>
        </Menu>
      </DialogContent>
    </Dialog>
  );
};

export default ModernNavigation;
