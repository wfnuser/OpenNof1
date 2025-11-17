'use client';

import React from 'react';
import { Menu } from 'lucide-react';

interface MobileMenuButtonProps {
  onClick: () => void;
}

export default function MobileMenuButton({ onClick }: MobileMenuButtonProps) {
  return (
    <button
      onClick={onClick}
      className="lg:hidden flex items-center justify-center w-7 h-7 md:w-8 md:h-8 hover:bg-gray-100 transition-colors duration-200 border border-gray-300"
      aria-label="Open navigation"
    >
      <Menu size={16} />
    </button>
  );
}