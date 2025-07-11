'use client';

import type { NextPage } from 'next';
import { useState, useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  Menu,
  MenuItem,
  IconButton,
} from '@mui/material';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import Checkbox from '@mui/material/Checkbox';

export type ChatHistoryType = {
  id: string;
  title: string;
  sendChatroomName: (chat_room_id: string, name: string) => void;
  deleteChatRoom: (id: string) => void;
  isSelectMode?: boolean;
  isSelected?: boolean;
  onToggleSelect?: () => void;
};

const ChatHistoryItem: NextPage<ChatHistoryType> = ({
  title,
  id,
  sendChatroomName,
  deleteChatRoom,
  isSelectMode = false,
  isSelected = false,
  onToggleSelect = () => {},
}) => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [rowIsSelected, setRowIsSelected] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(title);
  const inputRef = useRef<HTMLInputElement>(null);
  const open = Boolean(anchorEl);

  const [displayText, setDisplayText] = useState(title);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    const queryId = searchParams.get('id');
    if (queryId) {
      setRowIsSelected(queryId === id);
    }

    const handleChangeName = (event: CustomEvent<{ name: string }>) => {
      setIsAnimating(true);
      setTimeout(() => {
        setDisplayText(event.detail.name);
        setEditValue(event.detail.name);
        setIsAnimating(false);
      }, 300);
    };

    window.addEventListener(
      `changeChatroomName_${id}`,
      handleChangeName as EventListener
    );

    return () => {
      window.removeEventListener(
        `changeChatroomName_${id}`,
        handleChangeName as EventListener
      );
    };
  }, [searchParams, id]);

  const handleDeleteClick = (id: string) => {
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    deleteChatRoom(id);
    setDeleteDialogOpen(false);
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
  };

  const handleChatRoomChange = () => {
    router.push(`/chat/${id}`);
  };

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = async () => {
    await setAnchorEl(null);
  };

  const handleDoubleClick = () => {
    setIsEditing(true);
    setTimeout(() => {
      inputRef.current?.focus();
    }, 0);
  };

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setEditValue(event.target.value);
  };

  const handleInputBlur = () => {
    setIsEditing(false);
    sendChatroomName(id, editValue);
  };

  const handleInputKeyPress = (
    event: React.KeyboardEvent<HTMLInputElement>
  ) => {
    if (event.key === 'Enter') {
      setIsEditing(false);
      sendChatroomName(id, editValue);
    }
  };

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isEditing]);

  const handleEditClick = async (event: React.MouseEvent) => {
    await handleClose();
    setIsEditing(true);
  };

  return (
    <div
      className={`cursor-pointer pl-2 self-stretch bg-gray flex flex-col items-start justify-center ${
        isSelected
          ? 'bg-zinc-300'
          : isSelectMode
            ? 'hover:bg-zinc-200'
            : rowIsSelected
              ? 'bg-zinc-200'
              : 'hover:bg-zinc-200'
      }`}
      onClick={
        isSelectMode
          ? onToggleSelect
          : !isEditing
            ? handleChatRoomChange
            : undefined
      }
    >
      <div className="flex flex-row items-center justify-between w-full text-left text-black font-sans h-16">
        {isSelectMode && (
          <Checkbox
            checked={isSelected}
            onChange={onToggleSelect}
            onClick={e => e.stopPropagation()}
            sx={{ p: 0, mr: 1 }}
          />
        )}
        {isEditing ? (
          <input
            ref={inputRef}
            className="border border-gray-300 rounded p-1 w-full bg-transparent"
            value={editValue}
            onChange={handleInputChange}
            onBlur={handleInputBlur}
            onKeyPress={handleInputKeyPress}
            autoFocus
          />
        ) : (
          <div className="flex-1 min-w-0">
            <span
              className={`line-clamp-3 overflow-hidden text-ellipsis transition-all duration-300 ease-in-out ${
                isAnimating
                  ? 'opacity-0 transform translate-y-2'
                  : 'opacity-100 transform translate-y-0'
              }`}
              onDoubleClick={!isSelectMode ? handleDoubleClick : undefined}
            >
              {displayText}
            </span>
          </div>
        )}
        {!isSelectMode && (
          <IconButton
            aria-controls={open ? 'context-menu' : undefined}
            aria-haspopup="true"
            aria-expanded={open ? 'true' : undefined}
            onClick={handleClick}
            sx={{ ml: 1 }}
          >
            <MoreVertIcon />
          </IconButton>
        )}
        <Menu
          id="context-menu"
          anchorEl={anchorEl}
          open={open}
          onClose={handleClose}
          disableAutoFocusItem={true}
          MenuListProps={{
            'aria-labelledby': 'basic-button',
          }}
        >
          <MenuItem onClick={handleEditClick}>
            <EditIcon style={{ marginRight: 8 }} />
            名前を変更する
          </MenuItem>
          <MenuItem
            onClick={() => handleDeleteClick(id)}
            style={{ color: 'red' }}
          >
            <DeleteIcon style={{ marginRight: 8 }} />
            削除する
          </MenuItem>
        </Menu>
      </div>
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
        aria-labelledby="alert-dialog-title"
        aria-describedby="alert-dialog-description"
      >
        <DialogTitle id="alert-dialog-title">ファイルの削除確認</DialogTitle>
        <DialogContent>
          <DialogContentText id="alert-dialog-description">
            このファイルを削除してもよろしいですか？この操作は取り消せません。
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel} color="primary">
            キャンセル
          </Button>
          <Button onClick={handleDeleteConfirm} color="error" autoFocus>
            削除
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default ChatHistoryItem;
