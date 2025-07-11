'use client';

import React, {
  createContext,
  ReactNode,
  useContext,
  useEffect,
  useState,
} from 'react';
import ModernSidebar from './modern-sidebar';

interface SidebarContextType {
  isOpen: boolean;
  openSidebar: () => void;
  closeSidebar: () => void;
  toggleSidebar: () => void;
  isMobile: boolean;
}

const SidebarContext = createContext<SidebarContextType | undefined>(undefined);

export const useSidebar = () => {
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error('useSidebar must be used within a SidebarProvider');
  }
  return context;
};

interface SidebarProviderProps {
  children: ReactNode;
}

export const SidebarProvider: React.FC<SidebarProviderProps> = ({
  children,
}) => {
  const [isOpen, setIsOpen] = useState(true);
  const [isMobile, setIsMobile] = useState(false);
  const [initialized, setInitialized] = useState(false);

  // レスポンシブ検知
  useEffect(() => {
    const checkScreenSize = () => {
      try {
        const isMobileSize = window.innerWidth < 1024; // lg ブレークポイント

        setIsMobile(prevIsMobile => {
          // モバイル状態が変わった時のみ処理
          if (prevIsMobile !== isMobileSize) {
            // 初回読み込み時または手動で変更されていない場合
            if (
              !initialized ||
              !window.sessionStorage?.getItem('sidebarToggled')
            ) {
              // デスクトップではデフォルト表示、モバイルでは非表示（仕様に従い）
              setTimeout(() => setIsOpen(!isMobileSize), 0);
            }
          }
          return isMobileSize;
        });

        if (!initialized) {
          setInitialized(true);
        }
      } catch (error) {
        console.warn('Error in checkScreenSize:', error);
      }
    };

    // 初回実行
    checkScreenSize();

    // リサイズリスナー追加
    window.addEventListener('resize', checkScreenSize);

    return () => {
      window.removeEventListener('resize', checkScreenSize);
    };
  }, [initialized]);

  const openSidebar = () => {
    setIsOpen(true);
    try {
      window.sessionStorage?.setItem('sidebarToggled', 'true');
    } catch (error) {
      console.warn('sessionStorage not available:', error);
    }
  };

  const closeSidebar = () => {
    setIsOpen(false);
    try {
      window.sessionStorage?.setItem('sidebarToggled', 'true');
    } catch (error) {
      console.warn('sessionStorage not available:', error);
    }
  };

  const toggleSidebar = () => {
    setIsOpen(!isOpen);
    try {
      window.sessionStorage?.setItem('sidebarToggled', 'true');
    } catch (error) {
      console.warn('sessionStorage not available:', error);
    }
  };

  const contextValue: SidebarContextType = {
    isOpen,
    openSidebar,
    closeSidebar,
    toggleSidebar,
    isMobile,
  };

  const mainContentClasses = `
    flex flex-col overflow-hidden
    transition-all duration-300 ease-out
    ${isMobile
      ? 'flex-1'
      : isOpen
        ? 'flex-1'
        : 'flex-1'
    }
  `.trim().replace(/\s+/g, ' ');

  return (
    <SidebarContext.Provider value={contextValue}>
      <div className="flex h-screen bg-gray-50">
        {/* サイドバー */}
        <ModernSidebar />

        {/* メインコンテンツ */}
        <main className={mainContentClasses}>
          {children}
        </main>
      </div>
    </SidebarContext.Provider>
  );
};

export default SidebarProvider;
