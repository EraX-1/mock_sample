'use client';

import { Fragment, useCallback, useEffect, useRef, useState } from 'react';
import {
  Tooltip,
  TextareaAutosize,
  TextField,
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  Paper,
} from '@mui/material';
import type { NextPage } from 'next';
import UpArrowIcon from '@/components/icon/UpArrowIcon';
import ChatBubbleOutlineIcon from '@mui/icons-material/ChatBubbleOutline';
import AddCommentIcon from '@mui/icons-material/AddComment';
import CategoryIcon from '@mui/icons-material/Category';
import React from 'react';
import { ChatModelType, ChatIndexType } from '@/types/chat';
import { getCoreConfigApi } from '@/services/apiService';

const INITIAL_TOKEN = 700;

export type MessageBoxType = {
  selectedText: string;
  setSelectedText: (text: string) => void;
  onSubmit: () => void;
  customPrompt: string | null;
  setCustomPrompt: (text: string) => void;
  isCustomPromptActive: boolean;
  setIsCustomPromptActive: (bool: boolean) => void;
  tokenCount: number;
  setTokenCount: (count: number) => void;
  selectedModel: ChatModelType;
  setSelectedModel: (model: ChatModelType) => void;
  handleModelChange: any;
  indexType: ChatIndexType[];
  setIndexType: (types: ChatIndexType[]) => void;
  indexTypeOptions: { value: string; label: string }[];
  className?: string;
};

type TokenizeResponse = {
  tokenCount: number;
  tokens: number[];
  selectedModel: string;
  handleModelChange: any;
};

const MessageBox: NextPage<MessageBoxType> = ({
  selectedText,
  setSelectedText,
  onSubmit,
  customPrompt,
  setCustomPrompt,
  isCustomPromptActive,
  setIsCustomPromptActive,
  tokenCount,
  setTokenCount,
  selectedModel,
  setSelectedModel,
  handleModelChange,
  indexType,
  setIndexType,
  indexTypeOptions,
  className,
}) => {
  const [error, setError] = useState<string>('');
  const textAreaRef = useRef<HTMLTextAreaElement | null>(null);
  const [modelList, setModelList] = useState<string[]>([]);

  useEffect(() => {
    if (textAreaRef.current) {
      textAreaRef.current.focus();
    }
  }, []);

  useEffect(() => {
    // APIからモデルリストを取得
    const fetchModelList = async () => {
      try {
        const { response, error } = await getCoreConfigApi();
        if (response && response.MODEL_LIST) {
          setModelList(response.MODEL_LIST);
        } else if (error) {
          console.error('Failed to fetch model list:', error);
          // フォールバックとしてenvから取得
          const fallbackModelList = JSON.parse(
            process.env.NEXT_PUBLIC_MODEL_LIST || '[]'
          );
          setModelList(fallbackModelList);
        }
      } catch (error) {
        console.error('Failed to fetch model list:', error);
        // フォールバックとしてenvから取得
        const fallbackModelList = JSON.parse(
          process.env.NEXT_PUBLIC_MODEL_LIST || '[]'
        );
        setModelList(fallbackModelList);
      }
    };

    fetchModelList();
  }, []);

  const handleTokenize = useCallback(
    async (text: string) => {
      setError(''); // エラーをリセット
      if (text == '' && customPrompt == '') {
        setTokenCount(INITIAL_TOKEN);
        return;
      }
      try {
        const response = await fetch('/api/tokenize', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ text: text + customPrompt }),
        });

        if (!response.ok) {
          const { error }: { error: string } = await response.json();
          setError(error || 'Something went wrong');
          return;
        }

        const { tokenCount, tokens }: TokenizeResponse = await response.json();
        setTokenCount(INITIAL_TOKEN + tokenCount);
      } catch (err) {
        setError('Failed to tokenize text');
      }
    },
    [customPrompt, setTokenCount, setError]
  );

  useEffect(() => {
    handleTokenize(selectedText);
  }, [customPrompt, handleTokenize, selectedText]);

  const handleCustomPromptSwitchChange = () => {
    setIsCustomPromptActive(!isCustomPromptActive);
  };

  const handleInputChange = (value: string) => {
    setSelectedText(value);
    handleTokenize(value);
  };

  const handleSubmit = async () => {
    if (selectedText.trim()) {
      onSubmit();
      setSelectedText('');
      setTokenCount(700);
    }
  };

  // Ctrl+Enterで送信するためのハンドラ
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.ctrlKey && e.key === 'Enter') {
      handleSubmit();
    }
  };

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
        maxWidth: '1200px',
        margin: '0 auto',
      }}
      className={className}
    >
      {/* 参照文書選択UI */}
      <Paper
        elevation={0}
        sx={{
          display: 'flex',
          alignItems: 'center',
          mb: 2,
          p: 1,
          borderRadius: '10px',
          backgroundColor: '#f5f5f5',
          overflow: 'auto',
          width: '100%',
          '&::-webkit-scrollbar': {
            height: '8px',
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: '#cccccc',
            borderRadius: '4px',
          },
        }}
      >
        <CategoryIcon
          sx={{ mr: 1, color: 'text.secondary', minWidth: '24px' }}
        />
        <Box
          sx={{
            display: 'flex',
            overflowX: 'auto',
            flexWrap: 'nowrap',
            px: 1,
            '&::-webkit-scrollbar': {
              height: '6px',
            },
            '&::-webkit-scrollbar-thumb': {
              backgroundColor: '#cccccc',
              borderRadius: '4px',
            },
          }}
        >
          {indexTypeOptions.map(option => (
            <FormControlLabel
              key={option.value}
              control={
                <Checkbox
                  checked={indexType.includes(option.value as ChatIndexType)}
                  onChange={e => {
                    if (e.target.checked) {
                      setIndexType([
                        ...indexType,
                        option.value as ChatIndexType,
                      ]);
                    } else {
                      setIndexType(
                        indexType.filter(type => type !== option.value)
                      );
                    }
                  }}
                  size="small"
                />
              }
              label={option.label}
              sx={{
                minWidth: 'fit-content',
                mr: 1,
                '& .MuiFormControlLabel-label': {
                  fontSize: '0.85rem',
                },
              }}
            />
          ))}
        </Box>
      </Paper>

      <Box
        sx={{
          display: 'flex',
          flexDirection: { xs: 'column', sm: 'row' },
          alignItems: { xs: 'stretch', sm: 'flex-end' },
          width: '100%',
          gap: { xs: 1, sm: 2 },
        }}
      >
        <div style={{ width: '100%' }}>
          <div
            className={`bg-gray flex flex-row items-center justify-center py-2 px-6 gap-2.5`}
            style={{
              borderRadius: '10px',
              backgroundColor: '#f5f5f5',
              width: '100%',
            }}
          >
            <TextareaAutosize
              ref={textAreaRef}
              minRows={1}
              maxRows={10}
              placeholder="メッセージを送信する"
              className="bg-[transparent] w-full font-inter font-normal text-base text-black"
              value={selectedText}
              onChange={e => handleInputChange(e.target.value)}
              onKeyDown={handleKeyDown}
              style={{
                border: 'none',
                outline: 'none',
                resize: 'none',
              }}
            />
            {isCustomPromptActive ? (
              <Tooltip
                title={
                  <Fragment>
                    <h3 className="mb-2">カスタムプロンプト</h3>
                    <TextField
                      multiline
                      maxRows={4}
                      minRows={2}
                      className="w-64"
                      slotProps={{
                        input: {
                          sx: {
                            padding: 1,
                          },
                          className: 'text-sm border border-gray-300 rounded',
                        },
                      }}
                      value={customPrompt}
                      onChange={event => setCustomPrompt(event.target.value)}
                    />
                  </Fragment>
                }
                arrow
                placement="top"
                slotProps={{
                  tooltip: {
                    sx: {
                      backgroundColor: 'white',
                      color: 'rgba(0, 0, 0, 0.87)',
                      border: '1px solid #dadde9',
                      boxShadow: '4px 4px 10px rgba(0, 0, 0, 0.2)',
                    },
                  },
                  arrow: {
                    sx: {
                      color: 'white',
                    },
                  },
                }}
              >
                <button onClick={handleCustomPromptSwitchChange}>
                  <ChatBubbleOutlineIcon />
                </button>
              </Tooltip>
            ) : (
              <button onClick={handleCustomPromptSwitchChange}>
                <AddCommentIcon />
              </button>
            )}

            <Tooltip title="テキストを送信する" arrow placement="top">
              <button
                className={`cursor-pointer border-none p-0 rounded-full ${
                  selectedText ? 'bg-black' : 'bg-slate-300'
                }`}
                style={{
                  width: '30px',
                  height: '30px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
                onClick={handleSubmit}
              >
                <UpArrowIcon
                  color={`${selectedText ? 'white' : '#f5f5f5'}`}
                  className="h-5 w-6 text-slategray hover:brightness-50 hover:contrast-200"
                />
              </button>
            </Tooltip>
          </div>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'flex-end',
            }}
          >
            <Tooltip
              title="システムプロンプトで700トークンを使用します"
              arrow
              placement="top"
            >
              <Typography align="right">token: {tokenCount}/12800</Typography>
            </Tooltip>
          </Box>
        </div>
        <FormControl
          sx={{
            marginLeft: { xs: 0, sm: 1 },
            marginTop: { xs: 1, sm: 0 },
            minWidth: { xs: '100%', sm: '130px' },
            maxWidth: { sm: '130px' },
          }}
        >
          <InputLabel id="llm-model-label">LLMモデル</InputLabel>
          <Select
            labelId="llm-model-label"
            label="LLMモデル"
            value={selectedModel}
            onChange={handleModelChange}
            sx={{
              width: { xs: '100%', sm: '130px' },
            }}
          >
            {modelList.map((model: string, index: number) => (
              <MenuItem key={`${model}-${index}`} value={model}>
                {model}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>
    </Box>
  );
};

export default MessageBox;
