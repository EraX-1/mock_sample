import { ChatModelType } from '@/types/chat';

export const getModelLS = (): ChatModelType | null => {
  if (typeof window === 'undefined') {
    return null;
  }
  const model = localStorage.getItem('rag-chatbot-model');
  return model !== null ? (model as ChatModelType) : null;
};

export const setModelLS = (model: string) => {
  localStorage.setItem('rag-chatbot-model', model);
  return model;
};
