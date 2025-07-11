'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Tooltip,
  Card,
  CardContent,
  Dialog,
  DialogTitle,
  DialogContent,
  Button,
  Chip,
} from '@mui/material';
import {
  AccountTree as FlowIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  Fullscreen as FullscreenIcon,
  Search as SearchIcon,
} from '@mui/icons-material';

interface ConversationNode {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  tokens: number;
  timestamp: Date;
  children: string[];
  parent?: string;
  metadata?: {
    model?: string;
    indexTypes?: string[];
    references?: string[];
  };
}

interface FlowVisualizerProps {
  messages: Array<{
    type: 'user' | 'assistant';
    text: string;
    message_id?: string;
    model?: string;
    indexTypes?: { id: string; label: string }[];
    refFileList?: string[];
  }>;
}

const ConversationFlowVisualizer: React.FC<FlowVisualizerProps> = ({
  messages,
}) => {
  const [nodes, setNodes] = useState<ConversationNode[]>([]);
  const [selectedNode, setSelectedNode] = useState<ConversationNode | null>(
    null
  );
  const [zoom, setZoom] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    // メッセージをノードに変換
    const convertedNodes: ConversationNode[] = messages.map(
      (message, index) => ({
        id: message.message_id || `msg-${index}`,
        type: message.type,
        content: message.text,
        tokens: estimateTokens(message.text),
        timestamp: new Date(),
        children:
          index < messages.length - 1
            ? [messages[index + 1]?.message_id || `msg-${index + 1}`]
            : [],
        parent:
          index > 0
            ? messages[index - 1]?.message_id || `msg-${index - 1}`
            : undefined,
        metadata: {
          model: message.model,
          indexTypes: message.indexTypes?.map(t => t.label),
          references: message.refFileList,
        },
      })
    );

    setNodes(convertedNodes);
  }, [messages]);

  const estimateTokens = (text: string): number => {
    // 簡単なトークン推定（実際の実装では gpt-tokenizer を使用）
    return Math.ceil(text.length / 4);
  };

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.2, 3));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.2, 0.5));

  const getNodeColor = (type: string): string => {
    switch (type) {
      case 'user':
        return '#e3f2fd';
      case 'assistant':
        return '#f3e5f5';
      case 'system':
        return '#fff3e0';
      default:
        return '#f5f5f5';
    }
  };

  const getNodeBorderColor = (type: string): string => {
    switch (type) {
      case 'user':
        return '#2196f3';
      case 'assistant':
        return '#9c27b0';
      case 'system':
        return '#ff9800';
      default:
        return '#bdbdbd';
    }
  };

  const filteredNodes = nodes.filter(
    node =>
      searchTerm === '' ||
      node.content.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const renderNode = (node: ConversationNode, index: number) => (
    <Card
      key={node.id}
      sx={{
        minWidth: 200,
        maxWidth: 300,
        m: 1,
        backgroundColor: getNodeColor(node.type),
        border: `2px solid ${getNodeBorderColor(node.type)}`,
        cursor: 'pointer',
        transform: `scale(${zoom})`,
        transformOrigin: 'top left',
        '&:hover': {
          boxShadow: 4,
          transform: `scale(${zoom * 1.05})`,
        },
      }}
      onClick={() => setSelectedNode(node)}
    >
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Chip
            label={node.type}
            size="small"
            color={node.type === 'user' ? 'primary' : 'secondary'}
          />
          <Typography variant="caption" sx={{ ml: 1 }}>
            {node.tokens} tokens
          </Typography>
        </Box>

        <Typography
          variant="body2"
          sx={{
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            display: '-webkit-box',
            WebkitLineClamp: 3,
            WebkitBoxOrient: 'vertical',
          }}
        >
          {node.content}
        </Typography>

        {node.metadata?.model && (
          <Chip label={node.metadata.model} size="small" sx={{ mt: 1 }} />
        )}

        {node.metadata?.indexTypes && node.metadata.indexTypes.length > 0 && (
          <Box sx={{ mt: 1 }}>
            {node.metadata.indexTypes.map((type, idx) => (
              <Chip
                key={idx}
                label={type}
                size="small"
                variant="outlined"
                sx={{ mr: 0.5, mb: 0.5 }}
              />
            ))}
          </Box>
        )}
      </CardContent>
    </Card>
  );

  const renderConnectionLine = (fromIndex: number, toIndex: number) => {
    // SVGで接続線を描画（簡略化）
    return (
      <svg
        key={`line-${fromIndex}-${toIndex}`}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          pointerEvents: 'none',
          zIndex: -1,
        }}
      >
        <line
          x1={150}
          y1={fromIndex * 120 + 60}
          x2={150}
          y2={toIndex * 120 + 60}
          stroke="#bdbdbd"
          strokeWidth="2"
          markerEnd="url(#arrowhead)"
        />
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon points="0 0, 10 3.5, 0 7" fill="#bdbdbd" />
          </marker>
        </defs>
      </svg>
    );
  };

  return (
    <>
      <Paper sx={{ p: 2, height: 400, overflow: 'hidden' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <FlowIcon sx={{ mr: 1 }} />
          <Typography variant="h6">会話フロー</Typography>

          <Box sx={{ ml: 'auto', display: 'flex', gap: 1 }}>
            <Tooltip title="ズームイン">
              <IconButton onClick={handleZoomIn}>
                <ZoomInIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="ズームアウト">
              <IconButton onClick={handleZoomOut}>
                <ZoomOutIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="フルスクリーン">
              <IconButton onClick={() => setIsFullscreen(true)}>
                <FullscreenIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        <Box
          sx={{
            height: '100%',
            overflow: 'auto',
            position: 'relative',
            '&::-webkit-scrollbar': {
              width: '8px',
              height: '8px',
            },
            '&::-webkit-scrollbar-thumb': {
              backgroundColor: '#cccccc',
              borderRadius: '4px',
            },
          }}
        >
          {filteredNodes.map((node, index) => (
            <Box key={node.id} sx={{ position: 'relative' }}>
              {renderNode(node, index)}
              {index < filteredNodes.length - 1 &&
                renderConnectionLine(index, index + 1)}
            </Box>
          ))}
        </Box>
      </Paper>

      {/* 詳細ダイアログ */}
      <Dialog
        open={selectedNode !== null}
        onClose={() => setSelectedNode(null)}
        maxWidth="md"
        fullWidth
      >
        {selectedNode && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Chip
                  label={selectedNode.type}
                  color={selectedNode.type === 'user' ? 'primary' : 'secondary'}
                  sx={{ mr: 2 }}
                />
                <Typography variant="h6">メッセージ詳細</Typography>
              </Box>
            </DialogTitle>
            <DialogContent>
              <Typography variant="body1" sx={{ mb: 2 }}>
                {selectedNode.content}
              </Typography>

              <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                <Typography variant="body2">
                  <strong>トークン数:</strong> {selectedNode.tokens}
                </Typography>
                <Typography variant="body2">
                  <strong>送信時刻:</strong>{' '}
                  {selectedNode.timestamp.toLocaleString()}
                </Typography>
              </Box>

              {selectedNode.metadata?.model && (
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>モデル:</strong> {selectedNode.metadata.model}
                </Typography>
              )}

              {selectedNode.metadata?.indexTypes &&
                selectedNode.metadata.indexTypes.length > 0 && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      <strong>参照インデックス:</strong>
                    </Typography>
                    {selectedNode.metadata.indexTypes.map((type, idx) => (
                      <Chip
                        key={idx}
                        label={type}
                        size="small"
                        sx={{ mr: 1, mb: 1 }}
                      />
                    ))}
                  </Box>
                )}

              {selectedNode.metadata?.references &&
                selectedNode.metadata.references.length > 0 && (
                  <Box>
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      <strong>参照ファイル:</strong>
                    </Typography>
                    {selectedNode.metadata.references.map((ref, idx) => (
                      <Chip
                        key={idx}
                        label={ref}
                        size="small"
                        variant="outlined"
                        sx={{ mr: 1, mb: 1 }}
                      />
                    ))}
                  </Box>
                )}
            </DialogContent>
          </>
        )}
      </Dialog>

      {/* フルスクリーンダイアログ */}
      <Dialog
        open={isFullscreen}
        onClose={() => setIsFullscreen(false)}
        fullScreen
      >
        <Box
          sx={{
            p: 2,
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Typography variant="h5" sx={{ mr: 2 }}>
              会話フロー分析
            </Typography>
            <Button onClick={() => setIsFullscreen(false)}>閉じる</Button>
          </Box>

          {/* フルスクリーン版のフロー表示 */}
          <Box sx={{ flex: 1, overflow: 'auto' }}>
            {/* より詳細なフロー表示をここに実装 */}
            <Typography>詳細なフロー分析機能（開発中）</Typography>
          </Box>
        </Box>
      </Dialog>
    </>
  );
};

export default ConversationFlowVisualizer;
