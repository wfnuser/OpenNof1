'use client';

import React, { useState, useEffect } from 'react';
import { Save, RotateCcw, Settings } from 'lucide-react';
import { fetchTradingStrategy, updateTradingStrategy, resetTradingStrategy } from '@/lib/api';
import Toast from '@/components/Toast';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';

export default function SettingsPage() {
  const [strategy, setStrategy] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Load current strategy
  useEffect(() => {
    loadStrategy();
  }, []);

  const loadStrategy = async () => {
    try {
      setLoading(true);
      const data = await fetchTradingStrategy();
      setStrategy(data.strategy);
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load trading strategy' });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setMessage(null);
      
      await updateTradingStrategy(strategy);
      
      setMessage({ type: 'success', text: 'Trading strategy updated successfully' });
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to update trading strategy' });
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    try {
      setResetting(true);
      setMessage(null);
      
      await resetTradingStrategy();
      await loadStrategy(); // Reload to get default strategy
      
      setMessage({ type: 'success', text: 'Trading strategy reset to default' });
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to reset trading strategy' });
    } finally {
      setResetting(false);
    }
  };


  if (loading) {
    return (
      <div className="min-h-screen bg-white font-mono flex items-center justify-center">
        <div className="text-center">
          <Settings className="w-8 h-8 animate-spin mx-auto mb-2" />
          <div className="text-sm">LOADING SETTINGS...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-white font-mono flex">
      {/* Sidebar */}
      <Sidebar 
        className="hidden lg:block" 
        isOpen={sidebarOpen} 
        onToggle={() => setSidebarOpen(!sidebarOpen)} 
      />
      
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <Header 
          title="SYSTEM SETTINGS"
          onMenuToggle={() => setSidebarOpen(!sidebarOpen)}
        />

        {/* Mobile Sidebar */}
        <Sidebar 
          className="lg:hidden" 
          isOpen={sidebarOpen} 
          onToggle={() => setSidebarOpen(!sidebarOpen)} 
        />

        {/* Main Content */}
      <div className="flex-1 p-4 md:p-6">
        <div className="max-w-4xl mx-auto">
          {/* Trading Strategy Section */}
          <div className="border-2 border-black bg-white">
            {/* Section Header */}
            <div className="border-b-2 border-black bg-gray-50 px-4 py-3">
              <h2 className="text-lg font-bold uppercase tracking-wider">Trading Strategy Configuration</h2>
              <p className="text-sm text-gray-600 mt-1">
                Configure AI trading behavior and risk management rules
              </p>
            </div>

            {/* Strategy Editor */}
            <div className="p-4 md:p-6">
              <div className="mb-4">
                <label className="block text-sm font-bold uppercase tracking-wide text-gray-700 mb-2">
                  Trading Strategy Rules
                </label>
                <textarea
                  value={strategy}
                  onChange={(e) => setStrategy(e.target.value)}
                  className="w-full h-64 px-3 py-2 border-2 border-black font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter your trading strategy configuration..."
                />
              </div>

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-3">
                <button
                  onClick={handleSave}
                  disabled={saving || !strategy.trim()}
                  className="flex items-center justify-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-bold uppercase tracking-wide text-sm border-2 border-black transition-colors duration-200"
                >
                  {saving ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>SAVING...</span>
                    </>
                  ) : (
                    <>
                      <Save size={16} />
                      <span>SAVE STRATEGY</span>
                    </>
                  )}
                </button>

                <button
                  onClick={handleReset}
                  disabled={resetting}
                  className="flex items-center justify-center space-x-2 px-4 py-2 bg-gray-600 hover:bg-gray-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-bold uppercase tracking-wide text-sm border-2 border-black transition-colors duration-200"
                >
                  {resetting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>RESETTING...</span>
                    </>
                  ) : (
                    <>
                      <RotateCcw size={16} />
                      <span>RESET TO DEFAULT</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

        </div>
        </div>
      
        {/* Toast Notification */}
        {message && (
          <Toast
            message={message.text}
            type={message.type}
            onClose={() => setMessage(null)}
          />
        )}
      </div>
    </div>
  );
}