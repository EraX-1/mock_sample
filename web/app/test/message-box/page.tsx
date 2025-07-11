'use client';

import React, { useState } from 'react';
import MessageBox from '@/components/chat/message-box';
import { ChatModelType, ChatIndexType } from '@/types/chat';

export default function MessageBoxTestPage() {
  const [selectedText, setSelectedText] = useState<string>('');
  const [customPrompt, setCustomPrompt] = useState<string>('');
  const [isCustomPromptActive, setIsCustomPromptActive] =
    useState<boolean>(false);
  const [tokenCount, setTokenCount] = useState<number>(700);
  const [selectedModel, setSelectedModel] = useState<ChatModelType>(
    'gpt-4o' as ChatModelType
  );
  const [indexType, setIndexType] = useState<ChatIndexType[]>([]);

  const indexTypeOptions = [
    { value: 'test1', label: 'テストインデックス1' },
    { value: 'test2', label: 'テストインデックス2' },
  ];

  const handleModelChange = (event: any) => {
    setSelectedModel(event.target.value as ChatModelType);
  };

  const handleSubmit = () => {
    console.log('Submit:', selectedText);
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1>MessageBox テストページ</h1>
      <p>
        このページでMessageBoxコンポーネントのLLMモデルドロップダウンをテストできます。
      </p>

      <div style={{ marginTop: '30px' }}>
        <MessageBox
          selectedText={selectedText}
          setSelectedText={setSelectedText}
          onSubmit={handleSubmit}
          customPrompt={customPrompt}
          setCustomPrompt={setCustomPrompt}
          isCustomPromptActive={isCustomPromptActive}
          setIsCustomPromptActive={setIsCustomPromptActive}
          tokenCount={tokenCount}
          setTokenCount={setTokenCount}
          selectedModel={selectedModel}
          setSelectedModel={setSelectedModel}
          handleModelChange={handleModelChange}
          indexType={indexType}
          setIndexType={setIndexType}
          indexTypeOptions={indexTypeOptions}
        />
      </div>

      <div
        style={{
          marginTop: '20px',
          padding: '10px',
          backgroundColor: '#f5f5f5',
        }}
      >
        <h3>デバッグ情報:</h3>
        <p>選択されたモデル: {selectedModel}</p>
        <p>メッセージ: {selectedText}</p>
        <p>トークン数: {tokenCount}</p>
      </div>
    </div>
  );
}
