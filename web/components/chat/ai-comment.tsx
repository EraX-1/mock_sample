'use client';

import CopyIcon from '@/components/icon/copyIcon';
import { putEvaluationApi } from '@/services/apiService';
import DownloadIcon from '@mui/icons-material/Download';
import LinkIcon from '@mui/icons-material/Link';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import ThumbDownOutlinedIcon from '@mui/icons-material/ThumbDownOutlined';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import ThumbUpOutlinedIcon from '@mui/icons-material/ThumbUpOutlined';
import VideoLibraryIcon from '@mui/icons-material/VideoLibrary';
import VisibilityIcon from '@mui/icons-material/Visibility';
import {
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  FormGroup,
  FormLabel,
  Radio,
  RadioGroup,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Typography,
} from '@mui/material';
import type { NextPage } from 'next';
import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ChatMessage } from './chat-section';

export type AICommentType = {
  message: ChatMessage;
  refFileList?: string[];
  setSelectedFile: (file: {
    fileType: 'pdf' | 'xls' | 'xlsx' | 'xlsm';
    url: string;
  }) => void;
  previousMessage?: ChatMessage;
};

// VideoStepリンクを解析する関数
const extractVideoStepInfo = (text: string) => {
  const regex = /<videostep title="([^"]*)" desc="([^"]*)" url="([^"]*)">/g;
  const matches = [];
  let match;

  while ((match = regex.exec(text)) !== null) {
    matches.push({
      title: match[1],
      desc: match[2],
      url: match[3],
    });
  }

  return matches;
};

// VideoStepカードコンポーネント
const VideoStepCard = ({
  title,
  desc,
  url,
}: {
  title: string;
  desc: string;
  url: string;
}) => {
  return (
    <Card
      sx={{
        maxWidth: '100%',
        mb: 2,
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        borderRadius: '8px',
        overflow: 'hidden',
      }}
    >
      <Box
        sx={{ display: 'flex', alignItems: 'center', p: 2, bgcolor: '#f5f5f5' }}
      >
        <VideoLibraryIcon sx={{ color: '#1976d2', mr: 1 }} />
        <Typography
          variant="h6"
          component="div"
          sx={{ flexGrow: 1, fontSize: '1rem' }}
        >
          {title}
        </Typography>
      </Box>
      <CardContent sx={{ pt: 1, pb: 1 }}>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {desc}
        </Typography>
        <Button
          variant="outlined"
          size="small"
          endIcon={<OpenInNewIcon />}
          onClick={() => window.open(url, '_blank')}
          sx={{
            textTransform: 'none',
            borderColor: '#1976d2',
            color: '#1976d2',
            '&:hover': {
              backgroundColor: 'rgba(25, 118, 210, 0.04)',
              borderColor: '#1976d2',
            },
          }}
        >
          マニュアルを開く
        </Button>
      </CardContent>
    </Card>
  );
};

// SharePointリンクを生成する関数を修正
const generateSharePointUrl = (filePath: string): string => {
  // 実際のSharePointのベースURL
  const baseUrl =
    'https://kdkdserv.sharepoint.com/sites/KnowledgeDBPJ/Shared%20Documents/Forms/AllItems.aspx';

  // ファイルパスがBlobストレージのURLの場合の処理
  if (filePath.includes('blob.core.windows.net')) {
    // ファイル名だけを抽出（最後の部分）
    const fileName = filePath.split('/').pop() || '';

    // 実際のSharePointのパスを構築
    // 注: 実際のパスは環境に合わせて調整が必要です
    const targetPath = 'DataforIndex';

    // 実際のSharePointのURLを構築
    const fullPath = `/sites/KnowledgeDBPJ/Shared Documents/${targetPath}/${fileName}`;
    const encodedId = encodeURIComponent(fullPath);

    const parentPath = `/sites/KnowledgeDBPJ/Shared Documents/${targetPath}`;
    const encodedParent = encodeURIComponent(parentPath);

    return `${baseUrl}?id=${encodedId}&parent=${encodedParent}`;
  }

  // 通常のファイルパスの場合（SampleForIndex20250122 → DataforIndex に置換）
  const replacedPath = filePath.replace(
    'SampleForIndex20250122',
    'DataforIndex'
  );

  // id: ファイルまで含むエンコードされたURL
  const fullPath = `/sites/KnowledgeDBPJ/Shared Documents/${replacedPath}`;
  const encodedId = encodeURIComponent(fullPath);

  // parent: ファイルを除いた親フォルダまでのエンコード
  const parentDir = replacedPath.substring(0, replacedPath.lastIndexOf('/'));
  const fullParent = `/sites/KnowledgeDBPJ/Shared Documents/${parentDir}`;
  const encodedParent = encodeURIComponent(fullParent);

  // 最終URLの構築
  return `${baseUrl}?id=${encodedId}&parent=${encodedParent}&viewid=38d07675-2ced-49ad-afef-8840d7e6d927`;
};

// ソースまたは参照先をクリックした時のダイアログコンポーネント
const LinkOptionsDialog = ({
  isOpen,
  onClose,
  onPreview,
  fileName,
  displayName,
  sharePointPath,
}: {
  isOpen: boolean;
  onClose: () => void;
  onPreview: () => void;
  fileName: string;
  displayName: string;
  sharePointPath: string;
}) => {
  return (
    <Dialog open={isOpen} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle>ファイルを開く方法を選択</DialogTitle>
      <DialogContent>
        <Typography variant="body2" sx={{ mb: 2 }}>
          {displayName}
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<VisibilityIcon />}
            onClick={onPreview}
            fullWidth
          >
            プレビューで開く
          </Button>
          <Button
            variant="outlined"
            startIcon={<LinkIcon />}
            onClick={() => {
              // SharePointリンクを生成して新しいタブで開く
              const sharePointUrl = generateSharePointUrl(sharePointPath);
              window.open(sharePointUrl, '_blank');
              onClose();
            }}
            fullWidth
          >
            SharePointリンクで開く
          </Button>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>キャンセル</Button>
      </DialogActions>
    </Dialog>
  );
};

// 評価モーダルコンポーネント
const EvaluationModal = ({
  isOpen,
  onClose,
  onSubmit,
  initialEvaluation,
  answerText,
  questionText,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: {
    evaluation: 'good' | 'bad';
    timeSaved: string;
    comment: string;
    expectedDocuments: string;
    expectedAnswer: string;
    helpfulAspects: string[];
    improvementAreas: string[];
  }) => void;
  initialEvaluation?: 'good' | 'bad';
  answerText: string;
  questionText?: string;
}) => {
  const [evaluation, setEvaluation] = useState<'good' | 'bad'>(
    initialEvaluation || 'good'
  );
  const [timeSaved, setTimeSaved] = useState<string>('');
  const [comment, setComment] = useState<string>('');
  const [expectedDocuments, setExpectedDocuments] = useState<string>('');
  const [expectedAnswer, setExpectedAnswer] = useState<string>('');
  const [helpfulAspects, setHelpfulAspects] = useState<string[]>([]);
  const [improvementAreas, setImprovementAreas] = useState<string[]>([]);

  // initialEvaluationが変更されたときに評価を更新
  React.useEffect(() => {
    if (initialEvaluation) {
      setEvaluation(initialEvaluation);
    }
  }, [initialEvaluation]);

  // VideoStepリンクを除去したテキストを作成（メインと同じ処理）
  const cleanedAnswerText = answerText.replace(
    /<videostep title="[^"]*" desc="[^"]*" url="[^"]*">/g,
    ''
  );

  // 削減時間の選択肢
  const timeSavedOptions = [
    { value: 'none', label: '削減できず' },
    { value: 'under15', label: '15分以下' },
    { value: 'under30', label: '30分以下' },
    { value: 'under60', label: '60分以下' },
    { value: 'over60', label: '60分以上' },
  ];

  // 良い評価の選択肢
  const helpfulOptions = [
    '質問の意図通りであり、正確で最新の情報だった',
    '必要な情報が網羅されていた',
    '簡潔でわかりやすかった',
  ];

  // 悪い評価の選択肢
  const improvementOptions = [
    '情報が古かったり不正確だったりした',
    '情報が不足していた',
    '冗長で分かりにくい回答だった',
    '情報源の内容がそもそもよくない',
  ];

  // チェックボックスのハンドラ
  const handleHelpfulAspectsChange = (aspect: string) => {
    setHelpfulAspects(prev =>
      prev.includes(aspect)
        ? prev.filter(item => item !== aspect)
        : [...prev, aspect]
    );
  };

  const handleImprovementAreasChange = (area: string) => {
    setImprovementAreas(prev =>
      prev.includes(area) ? prev.filter(item => item !== area) : [...prev, area]
    );
  };

  const handleSubmit = () => {
    onSubmit({
      evaluation,
      timeSaved,
      comment,
      expectedDocuments,
      expectedAnswer,
      helpfulAspects,
      improvementAreas,
    });
    onClose();
    // フォームをリセット
    setTimeSaved('');
    setComment('');
    setExpectedDocuments('');
    setExpectedAnswer('');
    setHelpfulAspects([]);
    setImprovementAreas([]);
  };

  const handleClose = () => {
    onClose();
    // フォームをリセット
    setTimeSaved('');
    setComment('');
    setExpectedDocuments('');
    setExpectedAnswer('');
    setHelpfulAspects([]);
    setImprovementAreas([]);
  };

  return (
    <Dialog open={isOpen} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>回答の評価（デモ）</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, pt: 1 }}>
          {/* 質問表示 */}
          {questionText && (
            <Box>
              <Typography variant="h6" sx={{ mb: 1, fontWeight: 'bold' }}>
                質問内容
              </Typography>
              <Box
                sx={{
                  p: 2,
                  bgcolor: '#e3f2fd',
                  borderRadius: 1,
                  maxHeight: '150px',
                  overflow: 'auto',
                  border: '1px solid #bbdefb',
                }}
              >
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                  {questionText}
                </Typography>
              </Box>
            </Box>
          )}

          {/* 回答表示 */}
          <Box>
            <Typography variant="h6" sx={{ mb: 1, fontWeight: 'bold' }}>
              回答内容
            </Typography>
            <Box
              sx={{
                p: 2,
                bgcolor: '#f5f5f5',
                borderRadius: 1,
                maxHeight: '300px',
                overflow: 'auto',
                border: '1px solid #e0e0e0',
              }}
            >
              <ReactMarkdown
                className="react-markdown"
                remarkPlugins={[remarkGfm]}
                components={{
                  // ソースリンクは評価モーダルでは無効化（クリック不可）
                  a: ({ node, ...props }) => {
                    if (
                      props.href === '' &&
                      props.children?.toString().startsWith('source-doc:')
                    ) {
                      return (
                        <Typography
                          component="span"
                          sx={{
                            fontSize: 11,
                            backgroundColor: 'rgba(0,0,0,0.1)',
                            borderRadius: '4px',
                            padding: '4px',
                            marginLeft: '4px',
                            cursor: 'default',
                          }}
                        >
                          ソース
                        </Typography>
                      );
                    }
                    return <a {...props} />;
                  },
                }}
              >
                {cleanedAnswerText}
              </ReactMarkdown>
            </Box>
          </Box>

          {/* 二値評価 */}
          <FormControl component="fieldset">
            <FormLabel component="legend">この回答はいかがでしたか？</FormLabel>
            <RadioGroup
              value={evaluation}
              onChange={e => setEvaluation(e.target.value as 'good' | 'bad')}
              row
            >
              <FormControlLabel value="good" control={<Radio />} label="良い" />
              <FormControlLabel value="bad" control={<Radio />} label="悪い" />
            </RadioGroup>
          </FormControl>

          {/* 削減時間（ボタン選択） */}
          <FormControl component="fieldset">
            <FormLabel component="legend">
              回答はあなたの作業時間をどの程度削減できましたか？
            </FormLabel>
            <ToggleButtonGroup
              value={timeSaved}
              exclusive
              onChange={(event, newValue) => {
                if (newValue !== null) {
                  setTimeSaved(newValue);
                }
              }}
              sx={{ mt: 1, flexWrap: 'wrap', gap: 1 }}
            >
              {timeSavedOptions.map(option => (
                <ToggleButton
                  key={option.value}
                  value={option.value}
                  sx={{
                    textTransform: 'none',
                    border: '1px solid #ccc',
                    '&.Mui-selected': {
                      backgroundColor: '#1976d2',
                      color: 'white',
                      '&:hover': {
                        backgroundColor: '#1565c0',
                      },
                    },
                  }}
                >
                  {option.label}
                </ToggleButton>
              ))}
            </ToggleButtonGroup>
          </FormControl>

          {/* 評価に応じたチェックボックス設問 */}
          {evaluation === 'good' && (
            <FormControl component="fieldset">
              <FormLabel component="legend">
                どのような点が役に立ちましたか？（複数回答可）
              </FormLabel>
              <FormGroup sx={{ mt: 1 }}>
                {helpfulOptions.map(option => (
                  <FormControlLabel
                    key={option}
                    control={
                      <Checkbox
                        checked={helpfulAspects.includes(option)}
                        onChange={() => handleHelpfulAspectsChange(option)}
                      />
                    }
                    label={option}
                  />
                ))}
              </FormGroup>
            </FormControl>
          )}

          {evaluation === 'bad' && (
            <FormControl component="fieldset">
              <FormLabel component="legend">
                改善すべき点は何ですか？（複数回答可）
              </FormLabel>
              <FormGroup sx={{ mt: 1 }}>
                {improvementOptions.map(option => (
                  <FormControlLabel
                    key={option}
                    control={
                      <Checkbox
                        checked={improvementAreas.includes(option)}
                        onChange={() => handleImprovementAreasChange(option)}
                      />
                    }
                    label={option}
                  />
                ))}
              </FormGroup>
            </FormControl>
          )}

          {/* 使用されるべきドキュメント */}
          <TextField
            label="使用されるべきドキュメント（カスタム質問想定）"
            multiline
            rows={3}
            value={expectedDocuments}
            onChange={e => setExpectedDocuments(e.target.value)}
            placeholder="この質問に対して参照されるべきドキュメントがあれば入力してください"
            helperText="回答に使用されるべきだったドキュメント名やファイル名を入力してください"
          />

          {/* 期待していた回答 */}
          <TextField
            label="期待していた回答（カスタム質問想定）"
            multiline
            rows={4}
            value={expectedAnswer}
            onChange={e => setExpectedAnswer(e.target.value)}
            placeholder="期待していた回答内容を入力してください"
            helperText="どのような回答を期待していたかを具体的に入力してください"
          />

          {/* 自由記述 */}
          <TextField
            label="コメント（任意）"
            multiline
            rows={3}
            value={comment}
            onChange={e => setComment(e.target.value)}
            placeholder="回答に対するご意見やご感想をお聞かせください"
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>キャンセル</Button>
        <Button onClick={handleSubmit} variant="contained">
          送信（未実装）
        </Button>
      </DialogActions>
    </Dialog>
  );
};

const AIComment: NextPage<AICommentType> = ({
  message,
  refFileList,
  setSelectedFile,
  previousMessage,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [evaluation, setEvaluation] = useState<'good' | 'bad' | null>(
    message.evaluation || null
  );

  // コピー機能のための状態を追加
  const [copyStatus, setCopyStatus] = useState<string>('コピー');

  // ダイアログの状態管理
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedFileName, setSelectedFileName] = useState('');
  const [selectedFileType, setSelectedFileType] = useState<
    'pdf' | 'xls' | 'xlsx' | 'xlsm' | null
  >(null);
  const [selectedDisplayName, setSelectedDisplayName] = useState('');

  // 評価モーダルの状態管理
  const [evaluationModalOpen, setEvaluationModalOpen] = useState(false);
  const [pendingEvaluation, setPendingEvaluation] = useState<
    'good' | 'bad' | null
  >(null);

  // SharePointパスの状態を追加
  const [sharePointPath, setSharePointPath] = useState('');

  // VideoStepリンクを抽出
  const videoStepLinks = extractVideoStepInfo(message.text);

  // VideoStepリンクを除去したテキストを作成
  const cleanedText = message.text.replace(
    /<videostep title="[^"]*" desc="[^"]*" url="[^"]*">/g,
    ''
  );

  // <source-doc> タグをクリック可能なリンクに変換する関数
  const processSourceDocTags = (text: string) => {
    const parts = [];
    const regex = /<source-doc:([^(]+)\(p\.(\d+)\)---([^>]+)>/g;
    let lastIndex = 0;
    let match;

    while ((match = regex.exec(text)) !== null) {
      // タグの前のテキスト
      if (match.index > lastIndex) {
        parts.push(text.substring(lastIndex, match.index));
      }

      const url = match[1];
      const pageNum = match[2];
      const filename = match[3];

      // ソースリンクコンポーネントを追加
      parts.push(
        <Tooltip key={match.index} title={filename}>
          <Typography
            component="span"
            sx={{
              fontSize: 11,
              cursor: 'pointer',
              backgroundColor: 'rgba(0,0,0,0.1)',
              borderRadius: '4px',
              padding: '4px',
              marginLeft: '4px',
            }}
            onClick={() => {
              openFileDialog(url, filename);
            }}
          >
            ソース
          </Typography>
        </Tooltip>
      );

      lastIndex = regex.lastIndex;
    }

    // 残りのテキスト
    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }

    return parts;
  };

  // コピー機能のハンドラを追加
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.text);
      setCopyStatus('コピーしました！');
      setTimeout(() => setCopyStatus('コピー'), 2000);
    } catch (error) {
      setCopyStatus('コピーに失敗しました');
      setTimeout(() => setCopyStatus('コピー'), 2000);
    }
  };

  const handleSendEvaluation = async (newEvaluation: 'good' | 'bad') => {
    setEvaluation(newEvaluation);
    const params = {
      message_id: message.message_id,
      evaluation: newEvaluation,
    };
    await putEvaluationApi(params);
  };

  const refFileInTextList = refFileList
    ? [...new Set(refFileList.map(file => [file[0].split('(p')[0], file[1]]))]
    : [];

  // ファイル選択ダイアログを開く
  const openFileDialog = (fileName: string, sharePointPathParam?: string) => {
    console.log(fileName);
    console.log('SharePoint path:', sharePointPathParam);
    const fileExt = fileName.split('.')[fileName.split('.').length - 1] as
      | 'pdf'
      | 'xls'
      | 'xlsx'
      | 'xlsm';
    setSelectedFileName(fileName);
    setSelectedFileType(fileExt);
    // SharePointのパス情報も保存
    setSharePointPath(sharePointPathParam || fileName);
    setDialogOpen(true);
    setSelectedDisplayName(sharePointPathParam || fileName);
  };

  // プレビューで開く
  const openInPreview = async () => {
    if (selectedFileType) {
      console.log('Opening file in preview:', {
        selectedFileName,
        selectedFileType,
      });

      try {
        // URLからファイル名を抽出
        let actualFileName = selectedFileName;

        // Azure Blob Storage URL形式の場合はファイル名部分だけ抽出
        if (
          selectedFileName.includes('blob.core.windows.net') ||
          selectedFileName.startsWith('http')
        ) {
          actualFileName =
            selectedFileName.split('/').pop() || selectedFileName;
          console.log('Extracted filename from URL:', {
            originalUrl: selectedFileName,
            extractedFileName: actualFileName,
          });
        }

        // SAS URLを生成してからプレビューを開く（直接APIサーバーにアクセス）
        const apiUrl =
          process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';
        const response = await fetch(
          `${apiUrl}/api/blob-storage/sas-url/${encodeURIComponent(actualFileName)}`
        );

        if (!response.ok) {
          console.error(
            'Failed to generate SAS URL:',
            response.status,
            response.statusText
          );
          const errorText = await response.text();
          console.error('SAS URL generation error details:', errorText);
          throw new Error(
            `SAS URL生成に失敗しました: ${response.status} - ${errorText}`
          );
        }

        const data = await response.json();
        console.log('SAS URL generated successfully:', {
          blob_name: data.blob_name,
          url: data.sas_url,
        });

        setSelectedFile({
          fileType: selectedFileType,
          url: data.sas_url, // SAS URLを使用
        });
        setDialogOpen(false);
      } catch (error) {
        console.error('Error opening file in preview:', error);

        // エラーメッセージをユーザーに表示
        const errorMessage =
          error instanceof Error ? error.message : String(error);
        alert(
          `ファイルの読み込みに失敗しました: ${errorMessage}\n\nファイル名: ${selectedFileName}`
        );

        // ダイアログは閉じる
        setDialogOpen(false);
      }
    }
  };

  // ダウンロード機能のハンドラを追加
  const handleDownload = () => {
    const today = new Date();
    const dateStr = today.toISOString().split('T')[0];

    // 質問文を取得（存在する場合）
    const questionText = previousMessage?.text || '';

    // ファイル名を生成（質問文が長い場合は切り詰める）
    let fileName = `${dateStr}_${questionText}`;
    if (fileName.length > 100) {
      fileName = fileName.substring(0, 100) + '...';
    }
    fileName = fileName.replace(/[<>:"/\\|?*]/g, '_') + '.txt';

    // 参照元のファイルパスを取得
    const refFiles = refFileList?.map(file => file[0].split('(p')[0]) || [];

    // テキストコンテンツを構築
    const content = [
      '【質問】',
      questionText,
      '',
      '【回答】',
      message.text,
      '',
      '【参照元】',
      ...refFiles,
    ].join('\n');

    // Blobを作成してダウンロード
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // 評価ボタンのハンドラを修正
  const handleEvaluationClick = (newEvaluation: 'good' | 'bad') => {
    setPendingEvaluation(newEvaluation);
    setEvaluationModalOpen(true);
  };

  // 評価モーダルの送信ハンドラ
  const handleEvaluationSubmit = async (data: {
    evaluation: 'good' | 'bad';
    timeSaved: string;
    comment: string;
    expectedDocuments: string;
    expectedAnswer: string;
    helpfulAspects: string[];
    improvementAreas: string[];
  }) => {
    setEvaluation(data.evaluation);

    // ここでサーバーに送信する処理を実装
    // 現在はデモなので、コンソールに出力
    console.log('評価データ:', {
      message_id: message.message_id,
      evaluation: data.evaluation,
      timeSaved: data.timeSaved,
      comment: data.comment,
      expectedDocuments: data.expectedDocuments,
      expectedAnswer: data.expectedAnswer,
      helpfulAspects: data.helpfulAspects,
      improvementAreas: data.improvementAreas,
    });

    // 既存のAPI呼び出し（必要に応じて拡張）
    const params = {
      message_id: message.message_id,
      evaluation: data.evaluation,
    };
    await putEvaluationApi(params);
  };

  return (
    <div
      className={`self-stretch bg-white flex flex-row items-start justify-start gap-6 text-left not-italic text-base leading-normal font-sans overflow-x-hidden`}
    >
      <img
        className="relative w-8 h-8 object-cover"
        alt=""
        src="/ai-icon.png"
      />
      <div className="flex-1 flex flex-col items-start justify-start gap-2 pt-1">
        <Box className="react-markdown self-stretch">
          {processSourceDocTags(cleanedText).map((part, index) =>
            typeof part === 'string' ? (
              <ReactMarkdown
                key={index}
                remarkPlugins={[remarkGfm]}
                components={{
                  p: ({ node, ...props }) => <span {...props} />,
                }}
              >
                {part}
              </ReactMarkdown>
            ) : (
              part
            )
          )}
        </Box>

        {/* VideoStepカードを表示 */}
        {videoStepLinks.length > 0 && (
          <Box sx={{ width: '100%', mt: 2 }}>
            {videoStepLinks.map((link, index) => (
              <VideoStepCard
                key={index}
                title={link.title}
                desc={link.desc}
                url={link.url}
              />
            ))}
          </Box>
        )}

        {refFileList && refFileList.length > 0 && (
          <>
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="text-sm text-slategray mb-2"
            >
              {isOpen ? '参照先を非表示' : '参照先を表示'}
            </button>
            {isOpen &&
              refFileInTextList.map((refFile, index) => (
                <Tooltip
                  key={index}
                  title={refFile[0]}
                  arrow
                  placement="bottom"
                >
                  <i
                    className="cursor-pointer text-sm text-slategray"
                    onClick={() => {
                      // プレビュー用のファイル名
                      const fileName = refFile[1].split('(p')[0];
                      // SharePointリンク用のパス情報
                      const sharePointFileName = refFile[0];
                      openFileDialog(fileName, sharePointFileName);
                    }}
                  >
                    {refFile[0].replace(/^.*\/([^/]+)$/, '$1')}
                  </i>
                </Tooltip>
              ))}
          </>
        )}
        <div className="flex flex-row items-center justify-start">
          <Tooltip title="ダウンロード" arrow placement="bottom">
            <button
              className="cursor-pointer border-none p-0 bg-transparent mr-4"
              onClick={handleDownload}
            >
              <DownloadIcon className="h-6 w-6 text-slategray hover:brightness-50 hover:contrast-200" />
            </button>
          </Tooltip>
          <Tooltip title={copyStatus} arrow placement="bottom">
            <button
              className="cursor-pointer border-none p-0 bg-transparent"
              onClick={handleCopy}
            >
              <CopyIcon className="h-6 w-6 text-slategray hover:brightness-50 hover:contrast-200" />
            </button>
          </Tooltip>
          <div className="pl-4">
            {evaluation === 'good' ? (
              <ThumbUpIcon
                sx={{ color: 'gray', fontSize: 35 }}
                className="px-2 cursor-pointer"
                onClick={() => handleEvaluationClick('good')}
              />
            ) : (
              <ThumbUpOutlinedIcon
                sx={{ color: 'gray', fontSize: 35 }}
                className="px-2 cursor-pointer"
                onClick={() => handleEvaluationClick('good')}
              />
            )}
            {evaluation === 'bad' ? (
              <ThumbDownIcon
                sx={{ color: 'gray', fontSize: 35 }}
                className="px-2 cursor-pointer"
                onClick={() => handleEvaluationClick('bad')}
              />
            ) : (
              <ThumbDownOutlinedIcon
                sx={{ color: 'gray', fontSize: 35 }}
                className="px-2 cursor-pointer"
                onClick={() => handleEvaluationClick('bad')}
              />
            )}
          </div>
        </div>

        {/* ファイル選択ダイアログ */}
        <LinkOptionsDialog
          isOpen={dialogOpen}
          onClose={() => setDialogOpen(false)}
          onPreview={openInPreview}
          fileName={selectedFileName}
          displayName={selectedDisplayName}
          sharePointPath={sharePointPath}
        />

        {/* 評価モーダル */}
        <EvaluationModal
          isOpen={evaluationModalOpen}
          onClose={() => setEvaluationModalOpen(false)}
          onSubmit={handleEvaluationSubmit}
          initialEvaluation={pendingEvaluation || undefined}
          answerText={message.text}
          questionText={previousMessage?.text}
        />
      </div>
    </div>
  );
};

export default AIComment;
