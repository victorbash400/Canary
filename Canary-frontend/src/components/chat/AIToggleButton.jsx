import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { MessageCircle, X } from 'lucide-react';

export default function AIToggleButton({ onClick, isModalOpen }) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div className="fixed bottom-6 right-6 z-40">
      <div className="relative">
        {/* Tooltip */}
        {isHovered && !isModalOpen && (
          <div className="absolute right-full mr-3 bottom-1/2 translate-y-1/2 bg-[#1e1f23] text-[#fefce8] text-sm px-3 py-1.5 rounded-md shadow-md whitespace-nowrap border border-[#2d2d2d]">
            Talk to Canary AI
          </div>
        )}

        {/* Button */}
        <button
          onClick={onClick}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
          className={`
            w-12 h-12 rounded-full shadow-md transition-all duration-200
            flex items-center justify-center
            ${
              isModalOpen
                ? 'bg-red-500 hover:bg-red-600 text-white'
                : 'bg-[#111111] hover:bg-[#1e1f23] text-[#facc15] border border-[#2d2d2d]'
            }
          `}
        >
          {isModalOpen ? (
            <X className="w-5 h-5" />
          ) : (
            <MessageCircle className="w-5 h-5" />
          )}
        </button>
      </div>
    </div>
  );
}

AIToggleButton.propTypes = {
  onClick: PropTypes.func.isRequired,
  isModalOpen: PropTypes.bool.isRequired
};