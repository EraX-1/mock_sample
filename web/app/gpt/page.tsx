'use client';

import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  TextField, 
  Button, 
  IconButton,
  InputAdornment,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import CloseIcon from '@mui/icons-material/Close';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import DriveFileRenameOutlineIcon from '@mui/icons-material/DriveFileRenameOutline';
import DescriptionIcon from '@mui/icons-material/Description';
import AssignmentIcon from '@mui/icons-material/Assignment';
import ChatBubbleOutlineIcon from '@mui/icons-material/ChatBubbleOutline';
import AddPhotoAlternateIcon from '@mui/icons-material/AddPhotoAlternate';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import { getCoreConfigApi } from '@/services/apiService';
import { useEffect } from 'react';

export default function GPTPage() {
  const [gptName, setGptName] = useState('');
  const [description, setDescription] = useState('');
  const [instructions, setInstructions] = useState('');
  const [conversationStarters, setConversationStarters] = useState(['']);
  const [knowledge, setKnowledge] = useState('');
  const [isKnowledgeExpanded, setIsKnowledgeExpanded] = useState(false);
  const [iconPreview, setIconPreview] = useState<string | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [modelList, setModelList] = useState<string[]>([]);

  const handleAddConversationStarter = () => {
    setConversationStarters([...conversationStarters, '']);
  };

  const handleRemoveConversationStarter = (index: number) => {
    const newStarters = conversationStarters.filter((_, i) => i !== index);
    setConversationStarters(newStarters.length === 0 ? [''] : newStarters);
  };

  const handleConversationStarterChange = (index: number, value: string) => {
    const newStarters = [...conversationStarters];
    newStarters[index] = value;
    setConversationStarters(newStarters);
  };

  const handleIconUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setIconPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      const newFiles = Array.from(files);
      setUploadedFiles(prev => [...prev, ...newFiles]);
    }
  };

  const handleRemoveFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  useEffect(() => {
    // APIからモデルリストを取得
    const fetchModelList = async () => {
      try {
        const { response, error } = await getCoreConfigApi();
        if (response && response.MODEL_LIST) {
          setModelList(response.MODEL_LIST);
          // デフォルトで最初のモデルを選択
          if (response.MODEL_LIST.length > 0) {
            setSelectedModel(response.MODEL_LIST[0]);
          }
        } else if (error) {
          console.error('Failed to fetch model list:', error);
          // フォールバックとしてデフォルトのモデルリストを使用
          const fallbackModelList = ['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo'];
          setModelList(fallbackModelList);
          setSelectedModel(fallbackModelList[0]);
        }
      } catch (error) {
        console.error('Failed to fetch model list:', error);
        // フォールバックとしてデフォルトのモデルリストを使用
        const fallbackModelList = ['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo'];
        setModelList(fallbackModelList);
        setSelectedModel(fallbackModelList[0]);
      }
    };

    fetchModelList();
  }, []);

  return (
    <Box className="flex flex-col h-screen w-full bg-gray-50 overflow-auto">
      <Box className="max-w-5xl w-full mx-auto p-8">
        <Paper elevation={0} className="p-8 rounded-xl bg-white border border-gray-200">
          {/* タイトルセクション */}
          <Box className="p-6 mb-8 rounded-xl bg-gradient-to-r from-purple-50 to-pink-50">
            <Box className="flex items-center gap-4 mb-2">
              <AutoAwesomeIcon className="text-purple-600" sx={{ fontSize: 36 }} />
              <Typography variant="h4" className="font-black text-gray-900">
                新しいGPTを作成
              </Typography>
            </Box>
            <Typography variant="body1" className="text-gray-600 ml-14">
              指示、追加の知識、複数のスキルを組み合わせた ChatGPT のカスタム バージョンの検索・作成を行います。
            </Typography>
          </Box>
          {/* 名前とアイコン */}
          <Box className="mb-8">
            <Box className="flex items-center gap-2 mb-3">
              <DriveFileRenameOutlineIcon className="text-purple-600" sx={{ fontSize: 20 }} />
              <Typography variant="subtitle1" className="font-semibold text-gray-700">
                名前
              </Typography>
            </Box>
            <Box className="flex gap-4 items-center">
              {/* アイコンアップロード */}
              <Box className="flex-shrink-0">
                <input
                  accept="image/*"
                  style={{ display: 'none' }}
                  id="icon-upload"
                  type="file"
                  onChange={handleIconUpload}
                />
                <label htmlFor="icon-upload">
                  <Box
                    className="w-24 h-24 rounded-full border-2 border-dashed border-gray-300 flex items-center justify-center cursor-pointer hover:border-purple-400 transition-colors bg-gray-50 overflow-hidden"
                    sx={{
                      backgroundImage: iconPreview ? `url(${iconPreview})` : 'none',
                      backgroundSize: 'cover',
                      backgroundPosition: 'center',
                    }}
                  >
                    {!iconPreview && (
                      <AddPhotoAlternateIcon className="text-gray-400" sx={{ fontSize: 40 }} />
                    )}
                  </Box>
                </label>
              </Box>
              
              {/* 名前入力フィールド */}
              <TextField
                fullWidth
                placeholder="GPT に名前を付けてください"
                value={gptName}
                onChange={(e) => setGptName(e.target.value)}
                variant="outlined"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: '8px',
                    backgroundColor: '#f9fafb',
                    height: '56px', // アイコンと同じ高さに設定
                  }
                }}
              />
            </Box>
          </Box>

          {/* 説明 */}
          <Box className="mb-8">
            <Box className="flex items-center gap-2 mb-3">
              <DescriptionIcon className="text-purple-600" sx={{ fontSize: 20 }} />
              <Typography variant="subtitle1" className="font-semibold text-gray-700">
                説明
              </Typography>
            </Box>
            <TextField
              fullWidth
              placeholder="この GPT の機能の簡潔な説明を追加してください"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              variant="outlined"
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: '8px',
                  backgroundColor: '#f9fafb',
                }
              }}
            />
          </Box>

          {/* 指示 */}
          <Box className="mb-8">
            <Box className="flex items-center gap-2 mb-3">
              <AssignmentIcon className="text-purple-600" sx={{ fontSize: 20 }} />
              <Typography variant="subtitle1" className="font-semibold text-gray-700">
                指示
              </Typography>
            </Box>
            <TextField
              fullWidth
              multiline
              rows={6}
              placeholder="この GPT は何をしますか？どのように振舞いますか？してはいけないことは何ですか？"
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              variant="outlined"
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: '8px',
                  backgroundColor: '#f9fafb',
                }
              }}
            />
            <Typography variant="caption" className="text-gray-500 mt-2 block">
              GPT との会話に、指定された指示の一部または全部が含まれる場合があります。
            </Typography>
          </Box>

          {/* 会話のきっかけ */}
          <Box className="mb-8">
            <Box className="flex items-center justify-between mb-3">
              <Box className="flex items-center gap-2">
                <ChatBubbleOutlineIcon className="text-purple-600" sx={{ fontSize: 20 }} />
                <Typography variant="subtitle1" className="font-semibold text-gray-700">
                  会話のきっかけ
                </Typography>
              </Box>
              <IconButton 
                onClick={handleAddConversationStarter}
                size="small"
                className="text-blue-600"
              >
                <AddCircleOutlineIcon />
              </IconButton>
            </Box>
            {conversationStarters.map((starter, index) => (
              <Box key={index} className="mb-2">
                <TextField
                  fullWidth
                  placeholder="ユーザーが会話を開始するための例"
                  value={starter}
                  onChange={(e) => handleConversationStarterChange(index, e.target.value)}
                  variant="outlined"
                  InputProps={{
                    endAdornment: conversationStarters.length > 1 && (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => handleRemoveConversationStarter(index)}
                          size="small"
                        >
                          <CloseIcon fontSize="small" />
                        </IconButton>
                      </InputAdornment>
                    )
                  }}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: '8px',
                      backgroundColor: '#f9fafb',
                    }
                  }}
                />
              </Box>
            ))}
          </Box>

          {/* モデル選択 */}
          <Box className="mb-8">
            <Box className="flex items-center gap-2 mb-3">
              <SmartToyIcon className="text-purple-600" sx={{ fontSize: 20 }} />
              <Typography variant="subtitle1" className="font-semibold text-gray-700">
                モデルを選択
              </Typography>
            </Box>
            <Select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              displayEmpty
              sx={{
                width: '25%',
                minWidth: '200px',
                '& .MuiOutlinedInput-root': {
                  borderRadius: '8px',
                  backgroundColor: '#f9fafb',
                },
              }}
            >
              {modelList.map((model, index) => (
                <MenuItem key={`${model}-${index}`} value={model}>
                  {model}
                </MenuItem>
              ))}
            </Select>
          </Box>

          {/* 知識 */}
          <Box className="mb-8">
            <Button
              onClick={() => setIsKnowledgeExpanded(!isKnowledgeExpanded)}
              className="w-full justify-between text-gray-700 normal-case"
              endIcon={<ExpandMoreIcon className={`transform transition-transform ${isKnowledgeExpanded ? 'rotate-180' : ''}`} />}
            >
              <Typography variant="subtitle1" className="font-semibold">
                このGPTが参照する追加ファイル
              </Typography>
            </Button>
            {isKnowledgeExpanded && (
              <Box className="mt-3">
                <Typography variant="body2" className="text-gray-600 mb-3">
                  GPT との会話に、アップロードしたファイルの一部または全部が表示される場合があります。
                </Typography>
                
                {/* ファイルアップロードボタン */}
                <input
                  accept=".pdf,.txt,.doc,.docx,.csv,.json,.md"
                  style={{ display: 'none' }}
                  id="file-upload"
                  type="file"
                  multiple
                  onChange={handleFileUpload}
                />
                <label htmlFor="file-upload">
                  <Button
                    variant="outlined"
                    component="span"
                    className="normal-case text-gray-700 border-gray-300"
                    startIcon={<AttachFileIcon />}
                    sx={{ borderRadius: '8px' }}
                  >
                    ファイルをアップロードする
                  </Button>
                </label>

                {/* アップロードされたファイルのリスト */}
                {uploadedFiles.length > 0 && (
                  <Box className="mt-4 flex flex-wrap gap-2">
                    {uploadedFiles.map((file, index) => (
                      <Chip
                        key={index}
                        icon={<InsertDriveFileIcon />}
                        label={file.name}
                        onDelete={() => handleRemoveFile(index)}
                        variant="outlined"
                        sx={{
                          height: '32px',
                          maxWidth: 'calc(50% - 4px)',
                          '& .MuiChip-label': {
                            display: 'block',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                          }
                        }}
                      />
                    ))}
                  </Box>
                )}
              </Box>
            )}
          </Box>

          {/* 作成ボタン */}
          <Box className="flex justify-center">
            <Button
              variant="contained"
              className="bg-purple-600 hover:bg-purple-700 text-white normal-case px-12 py-3 text-lg font-semibold shadow-lg hover:shadow-xl transition-all"
              sx={{ borderRadius: '12px' }}
              onClick={() => console.log('GPT作成（ハリボテ）')}
            >
              GPTを作成
            </Button>
          </Box>
        </Paper>
      </Box>
    </Box>
  );
}