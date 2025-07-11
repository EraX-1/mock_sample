'use client';

import type { NextPage } from 'next';
import { getAuthUrlApi, getAdminAuthUrlApi } from '@/services/apiService';
import Image from 'next/image';

const Frame: NextPage = () => {
  const handleMicrosoftLogin = async () => {
    const { response } = await getAuthUrlApi();
    if (response?.auth_url) {
      window.location.href = response.auth_url;
    }
  };

  const handleAdminLogin = async () => {
    const { response } = await getAdminAuthUrlApi();
    if (response?.auth_url) {
      window.location.href = response.auth_url;
    }
  };


  return (
    <div className="relative flex items-center justify-center min-h-screen overflow-hidden">
      {/* 静的グラデーション背景 */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
        <div
          className="absolute inset-0 opacity-30"
          style={{
            background: `
              radial-gradient(circle at 20% 50%, rgba(59, 130, 246, 0.3) 0%, transparent 50%),
              radial-gradient(circle at 80% 20%, rgba(139, 92, 246, 0.3) 0%, transparent 50%),
              radial-gradient(circle at 40% 80%, rgba(236, 72, 153, 0.2) 0%, transparent 50%)
            `,
          }}
        />
        <div
          className="absolute inset-0 opacity-20"
          style={{
            background: `
              radial-gradient(circle at 60% 30%, rgba(16, 185, 129, 0.2) 0%, transparent 50%),
              radial-gradient(circle at 90% 70%, rgba(245, 158, 11, 0.2) 0%, transparent 50%),
              radial-gradient(circle at 10% 90%, rgba(99, 102, 241, 0.2) 0%, transparent 50%)
            `,
          }}
        />
      </div>

      {/* メインコンテンツ */}
      <div className="relative z-10 p-8 space-y-6 bg-white/80 backdrop-blur-md rounded-2xl shadow-xl border border-white/20">
        <h2 className="text-xl font-bold text-center mb-8">
          湯山製作所 RAGチャットボット
        </h2>
        <div className="w-[320px] space-y-4">
          <button
            onClick={handleMicrosoftLogin}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-[#2F2F2F] text-white rounded hover:bg-[#404040] transition-colors"
          >
            <Image
              src="/ms-symbollockup_mssymbol_19.png"
              alt="Microsoft logo"
              width={24}
              height={24}
              className="w-6 h-6"
            />
            <span>Microsoftアカウントでログイン</span>
          </button>

          <button
            onClick={handleAdminLogin}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors border-2 border-red-300"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            <span>管理者としてログイン</span>
          </button>

        </div>
      </div>
    </div>
  );
};

export default Frame;
