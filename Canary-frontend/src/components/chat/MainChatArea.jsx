// MainChatArea.jsx - Fixed for proper overlay
import { useState } from 'react';
import NewsFeed from './NewsFeed';
import AIToggleButton from './AIToggleButton';
import AIModal from './AIModal';

export default function MainChatArea() {
  const [isAIModalOpen, setIsAIModalOpen] = useState(false);

  const handleToggleAI = () => {
    setIsAIModalOpen(!isAIModalOpen);
  };

  const handleCloseAI = () => {
    setIsAIModalOpen(false);
  };

  return (
    <div className="relative h-screen">
      {/* Main Content Area - News Feed (always rendered) */}
      <NewsFeed />

      {/* AI Toggle Button (always rendered) */}
      <AIToggleButton 
        onClick={handleToggleAI}
        isModalOpen={isAIModalOpen}
      />

      {/* AI Modal Overlay (conditionally rendered on top) */}
      {isAIModalOpen && (
        <AIModal
          isOpen={isAIModalOpen}
          onClose={handleCloseAI}
        />
      )}
    </div>
  );
}