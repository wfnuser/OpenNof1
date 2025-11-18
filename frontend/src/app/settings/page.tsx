"use client";

import React, { useState, useEffect } from "react";
import { Save, RotateCcw, Settings, Power, Play, Square } from "lucide-react";
import {
  fetchTradingStrategy,
  updateTradingStrategy,
  resetTradingStrategy,
  fetchAgentStatus,
  startAgent,
  stopAgent,
} from "@/lib/api";
import type { AgentStatus } from "@/lib/api";
import Toast from "@/components/Toast";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";

export default function SettingsPage() {
  const [strategy, setStrategy] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Bot status
  const [botStatus, setBotStatus] = useState<AgentStatus>({
    is_running: false,
    decision_interval: 0,
    symbols: [],
    timeframes: [],
    model_name: "",
    last_run: null,
    next_run: null,
    uptime_seconds: null,
  });
  const [botLoading, setBotLoading] = useState(false);

  // Load current strategy and bot status
  useEffect(() => {
    loadStrategy();
    loadBotStatus();
  }, []);

  const loadStrategy = async () => {
    try {
      setLoading(true);
      const data = await fetchTradingStrategy();
      setStrategy(data.strategy);
    } catch (error) {
      setMessage({ type: "error", text: "Failed to load trading strategy" });
    } finally {
      setLoading(false);
    }
  };

  const loadBotStatus = async () => {
    try {
      const status = await fetchAgentStatus();
      setBotStatus(status);
    } catch (error) {
      console.error("Failed to load bot status:", error);
    }
  };

  const handleBotToggle = async () => {
    try {
      setBotLoading(true);
      setMessage(null);

      const actionResponse = botStatus.is_running
        ? await stopAgent()
        : await startAgent();

      setMessage({
        type: "success",
        text: actionResponse.message,
      });

      await loadBotStatus(); // Reload status
    } catch (error) {
      const fallbackMessage = `Failed to ${
        botStatus.is_running ? "stop" : "start"
      } trading bot`;
      setMessage({
        type: "error",
        text: error instanceof Error ? error.message : fallbackMessage,
      });
    } finally {
      setBotLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setMessage(null);

      await updateTradingStrategy(strategy);

      setMessage({
        type: "success",
        text: "Trading strategy updated successfully",
      });
    } catch (error) {
      setMessage({
        type: "error",
        text:
          error instanceof Error
            ? error.message
            : "Failed to update trading strategy",
      });
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

      setMessage({
        type: "success",
        text: "Trading strategy reset to default",
      });
    } catch (error) {
      setMessage({
        type: "error",
        text:
          error instanceof Error
            ? error.message
            : "Failed to reset trading strategy",
      });
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
          <div className="max-w-4xl mx-auto space-y-6">
            {/* Bot Control Section */}
            <div className="border-2 border-black bg-white">
              {/* Section Header */}
              <div className="border-b-2 border-black bg-gray-50 px-4 py-3">
                <h2 className="text-lg font-bold uppercase tracking-wider">
                  Trading Bot Control
                </h2>
              </div>

              {/* Bot Control */}
              <div className="p-4 md:p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                      <Power
                        className={
                          botStatus.is_running
                            ? "text-green-600"
                            : "text-red-600"
                        }
                      />
                      <span className="font-medium">
                        Trading Bot Status:
                        <span
                          className={`ml-2 font-bold ${
                            botStatus.is_running
                              ? "text-green-600"
                              : "text-red-600"
                          }`}
                        >
                          {botStatus.is_running ? "RUNNING" : "STOPPED"}
                        </span>
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={handleBotToggle}
                    disabled={botLoading}
                    className={`flex items-center justify-center space-x-2 px-4 py-2 font-bold uppercase tracking-wide text-sm border-2 border-black transition-colors duration-200 ${
                      botStatus.is_running
                        ? "bg-red-600 hover:bg-red-700 text-white"
                        : "bg-blue-600 hover:bg-blue-700 text-white"
                    } disabled:bg-gray-400 disabled:cursor-not-allowed disabled:text-gray-200`}
                  >
                    {botLoading ? (
                      <>
                        <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                        <span>
                          {botStatus.is_running ? "STOPPING..." : "STARTING..."}
                        </span>
                      </>
                    ) : (
                      <>
                        {botStatus.is_running ? (
                          <Square size={16} />
                        ) : (
                          <Play size={16} />
                        )}
                        <span>
                          {botStatus.is_running ? "STOP BOT" : "START BOT"}
                        </span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Trading Strategy Section */}
            <div className="border-2 border-black bg-white">
              {/* Section Header */}
              <div className="border-b-2 border-black bg-gray-50 px-4 py-3">
                <h2 className="text-lg font-bold uppercase tracking-wider">
                  Trading Strategy Configuration
                </h2>
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
