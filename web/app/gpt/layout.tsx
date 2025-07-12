'use client';

import SidebarProvider from '@/components/navigation/sidebar-provider';

export default function GPTLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <SidebarProvider>
      <div className="w-full h-full bg-white">
        {children}
      </div>
    </SidebarProvider>
  );
}