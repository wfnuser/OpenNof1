'use client';

import React from 'react';
import { Twitter, Github } from 'lucide-react';
import MobileMenuButton from './MobileMenuButton';

interface HeaderProps {
  title: string;
  showMobileTitle?: boolean;
  onMenuToggle: () => void;
}

export default function Header({ 
  title, 
  showMobileTitle = false, 
  onMenuToggle
}: HeaderProps) {
  return (
    <header className="bg-white border-b-2 border-black px-4 md:px-6 py-3 md:py-4 flex-shrink-0">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2 md:space-x-4">
          <MobileMenuButton onClick={onMenuToggle} />
          {showMobileTitle && (
            <h1 className="text-lg md:text-xl font-bold uppercase tracking-wider lg:hidden">
              {title}
            </h1>
          )}
          {!showMobileTitle && (
            <h1 className="text-lg md:text-xl font-bold uppercase tracking-wider">
              {title}
            </h1>
          )}
        </div>
        
        <div className="flex items-center space-x-2 md:space-x-3">
          <div className="flex items-center space-x-1">
            <a 
              href="https://twitter.com/intent/follow?screen_name=weiraolilun" 
              target="_blank" 
              rel="noopener noreferrer"
              className="flex items-center justify-center w-7 h-7 md:w-7 md:h-7 hover:bg-gray-100 rounded-full transition-colors duration-200"
              title="Tend to follow"
            >
              <Twitter size={16} className="md:w-[18px] md:h-[18px] text-gray-700 hover:text-black" />
            </a>
            <a 
              href="https://github.com/wfnuser/OpenNof1" 
              target="_blank" 
              rel="noopener noreferrer"
              className="flex items-center justify-center w-7 h-7 md:w-7 md:h-7 hover:bg-gray-100 rounded-full transition-colors duration-200"
              title="View GitHub profile"
            >
              <Github size={16} className="md:w-[18px] md:h-[18px] text-gray-700 hover:text-black" />
            </a>
          </div>
        </div>
      </div>
    </header>
  );
}