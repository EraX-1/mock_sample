'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Tooltip,
  Avatar,
  Badge,
  Menu,
  MenuItem,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  Fab,
  Chip,
} from '@mui/material';
import {
  ScreenShare as ScreenShareIcon,
  StopScreenShare as StopScreenShareIcon,
  Comment as CommentIcon,
  Person as PersonIcon,
  Videocam as VideocamIcon,
  VideocamOff as VideocamOffIcon,
  Mic as MicIcon,
  MicOff as MicOffIcon,
  Code as CodeIcon,
  Assignment as AssignmentIcon,
} from '@mui/icons-material';

interface CollaborationUser {
  id: string;
  name: string;
  avatar?: string;
  status: 'online' | 'away' | 'busy';
  isSharing?: boolean;
  cursor?: { x: number; y: number };
}

interface Comment {
  id: string;
  userId: string;
  userName: string;
  content: string;
  timestamp: Date;
  position: { x: number; y: number };
  resolved: boolean;
}

interface CodeReview {
  id: string;
  file: string;
  line: number;
  reviewer: string;
  comment: string;
  severity: 'info' | 'warning' | 'error';
  status: 'pending' | 'resolved';
}

const RealtimeCollaboration: React.FC = () => {
  const [users, setUsers] = useState<CollaborationUser[]>([
    { id: '1', name: 'Developer 1', status: 'online' },
    { id: '2', name: 'Designer 1', status: 'online' },
    { id: '3', name: 'PM 1', status: 'away' },
  ]);

  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [comments, setComments] = useState<Comment[]>([]);
  const [showCommentDialog, setShowCommentDialog] = useState(false);
  const [commentPosition, setCommentPosition] = useState({ x: 0, y: 0 });
  const [newComment, setNewComment] = useState('');
  const [codeReviews, setCodeReviews] = useState<CodeReview[]>([
    {
      id: '1',
      file: 'chat-section.tsx',
      line: 157,
      reviewer: 'AI Reviewer',
      comment:
        'この部分でメモリリークの可能性があります。useCallback の依存配列を確認してください。',
      severity: 'warning',
      status: 'pending',
    },
    {
      id: '2',
      file: 'message-box.tsx',
      line: 92,
      reviewer: 'AI Reviewer',
      comment:
        'アクセシビリティの改善: aria-label を追加することを推奨します。',
      severity: 'info',
      status: 'pending',
    },
  ]);

  const videoRef = useRef<HTMLVideoElement>(null);
  const [isVideoEnabled, setIsVideoEnabled] = useState(false);
  const [isAudioEnabled, setIsAudioEnabled] = useState(false);
  const [stream, setStream] = useState<MediaStream | null>(null);

  const initializeCollaboration = useCallback(() => {
    // WebSocket接続やWebRTC設定
    console.log('コラボレーション機能を初期化しています...');

    // マウスカーソルの追跡
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('click', handleClick);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('click', handleClick);
    };
  }, []);

  useEffect(() => {
    // リアルタイム通信の初期化（WebSocket, WebRTCなど）
    initializeCollaboration();

    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, [initializeCollaboration, stream]);

  const handleMouseMove = (e: MouseEvent) => {
    // 他のユーザーにカーソル位置を送信
    const cursorData = {
      x: e.clientX,
      y: e.clientY,
      userId: 'current-user',
    };
    // WebSocketで送信
    console.log('カーソル位置:', cursorData);
  };

  const handleClick = (e: MouseEvent) => {
    // 右クリックでコメント追加
    if (e.button === 2) {
      e.preventDefault();
      setCommentPosition({ x: e.clientX, y: e.clientY });
      setShowCommentDialog(true);
    }
  };

  const startScreenShare = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getDisplayMedia({
        video: true,
        audio: true,
      });

      setStream(mediaStream);
      setIsScreenSharing(true);

      // 他のユーザーに画面共有開始を通知
      broadcastScreenShare(mediaStream);

      mediaStream.getVideoTracks()[0].onended = () => {
        stopScreenShare();
      };
    } catch (error) {
      console.error('画面共有の開始に失敗:', error);
    }
  };

  const stopScreenShare = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
    setIsScreenSharing(false);
  };

  const broadcastScreenShare = (mediaStream: MediaStream) => {
    // WebRTCで他のユーザーに画面共有
    console.log('画面共有を開始しました');
  };

  const toggleVideo = async () => {
    if (!isVideoEnabled) {
      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({
          video: true,
        });
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
        }
        setStream(mediaStream);
        setIsVideoEnabled(true);
      } catch (error) {
        console.error('ビデオの開始に失敗:', error);
      }
    } else {
      if (stream) {
        stream.getVideoTracks().forEach(track => track.stop());
      }
      setIsVideoEnabled(false);
    }
  };

  const toggleAudio = async () => {
    if (!isAudioEnabled) {
      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({
          audio: true,
        });
        setIsAudioEnabled(true);
      } catch (error) {
        console.error('オーディオの開始に失敗:', error);
      }
    } else {
      setIsAudioEnabled(false);
    }
  };

  const addComment = () => {
    if (newComment.trim()) {
      const comment: Comment = {
        id: Date.now().toString(),
        userId: 'current-user',
        userName: 'Current User',
        content: newComment,
        timestamp: new Date(),
        position: commentPosition,
        resolved: false,
      };

      setComments([...comments, comment]);
      setNewComment('');
      setShowCommentDialog(false);
    }
  };

  const runAICodeReview = () => {
    // AI駆動のコードレビューを実行
    const newReview: CodeReview = {
      id: Date.now().toString(),
      file: 'current-file.tsx',
      line: Math.floor(Math.random() * 100),
      reviewer: 'AI Reviewer',
      comment:
        'パフォーマンスの改善提案: useMemo を使用してレンダリング最適化を行ってください。',
      severity: 'info',
      status: 'pending',
    };

    setCodeReviews([...codeReviews, newReview]);
  };

  const generateDocumentation = () => {
    // 自動ドキュメント生成
    console.log('API仕様書を自動生成しています...');

    // OpenAPIスキーマ生成のシミュレーション
    const apiDoc = {
      openapi: '3.0.0',
      info: {
        title: 'Yuyama RAG Chatbot API',
        version: '1.0.0',
      },
      paths: {
        '/chat_messages': {
          post: {
            summary: 'チャットメッセージを送信',
            description: 'ユーザーからのメッセージを受信してAI応答を生成',
          },
        },
      },
    };

    console.log('生成されたAPI仕様:', apiDoc);
  };

  return (
    <Box sx={{ position: 'relative', height: '100%' }}>
      {/* ユーザー一覧 */}
      <Paper
        sx={{
          position: 'fixed',
          top: 20,
          right: 20,
          p: 2,
          zIndex: 1000,
          minWidth: 200,
        }}
      >
        <Typography variant="h6" sx={{ mb: 2 }}>
          コラボレーション
        </Typography>

        {users.map(user => (
          <Box
            key={user.id}
            sx={{ display: 'flex', alignItems: 'center', mb: 1 }}
          >
            <Badge
              color={
                user.status === 'online'
                  ? 'success'
                  : user.status === 'away'
                    ? 'warning'
                    : 'error'
              }
              variant="dot"
            >
              <Avatar sx={{ width: 32, height: 32, mr: 1 }}>
                {user.name[0]}
              </Avatar>
            </Badge>
            <Typography variant="body2">{user.name}</Typography>
            {user.isSharing && (
              <ScreenShareIcon
                sx={{ ml: 1, fontSize: 16, color: 'primary.main' }}
              />
            )}
          </Box>
        ))}

        {/* コントロールボタン */}
        <Box sx={{ mt: 2, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          <Tooltip
            title={isScreenSharing ? '画面共有を停止' : '画面共有を開始'}
          >
            <IconButton
              onClick={isScreenSharing ? stopScreenShare : startScreenShare}
              color={isScreenSharing ? 'secondary' : 'default'}
            >
              {isScreenSharing ? <StopScreenShareIcon /> : <ScreenShareIcon />}
            </IconButton>
          </Tooltip>

          <Tooltip title={isVideoEnabled ? 'ビデオを停止' : 'ビデオを開始'}>
            <IconButton
              onClick={toggleVideo}
              color={isVideoEnabled ? 'primary' : 'default'}
            >
              {isVideoEnabled ? <VideocamIcon /> : <VideocamOffIcon />}
            </IconButton>
          </Tooltip>

          <Tooltip title={isAudioEnabled ? 'マイクを無効' : 'マイクを有効'}>
            <IconButton
              onClick={toggleAudio}
              color={isAudioEnabled ? 'primary' : 'default'}
            >
              {isAudioEnabled ? <MicIcon /> : <MicOffIcon />}
            </IconButton>
          </Tooltip>
        </Box>
      </Paper>

      {/* ビデオ通話 */}
      {isVideoEnabled && (
        <Paper
          sx={{
            position: 'fixed',
            bottom: 20,
            right: 20,
            width: 200,
            height: 150,
            zIndex: 1000,
          }}
        >
          <video
            ref={videoRef}
            autoPlay
            muted
            style={{ width: '100%', height: '100%' }}
          />
        </Paper>
      )}

      {/* コードレビューパネル */}
      <Paper
        sx={{
          position: 'fixed',
          bottom: 20,
          left: 20,
          p: 2,
          maxWidth: 400,
          zIndex: 1000,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <CodeIcon sx={{ mr: 1 }} />
          <Typography variant="h6">AI コードレビュー</Typography>
          <Button size="small" onClick={runAICodeReview} sx={{ ml: 'auto' }}>
            実行
          </Button>
        </Box>

        {codeReviews.slice(0, 3).map(review => (
          <Box
            key={review.id}
            sx={{ mb: 2, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Chip
                label={review.severity}
                size="small"
                color={
                  review.severity === 'error'
                    ? 'error'
                    : review.severity === 'warning'
                      ? 'warning'
                      : 'info'
                }
              />
              <Typography variant="caption" sx={{ ml: 1 }}>
                {review.file}:{review.line}
              </Typography>
            </Box>
            <Typography variant="body2">{review.comment}</Typography>
          </Box>
        ))}
      </Paper>

      {/* フローティングアクションボタン */}
      <Fab
        color="primary"
        sx={{ position: 'fixed', bottom: 200, right: 20 }}
        onClick={generateDocumentation}
      >
        <AssignmentIcon />
      </Fab>

      {/* コメント表示 */}
      {comments.map(comment => (
        <Paper
          key={comment.id}
          sx={{
            position: 'absolute',
            left: comment.position.x,
            top: comment.position.y,
            p: 1,
            maxWidth: 200,
            zIndex: 999,
          }}
        >
          <Typography variant="caption" color="primary">
            {comment.userName}
          </Typography>
          <Typography variant="body2">{comment.content}</Typography>
          <Typography variant="caption" color="text.secondary">
            {comment.timestamp.toLocaleTimeString()}
          </Typography>
        </Paper>
      ))}

      {/* コメント追加ダイアログ */}
      <Dialog
        open={showCommentDialog}
        onClose={() => setShowCommentDialog(false)}
      >
        <DialogTitle>コメントを追加</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            multiline
            rows={3}
            fullWidth
            placeholder="コメントを入力..."
            value={newComment}
            onChange={e => setNewComment(e.target.value)}
          />
          <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
            <Button onClick={addComment} variant="contained">
              追加
            </Button>
            <Button onClick={() => setShowCommentDialog(false)}>
              キャンセル
            </Button>
          </Box>
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default RealtimeCollaboration;
