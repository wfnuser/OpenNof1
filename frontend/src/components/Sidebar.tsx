'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Menu, X, BarChart3, Settings } from 'lucide-react';

interface SidebarProps {
  className?: string;
  onToggle?: () => void;
  isOpen?: boolean;
}

const navigation = [
  {
    name: 'Dashboard',
    href: '/',
    icon: BarChart3,
  },
  {
    name: 'Settings',
    href: '/settings',
    icon: Settings,
  },
];

export default function Sidebar({ className = '', onToggle, isOpen: externalIsOpen }: SidebarProps) {
  const [internalIsOpen, setInternalIsOpen] = useState(false);
  const pathname = usePathname();

  const isOpen = externalIsOpen !== undefined ? externalIsOpen : internalIsOpen;
  const toggleSidebar = () => {
    if (onToggle) {
      onToggle();
    } else {
      setInternalIsOpen(!internalIsOpen);
    }
  };

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-20 bg-black bg-opacity-50 lg:hidden"
          onClick={toggleSidebar}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed left-0 top-0 z-50 h-full w-64 transform bg-white border-r-2 border-black font-mono transition-transform duration-300 ease-in-out lg:relative lg:self-stretch lg:h-full lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        } ${className}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b-2 border-black px-4 md:px-6 py-3 md:py-4">
          <h2 className="text-lg md:text-xl font-bold uppercase tracking-wider">OpenNof1</h2>
          <button
            onClick={toggleSidebar}
            className="lg:hidden p-1 hover:bg-gray-100 transition-colors"
          >
            <X size={16} />
          </button>
        </div>

        {/* Navigation */}
        <nav>
          <ul>
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              
              return (
                <li key={item.name}>
                  <Link
                    href={item.href}
                    onClick={toggleSidebar}
                    className={`flex items-center space-x-3 px-4 md:px-6 py-3 text-sm font-medium transition-colors duration-200 ${
                      isActive
                        ? 'bg-black text-white'
                        : 'bg-white text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <Icon size={16} />
                    <span className="uppercase tracking-wide">{item.name}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </div>

    </>
  );
}
