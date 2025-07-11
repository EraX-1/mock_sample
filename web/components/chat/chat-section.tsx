'use client';

import React, { useRef } from 'react';

import ChatMessage from './chat-message';
import AIComment from './ai-comment';
import MessageBox from './message-box';
import { useCallback, useEffect, useState } from 'react';

import { CircularProgress, Tooltip, Box } from '@mui/material';
import ChatIcon from '@mui/icons-material/Chat';
import { SelectChangeEvent } from '@mui/material/Select';
import {
  createChatMessageApi,
  getListChatMessagesApi,
  getChatRoomApi,
  getSearchIndexTypesForUserApi,
} from '@/services/apiService';
import AICommentLoading from './ai-comment-loading';
import { ChatIndexType } from '@/types/chat';
import FilePreviewer from './file-previewer';
import { getModelLS, setModelLS } from '@/services/localStorageService';
import { ChatModelType } from '@/types/chat';

export type ChatMessage = {
  type: 'user' | 'assistant';
  text: string;
  refFileList?: string[];
  message_id?: string;
  evaluation?: 'good' | 'bad';
  model?: string;
  indexTypes?: { id: string; label: string }[];
};

interface ChatSectionType {
  chatRoomId: string;
  indexType: ChatIndexType[];
  setIndexType: (types: ChatIndexType[]) => void;
  sendChatroomName: (chat_room_id: string, name: string) => void;
}

const INITIAL_TOKEN = 700;
const initModel: ChatModelType = process.env
  .NEXT_PUBLIC_DEFAULT_MODEL as ChatModelType;

const ChatSection = React.memo<ChatSectionType>(
  ({ chatRoomId, indexType, setIndexType, sendChatroomName }) => {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [selectedText, setSelectedText] = useState<string>('');
    const [assistantPrompt, setAssistantPrompt] = useState<string>('');
    const [isCustomPromptActive, setIsCustomPromptActive] =
      useState<boolean>(false);
    const [isAILoading, setIsAILoading] = useState<boolean>(false);
    const [chatMessages, setChatMessages] = useState<any>([]);
    const [isChatMessageLoading, setIsChatMessageLoading] = useState<any>(true);
    const [error, setError] = useState<any>();
    const firstResRef = useRef<boolean>(true);
    const [indexTypeOptions, setIndexTypeOptions] = useState<
      { value: string; label: string }[]
    >([]);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const [selectedModel, setSelectedModel] =
      useState<ChatModelType>(initModel);

    const [tokenCount, setTokenCount] = useState<number>(INITIAL_TOKEN);

    const [selectedFile, setSelectedFile] = useState<{
      fileType: 'pdf' | 'xls' | 'xlsx' | 'xlsm';
      url: string;
    } | null>(null);

    useEffect(() => {
      const modelInLS = getModelLS();
      if (modelInLS) {
        setSelectedModel(modelInLS);
      }
    }, []);

    useEffect(() => {
      (async () => {
        const { response } = await getSearchIndexTypesForUserApi();
        if (response) {
          const options = response.map((indexTypeItem: any) => ({
            value: indexTypeItem.id,
            label: indexTypeItem.folder_name,
          }));
          setIndexTypeOptions(options);
        }
      })();
    }, []);

    useEffect(() => {
      (async () => {
        if (chatRoomId) {
          const { response: messagesRes } = await getListChatMessagesApi({
            chat_room_id: chatRoomId,
          });
          setChatMessages(messagesRes);
          setError(error);
          const { response: chatroomRes } = await getChatRoomApi({
            chat_room_id: chatRoomId,
          });
          if (
            chatroomRes &&
            chatroomRes.is_active_custom_prompt &&
            chatroomRes.custom_prompt
          ) {
            setAssistantPrompt(chatroomRes.custom_prompt);
            setIsCustomPromptActive(true);
          }
        }
        setIsChatMessageLoading(false);
      })();
    }, [chatRoomId, error]);

    useEffect(() => {
      if (chatMessages) {
        setMessages(
          chatMessages.map((message: any) => ({
            type: message.role,
            text: message.message,
            refFileList: message.references,
            message_id: message.id,
            evaluation: message.evaluation,
            model: message.model,
            indexTypes: message.index_types
              ? message.index_types.map((indexTypeId: string) => {
                  // indexTypeOptionsからラベル情報を取得
                  const typeOption = indexTypeOptions.find(
                    opt => opt.value === indexTypeId
                  );
                  return {
                    id: indexTypeId,
                    label: typeOption ? typeOption.label : indexTypeId, // 見つからない場合はIDをそのまま表示
                  };
                })
              : undefined,
          }))
        );
      }
    }, [chatMessages, indexTypeOptions]);

    const handleModelChange = (event: SelectChangeEvent) => {
      setSelectedModel(event.target.value as ChatModelType);
      setModelLS(event.target.value as ChatModelType);
    };

    useEffect(() => {
      // コンポーネントが更新されるたびに実行
      messagesEndRef?.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSubmit = useCallback(async () => {
      if (!selectedText.trim()) return;

      setIsAILoading(true);
      // 最初のメッセージならチャットルーム名更新
      if (messages.length === 0) {
        const newChatroomName = selectedText.slice(0, 20);
        sendChatroomName(chatRoomId, newChatroomName);
        // TODO: コンテキストを使用するかどうか要検討
        const event = new CustomEvent(`changeChatroomName_${chatRoomId}`, {
          detail: {
            name: newChatroomName,
          },
        });
        window.dispatchEvent(event);
      }

      // 楽観的更新
      setMessages([
        ...messages,
        {
          type: 'user',
          text: selectedText,
          model: selectedModel,
          indexTypes: indexType.map(id => {
            const option = indexTypeOptions.find(opt => opt.value === id);
            return {
              id,
              label: option ? option.label : id,
            };
          }),
        },
      ]);

      try {
        const chatHistory = messages.map(message => {
          if (message.type === 'user') {
            return {
              type: 'user',
              content: message.text,
            };
          } else if (message.type === 'assistant') {
            return {
              type: 'assistant',
              content: message.text,
            };
          }
        });

        const params = {
          chat_room_id: chatRoomId,
          message: selectedText,
          assistant_prompt: assistantPrompt,
          is_active_assistant_prompt: isCustomPromptActive,
          chat_history: chatHistory,
          index_type: indexType,
          index_type_details: indexType.map(id => {
            const option = indexTypeOptions.find(opt => opt.value === id);
            return {
              id,
              folder_name: option ? option.label : id,
            };
          }),
          model: selectedModel,
        };

        let buffer = '';
        const { response: _, error } = await createChatMessageApi(
          params,
          chunk => {
            buffer += chunk;

            // <<USED_TOKEN_START>> と <<REFERENCES_START>> の処理を分離
            if (buffer.includes('<<USED_TOKEN_START>>')) {
              const [messagePart, tokenPart] = buffer.split(
                '<<USED_TOKEN_START>>'
              );

              // メッセージ部分を処理
              if (messagePart.trim()) {
                setMessages(prevMessages => {
                  const updatedMessages = [...prevMessages];
                  const lastIndex = updatedMessages.length - 1;
                  if (updatedMessages[lastIndex].type === 'assistant') {
                    updatedMessages[lastIndex] = {
                      ...updatedMessages[lastIndex],
                      text: messagePart.trim(),
                    };
                  }
                  return updatedMessages;
                });
              }

              // バッファを更新
              buffer = tokenPart || '';
            }

            // <<REFERENCES_START>> の処理を独立して行う
            if (buffer.includes('<<REFERENCES_START>>')) {
              const [_, referencesPart] = buffer.split('<<REFERENCES_START>>');

              // リファレンス情報を解析
              try {
                const referencesJson = referencesPart.trim();
                const references = JSON.parse(referencesJson);
                setMessages(prevMessages => {
                  const updatedMessages = [...prevMessages];
                  const lastIndex = updatedMessages.length - 1;
                  if (updatedMessages[lastIndex].type === 'assistant') {
                    updatedMessages[lastIndex] = {
                      ...updatedMessages[lastIndex],
                      refFileList: references,
                    };
                    (async () => {
                      if (!firstResRef.current) {
                        firstResRef.current = true;
                      }
                    })();
                  }
                  return updatedMessages;
                });
              } catch (e) {
                console.error('リファレンスの解析に失敗しました:', e);
              }

              // バッファをリセット
              buffer = '';
            } else {
              // 通常のメッセージ処理
              if (firstResRef.current) {
                setIsAILoading(false);
                setMessages(prevMessages => [
                  ...prevMessages,
                  {
                    type: 'assistant',
                    text: '',
                  },
                ]);
                firstResRef.current = false;
              }

              // 既存のメッセージ更新処理
              setMessages(prevMessages => {
                const updatedMessages = [...prevMessages];
                const lastIndex = updatedMessages.length - 1;

                if (updatedMessages[lastIndex].type === 'assistant') {
                  updatedMessages[lastIndex] = {
                    ...updatedMessages[lastIndex],
                    text: updatedMessages[lastIndex].text + chunk,
                  };
                }
                return updatedMessages;
              });
            }
          }
        );
        if (error) {
          setIsAILoading(false);
          if (error instanceof Error) {
            setMessages(prevMessages => [
              ...prevMessages,
              {
                type: 'assistant',
                text: error.message,
              },
            ]);
          }
        }
      } catch (error) {
        setIsAILoading(false);
        setMessages(prevMessages => [
          ...prevMessages,
          {
            type: 'assistant',
            text: 'エラーが発生しました。',
          },
        ]);
      } finally {
        setSelectedText('');
      }
    }, [
      selectedText,
      indexType,
      assistantPrompt,
      chatRoomId,
      indexTypeOptions,
      isCustomPromptActive,
      messages,
      selectedModel,
      sendChatroomName,
    ]);

    if (!chatRoomId)
      return (
        <div className="flex items-center justify-center h-screen w-full bg-white">
          <div className="flex flex-col items-center justify-center space-y-4 text-center max-w-md mx-auto px-6">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-2xl flex items-center justify-center mb-2">
              <ChatIcon className="w-8 h-8 text-blue-600" />
            </div>
            <h2 className="text-2xl font-semibold text-gray-900">
              チャットを開始しましょう
            </h2>
            <p className="text-gray-600 leading-relaxed">
              左上のメニューボタンをクリックして新しいチャットを作成するか、既存のチャット履歴から選択してください。
            </p>
          </div>
        </div>
      );

    return (
      <div className="w-full h-full bg-white flex flex-row font-sans relative overflow-hidden">
        {/* チャット部分 */}
        <div
          className="flex flex-col font-sans relative overflow-hidden"
          style={{
            width: selectedFile ? '60%' : '100%',
            height: '100%',
            transition: 'width 0.3s ease-in-out',
          }}
        >
          <div className="flex-1 flex self-stretch flex-col items-center justify-between py-5 gap-2.5">
            <div className="self-stretch flex-1 flex flex-col justify-start overflow-y-auto scrollbar-custom px-4 sm:px-6 md:px-8 lg:px-10">
              {isChatMessageLoading ? (
                <div
                  style={{
                    width: '100%',
                    height: '100%',
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                  }}
                >
                  <CircularProgress />
                </div>
              ) : (
                <div
                  style={{
                    paddingBottom: '30px',
                    maxWidth: '1200px',
                    margin: '0 auto',
                    width: '100%',
                  }}
                >
                  {messages.map((message, index) =>
                    message.type === 'user' ? (
                      <ChatMessage
                        key={index}
                        text={message.text}
                        model={message.model}
                        indexTypes={message.indexTypes}
                      />
                    ) : (
                      <AIComment
                        key={index}
                        message={message}
                        refFileList={message.refFileList}
                        setSelectedFile={setSelectedFile}
                        previousMessage={
                          index > 0 ? messages[index - 1] : undefined
                        }
                      />
                    )
                  )}
                  {isAILoading && <AICommentLoading />}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>
            <div className="w-full px-4 sm:px-6 md:px-8 lg:px-10">
              <MessageBox
                selectedText={selectedText}
                setSelectedText={setSelectedText}
                onSubmit={handleSubmit}
                customPrompt={assistantPrompt}
                setCustomPrompt={setAssistantPrompt}
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
                className="w-full"
              />
            </div>
          </div>
        </div>

        {/* プレビュー部分 */}
        {selectedFile && (
          <div
            style={{
              width: '40%',
              display: 'flex',
              flexDirection: 'column',
              height: '100%',
              borderLeft: '1px solid rgba(0, 0, 0, 0.1)',
              background: '#f5f5f5',
            }}
          >
            <Box
              sx={{
                position: 'relative',
                height: '40px',
                width: '100%',
                display: 'flex',
                justifyContent: 'flex-end',
                padding: '10px',
                background: 'rgba(255, 255, 255, 0.9)',
                backdropFilter: 'blur(8px)',
                borderBottom: '1px solid rgba(0, 0, 0, 0.1)',
                boxSizing: 'border-box',
              }}
            >
              <Tooltip title="ファイルプレビューを閉じる" arrow>
                <button
                  onClick={() => setSelectedFile(null)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    width: '24px',
                    height: '24px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: 0,
                  }}
                >
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </Tooltip>
            </Box>
            <FilePreviewer
              customStyle={{
                width: '100%',
                height: 'calc(100% - 40px)',
              }}
              fileType={selectedFile.fileType}
              url={selectedFile.url}
            />
          </div>
        )}
      </div>
    );
  }
);

export default ChatSection;
