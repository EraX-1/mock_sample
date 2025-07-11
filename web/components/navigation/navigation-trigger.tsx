'use client';

import React, { useEffect } from 'react';
import { Tooltip } from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import MenuIcon from '@mui/icons-material/Menu';

interface NavigationTriggerProps {
  onClick: () => void;
  variant?: 'search' | 'menu';
  className?: string;
}

const NavigationTrigger: React.FC<NavigationTriggerProps> = ({
  onClick,
  variant = 'search',
  className = '',
}) => {
  // キーボードショートカット (Cmd+K / Ctrl+K)
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
        event.preventDefault();
        onClick();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClick]);

  const baseClasses = `
    fixed top-5 left-5 z-[1001] w-12 h-12 rounded-2xl
    backdrop-blur-md bg-white/80 hover:bg-white/90
    border border-gray-200/50 hover:border-gray-300/80
    shadow-lg hover:shadow-xl
    flex items-center justify-center
    transition-all duration-300 ease-out
    hover:scale-105 active:scale-95
    group cursor-pointer
    ${className}
  `;

  const searchClasses = `
    ${baseClasses}
    bg-gradient-to-br from-blue-50/80 to-indigo-50/80
    hover:from-blue-100/90 hover:to-indigo-100/90
    border-blue-200/50 hover:border-blue-300/80
  `;

  const menuClasses = `
    ${baseClasses}
    bg-gradient-to-br from-gray-50/80 to-slate-50/80
    hover:from-gray-100/90 hover:to-slate-100/90
  `;

  return (
    <Tooltip
      title={variant === 'search' ? 'ナビゲーション (⌘K)' : 'メニューを開く'}
      placement="right"
    >
      <button
        onClick={onClick}
        className={variant === 'search' ? searchClasses : menuClasses}
        aria-label={
          variant === 'search' ? 'ナビゲーションを開く' : 'メニューを開く'
        }
      >
        {variant === 'search' ? (
          <SearchIcon className="w-5 h-5 text-blue-700 transition-transform duration-300 group-hover:scale-110" />
        ) : (
          <MenuIcon className="w-5 h-5 text-gray-700 transition-transform duration-300 group-hover:scale-110" />
        )}
      </button>
    </Tooltip>
  );
};

export default NavigationTrigger;
