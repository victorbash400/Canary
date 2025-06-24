import React, { useState, useEffect, useRef, useCallback } from 'react';
import PropTypes from 'prop-types';
import { motion, AnimatePresence } from 'framer-motion';
import { X, MessageSquare, Plus, BrainCircuit, Loader, Sparkles } from 'lucide-react';

import {
  getChatById,
  saveMessage,
  createNewChat,
  getAllChats,
  getAIMemory,
} from '../../services/MainChatArea-api';
import ChatInput from './ChatInput';
import ChatBubble from './ChatBubble';

export default function AIModalV2({ isOpen, onClose }) {
  const Sidebar = ({ chats, currentChatId, onSelectChat, onCreateNew, loading }) => (
    <div className="w-56 bg-gradient-to-b from-black/15 via-black/25 to-black/35 h-full flex flex-col backdrop-blur-xl">
      <div className="p-3 flex justify-between items-center shrink-0">
        <h2 className="font-medium text-white text-sm">Chats</h2>
        <button
          onClick={onCreateNew}
          className="p-1.5 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition-all duration-200 hover:scale-105 active:scale-95 group"
          title="New Chat"
        >
          <Plus className="w-4 h-4 group-hover:rotate-90 transition-transform duration-200" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 py-1 space-y-1 custom-scrollbar">
        {loading && (
          <div className="flex items-center justify-center p-6 text-gray-500">
            <Loader className="w-4 h-4 animate-spin mr-2" />
            <span className="text-xs">Loading...</span>
          </div>
        )}

        {!loading && chats.length === 0 && (
          <div className="text-center p-4 text-gray-500">
            <MessageSquare className="w-6 h-6 mx-auto mb-2 opacity-50" />
            <p className="text-xs">No conversations</p>
            <p className="text-xs mt-1 opacity-70">Click '+' to start</p>
          </div>
        )}

        {!loading && chats.map(chat => (
          <motion.button
            key={chat.chatId}
            onClick={() => onSelectChat(chat.chatId)}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className={`w-full text-left p-2.5 rounded-lg transition-all duration-200 text-sm truncate group ${
              currentChatId === chat.chatId
                ? 'bg-gradient-to-r from-yellow-400/15 to-yellow-500/15 text-yellow-200 shadow-md'
                : 'text-gray-400 hover:bg-white/5 hover:text-gray-200'
            }`}
          >
            <div className="flex items-center gap-2">
              <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                currentChatId === chat.chatId ? 'bg-yellow-400' : 'bg-gray-600 group-hover:bg-gray-500'
              }`} />
              <span className="truncate">{chat.title || 'New conversation'}</span>
            </div>
          </motion.button>
        ))}
      </div>
    </div>
  );

  const ChatPanel = ({ messages, onSendMessage, loading, isNewChat }) => {
    const messagesEndRef = useRef(null);
    useEffect(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
      <div className="relative flex-1 flex flex-col h-full bg-gradient-to-b from-black/5 to-black/15">
        <div className="flex-1 overflow-y-auto px-6 py-4 custom-scrollbar pb-24">
          {loading && (
            <div className="flex justify-center items-center h-full text-gray-400">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              >
                <Loader className="w-6 h-6" />
              </motion.div>
            </div>
          )}

          {!loading && messages.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="flex flex-col justify-center items-center h-full text-center"
            >
              <div className="relative mb-6">
                <div className="absolute inset-0 bg-yellow-400/15 blur-2xl rounded-full" />
                <div className="relative bg-gradient-to-br from-yellow-400/15 to-yellow-500/15 p-6 rounded-2xl">
                  <Sparkles className="w-8 h-8 text-yellow-400" />
                </div>
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Canary AI</h3>
              <p className="text-sm text-gray-400 max-w-xs leading-relaxed">
                {isNewChat ?
                  "Ready to help! Ask me anything or let me know what you'd like to monitor." :
                  "Continue our conversation or start fresh with a new topic."
                }
              </p>
            </motion.div>
          )}

          {!loading && messages.length > 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.4 }}
            >
              {messages.map(msg => (
                <ChatBubble
                  key={msg.id}
                  message={msg.content}
                  isUser={msg.role === 'user'}
                  timestamp={msg.timestamp}
                  imageData={msg.image_data}
                  messageType={msg.message_type}
                  imageFilename={msg.image_filename}
                />
              ))}
              <div ref={messagesEndRef} />
            </motion.div>
          )}
        </div>

        <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-black/80 to-transparent">
          <ChatInput
            onSendMessage={onSendMessage}
            onImageUpload={() => {}}
            hasMessages={messages.length > 0}
            disabled={false}
          />
        </div>
      </div>
    );
  };

  const MemoryPanel = ({ aiMemory, loading }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.4 }}
      className="p-8 overflow-y-auto custom-scrollbar w-full bg-gradient-to-b from-black/5 to-black/15"
    >
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center gap-3 mb-8">
          <div className="p-2 bg-gradient-to-br from-yellow-400/15 to-yellow-500/15 rounded-xl">
            <BrainCircuit className="w-5 h-5 text-yellow-400" />
          </div>
          <h2 className="text-xl font-semibold text-white">AI Memory</h2>
        </div>

        {loading ? (
          <div className="flex justify-center items-center h-48 text-gray-400">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            >
              <Loader className="w-6 h-6 mr-3" />
            </motion.div>
            <span>Loading memory...</span>
          </div>
        ) : aiMemory ? (
          <motion.div
            className="space-y-6"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            <div className="bg-gradient-to-br from-black/15 to-black/25 rounded-2xl p-6 backdrop-blur-sm">
              <h3 className="text-xs text-yellow-400 uppercase tracking-wider font-semibold mb-4 flex items-center gap-2">
                <div className="w-1 h-4 bg-yellow-400 rounded-full" />
                Personalization Summary
              </h3>
              <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-line">
                {aiMemory.summary || 'No summary yet. Keep chatting to build my understanding of your preferences and needs.'}
              </p>
            </div>

            {aiMemory.active_monitoring?.length > 0 && (
              <div className="bg-gradient-to-br from-black/15 to-black/25 rounded-2xl p-6 backdrop-blur-sm">
                <h3 className="text-xs text-yellow-400 uppercase tracking-wider font-semibold mb-4 flex items-center gap-2">
                  <div className="w-1 h-4 bg-yellow-400 rounded-full" />
                  Actively Monitoring
                </h3>
                <div className="flex flex-wrap gap-2">
                  {aiMemory.active_monitoring.map((topic, idx) => (
                    <motion.span
                      key={idx}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: idx * 0.1 }}
                      className="bg-gradient-to-r from-gray-700/40 to-gray-600/40 text-gray-300 text-xs px-3 py-2 rounded-full backdrop-blur-sm"
                    >
                      {topic}
                    </motion.span>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        ) : (
          <div className="text-center p-8 text-gray-500">
            <BrainCircuit className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p className="text-sm">No memory data available yet.</p>
            <p className="text-xs mt-2 text-gray-600">Start chatting to build AI memory.</p>
          </div>
        )}
      </div>
    </motion.div>
  );

  // Core Logic
  const [activeView, setActiveView] = useState('chat');
  const [chats, setChats] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [aiMemory, setAiMemory] = useState(null);
  const [loading, setLoading] = useState({ chats: false, messages: false, memory: false });
  const [isNewChat, setIsNewChat] = useState(true);

  const loadAllChats = useCallback(async () => {
    setLoading(prev => ({ ...prev, chats: true }));
    try {
      const chatList = await getAllChats();
      setChats(chatList);

      if (chatList.length > 0) {
        setCurrentChatId(chatList[0].chatId);
        setIsNewChat(false);
      } else {
        setCurrentChatId(null);
        setIsNewChat(true);
      }
    } catch (err) {
      console.error('Error loading chats:', err);
    } finally {
      setLoading(prev => ({ ...prev, chats: false }));
    }
  }, []);

  const loadAIMemory = useCallback(async () => {
    setLoading(prev => ({ ...prev, memory: true }));
    try {
      const memory = await getAIMemory();
      setAiMemory(memory);
    } catch (err) {
      console.error('Error loading AI memory:', err);
    } finally {
      setLoading(prev => ({ ...prev, memory: false }));
    }
  }, []);

  useEffect(() => {
    const escHandler = (e) => e.key === 'Escape' && onClose();
    if (isOpen) {
      document.addEventListener('keydown', escHandler);
      loadAllChats();
      loadAIMemory();
      setActiveView('chat');
    }
    return () => document.removeEventListener('keydown', escHandler);
  }, [isOpen, onClose, loadAllChats, loadAIMemory]);

  useEffect(() => {
    if (currentChatId && isOpen) {
      const loadChat = async () => {
        setLoading(prev => ({ ...prev, messages: true }));
        try {
          const chat = await getChatById(currentChatId);
          setMessages(chat.messages || []);
          setIsNewChat(chat.messages?.length === 0);
        } catch (err) {
          console.error('Chat error:', err);
          setMessages([]);
          setIsNewChat(true);
        } finally {
          setLoading(prev => ({ ...prev, messages: false }));
        }
      };
      loadChat();
    } else {
      setMessages([]);
      setIsNewChat(true);
    }
  }, [currentChatId, isOpen]);

  const handleCreateNewChat = async () => {
    setLoading(prev => ({ ...prev, messages: true }));
    try {
      const newChat = await createNewChat();
      setChats(prev => [newChat, ...prev.filter(chat => chat.chatId !== newChat.chatId)]);
      setCurrentChatId(newChat.chatId);
      setMessages([]);
      setIsNewChat(true);
      setActiveView('chat');
      return newChat.chatId;
    } catch (err) {
      console.error('New chat error:', err);
      return null;
    } finally {
      setLoading(prev => ({ ...prev, messages: false }));
    }
  };

  const handleSendMessage = async (text) => {
    let chatId = currentChatId;
    if (!chatId) {
      const newChatId = await handleCreateNewChat();
      if (!newChatId) return;
      chatId = newChatId;
    }

    const userMessage = {
      id: Date.now().toString(),
      content: text,
      role: 'user',
      timestamp: new Date().toISOString(),
      message_type: 'text',
    };

    setMessages(prev => [...prev, userMessage]);
    setIsNewChat(false);

    try {
      const aiResponse = await saveMessage(chatId, text);
      if (aiResponse) {
        setMessages(prev => [...prev, aiResponse]);
        loadAIMemory();
      }
    } catch (err) {
      console.error('Message error:', err);
      setMessages(prev => prev.filter(msg => msg.id !== userMessage.id));
    }
  };

  if (!isOpen) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 50, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 30, scale: 0.95 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      className="fixed z-50 bottom-6 right-6 w-[52rem] max-w-[92vw] h-[88vh] rounded-3xl shadow-2xl border border-white/10 flex flex-col overflow-hidden text-white"
      style={{
        background: 'linear-gradient(135deg, rgba(24,24,28,0.95) 0%, rgba(16,16,20,0.95) 100%)',
        backdropFilter: 'blur(40px)',
        WebkitBackdropFilter: 'blur(40px)',
      }}
    >
      {/* Header */}
      <div className="p-4 flex items-center justify-between shrink-0 bg-gradient-to-r from-black/15 to-black/25">
        <div className="flex items-center gap-1">
          <motion.button
            onClick={() => setActiveView('chat')}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className={`px-4 py-2 flex items-center gap-2 rounded-xl text-sm font-medium transition-all duration-200 ${
              activeView === 'chat'
                ? 'bg-gradient-to-r from-white/10 to-white/5 text-white shadow-md'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <MessageSquare className="w-4 h-4" />
            Chat
          </motion.button>
          <motion.button
            onClick={() => setActiveView('memory')}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className={`px-4 py-2 flex items-center gap-2 rounded-xl text-sm font-medium transition-all duration-200 ${
              activeView === 'memory'
                ? 'bg-gradient-to-r from-white/10 to-white/5 text-white shadow-md'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <BrainCircuit className="w-4 h-4" />
            Memory
          </motion.button>
        </div>
        <motion.button
          onClick={onClose}
          whileHover={{ scale: 1.1, rotate: 90 }}
          whileTap={{ scale: 0.9 }}
          className="p-2 rounded-xl hover:bg-white/10 text-gray-400 hover:text-white transition-all duration-200"
        >
          <X className="w-5 h-5" />
        </motion.button>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        <AnimatePresence mode="wait">
          {activeView === 'chat' ? (
            <motion.div
              key="chat-view"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
              className="flex w-full h-full"
            >
              <Sidebar
                chats={chats}
                currentChatId={currentChatId}
                onSelectChat={(chatId) => {
                  setCurrentChatId(chatId);
                  const selectedChat = chats.find(chat => chat.chatId === chatId);
                  setIsNewChat(selectedChat?.messages?.length === 0);
                }}
                onCreateNew={handleCreateNewChat}
                loading={loading.chats}
              />
              <ChatPanel
                messages={messages}
                onSendMessage={handleSendMessage}
                loading={loading.messages}
                isNewChat={isNewChat}
              />
            </motion.div>
          ) : (
            <motion.div
              key="memory-view"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
              className="w-full h-full"
            >
              <MemoryPanel aiMemory={aiMemory} loading={loading.memory} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 2px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.2);
        }
      `}</style>
    </motion.div>
  );
}

AIModalV2.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
};