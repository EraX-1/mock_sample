'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';
import ModernNavigation from './modern-navigation';
import NavigationTrigger from './navigation-trigger';

interface NavigationContextType {
  isOpen: boolean;
  openNavigation: () => void;
  closeNavigation: () => void;
  toggleNavigation: () => void;
}

const NavigationContext = createContext<NavigationContextType | undefined>(
  undefined
);

export const useNavigation = () => {
  const context = useContext(NavigationContext);
  if (!context) {
    throw new Error('useNavigation must be used within a NavigationProvider');
  }
  return context;
};

interface NavigationProviderProps {
  children: ReactNode;
  showTrigger?: boolean;
  triggerVariant?: 'search' | 'menu';
}

export const NavigationProvider: React.FC<NavigationProviderProps> = ({
  children,
  showTrigger = true,
  triggerVariant = 'search',
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const openNavigation = () => setIsOpen(true);
  const closeNavigation = () => setIsOpen(false);
  const toggleNavigation = () => setIsOpen(!isOpen);

  const contextValue: NavigationContextType = {
    isOpen,
    openNavigation,
    closeNavigation,
    toggleNavigation,
  };

  return (
    <NavigationContext.Provider value={contextValue}>
      {children}

      {/* トリガーボタン */}
      {showTrigger && (
        <NavigationTrigger onClick={openNavigation} variant={triggerVariant} />
      )}

      {/* モダンナビゲーション */}
      <ModernNavigation isOpen={isOpen} onClose={closeNavigation} />
    </NavigationContext.Provider>
  );
};

export default NavigationProvider;
