'use client';

import type { NextPage } from 'next';
import { useState } from 'react';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import { Tooltip, Chip, Box } from '@mui/material';
import CategoryIcon from '@mui/icons-material/Category';

export type ChatMessageType = {
  text: string;
  model: string | undefined;
  indexTypes?: { id: string; label: string }[];
};

const ChatMessage: NextPage<ChatMessageType> = ({
  text,
  model,
  indexTypes,
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const [copyStatus, setCopyStatus] = useState<string>('コピー');

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopyStatus('コピーしました！');
      setTimeout(() => setCopyStatus('コピー'), 2000);
    } catch (error) {
      setCopyStatus('コピーに失敗しました');
      setTimeout(() => setCopyStatus('コピー'), 2000);
    }
  };

  return (
    <div
      className={
        'relative self-stretch flex flex-col items-end justify-start pt-8 pb-12 gap-2 w-full text-base leading-normal not-italic font-sans'
      }
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="flex flex-row-reverse items-center justify-start gap-2 w-full">
        <i
          className="justify-end bg-gray px-5 py-2 max-w-[440px] rounded-3xl relative"
          style={{ backgroundColor: '#f5f5f5' }}
        >
          {text}
          {model && (
            <span className="absolute -top-4 -right-3 text-sm px-3 rounded-full shadow bg-white">
              {model}
            </span>
          )}
          {isHovered && (
            <Tooltip title={copyStatus} arrow placement="bottom">
              <button
                onClick={handleCopy}
                className="absolute left-[-30px] top-1/2 transform -translate-y-1/2 hover:text-gray-500 transition"
                style={{ backgroundColor: 'transparent', border: 'none' }}
              >
                <ContentCopyIcon
                  style={{ fontSize: 16, cursor: 'pointer', color: 'gray' }}
                />
              </button>
            </Tooltip>
          )}
        </i>
      </div>

      {indexTypes && indexTypes.length > 0 && (
        <Box
          sx={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: 0.5,
            maxWidth: '440px',
            justifyContent: 'flex-end',
            mt: 1,
          }}
        >
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              fontSize: '0.75rem',
              color: 'gray',
              mr: 0.5,
            }}
          >
            <CategoryIcon fontSize="small" sx={{ mr: 0.5 }} />
            参照先:
          </Box>
          {indexTypes.map((indexType, index) => (
            <Chip
              key={`${indexType.id || 'idx'}-${index}`}
              label={indexType.label}
              size="small"
              sx={{
                fontSize: '0.7rem',
                height: '20px',
                backgroundColor: '#e0e0e0',
              }}
            />
          ))}
        </Box>
      )}
    </div>
  );
};

export default ChatMessage;
