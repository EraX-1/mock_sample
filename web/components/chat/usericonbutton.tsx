import React, { useState } from 'react';
import { Popover, Snackbar, TextField } from '@mui/material';
import { putChatRoomsApi } from '@/services/apiService';

interface UserIconButton {
  chatRoomId: string;
  assistantPrompt: string;
  setAssistantPrompt: (value: string) => void;
}

const UserIconButton: React.FunctionComponent<UserIconButton> = ({
  chatRoomId,
  assistantPrompt,
  setAssistantPrompt,
}) => {
  const [anchorEl, setAnchorEl] = React.useState<HTMLButtonElement | null>(
    null
  );
  const [temporaryprompt, setTemporaryprompt] =
    useState<string>(assistantPrompt);
  const [snackbarOpen, setSnackbarOpen] = useState(false);

  const handleSnackbarClose = (
    event: React.SyntheticEvent | Event,
    reason?: string
  ) => {
    if (reason === 'clickaway') {
      return;
    }
    setSnackbarOpen(false);
  };

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const open = Boolean(anchorEl);
  const id = open ? 'simple-popover' : undefined;

  const updateChatRoom = async (roomId: string, prompt: string) => {
    try {
      const params: any = {
        chat_room_id: roomId,
        prompt: prompt,
      };

      const { response } = await putChatRoomsApi({ params });

      setAssistantPrompt(response.prompt || assistantPrompt);

      return response;
    } catch (error) {
      throw error;
    } finally {
      setSnackbarOpen(true);
    }
  };

  return (
    <div>
      <button
        className="bg-transparent"
        aria-describedby={id}
        onClick={handleClick}
      >
        <img
          className="cursor-pointer w-10 h-10 object-cover"
          alt=""
          src="/ai-icon.png"
        />
      </button>
      <Popover
        id={id}
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'left',
        }}
      >
        <div className="flex flex-col justify-start px-4 py-4 w-72 h-96 gap-1 text-sm rounded-full">
          <div className="mb-1 font-bold">アシスタントプロンプト</div>
          <TextField
            sx={{
              '& .MuiInputBase-root': {
                fontSize: '12px',
              },
            }}
            id="outlined-multiline-flexible"
            value={temporaryprompt}
            onChange={e => {
              setTemporaryprompt(e.target.value);
            }}
            label=""
            multiline
            rows={12}
          />
          <button
            className="h-8 w-20 rounded-full cursor-pointer bg-slate-200 text-slategray hover:text-black font-bold"
            onClick={() => updateChatRoom(chatRoomId, temporaryprompt)}
          >
            決定する
          </button>
        </div>
      </Popover>
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={handleSnackbarClose}
        message="アシスタントプロンプトが更新されました"
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
      />
    </div>
  );
};

export default UserIconButton;
