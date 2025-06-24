import React, { useState, useEffect, useRef } from 'react';
import { ArrowUp } from 'lucide-react';
import PropTypes from 'prop-types';

function ChatInput({ onSendMessage, onImageUpload, hasMessages, disabled }) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      const maxHeight = parseInt(textareaRef.current.style.maxHeight || '120', 10);
      textareaRef.current.style.height = `${Math.min(scrollHeight, maxHeight)}px`;
    }
  }, [message]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className={`w-full ${hasMessages ? 'pb-2 sm:pb-3' : 'pb-6 sm:pb-8'}`}>
      <div className="max-w-2xl mx-auto px-3 sm:px-0">
        <div className="relative">
          <div className="relative bg-[#1e1f23] rounded-3xl shadow-xl border border-[#2d2d2d]">
            <div className="flex items-center py-2 px-3 gap-2">
              <div className="flex-1">
                <textarea
                  ref={textareaRef}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={disabled}
                  placeholder="Send a message..."
                  className="w-full px-1 py-1 bg-transparent border-0 resize-none focus:outline-none text-[#fefce8] placeholder-gray-400 text-base font-normal leading-relaxed disabled:opacity-50"
                  rows="1"
                  style={{
                    minHeight: '36px',
                    maxHeight: '120px',
                  }}
                />
              </div>

              <div className="flex items-center">
                <button
                  onClick={handleSubmit}
                  disabled={!message.trim() || disabled}
                  className="h-8 w-8 bg-[#facc15] text-black rounded-full flex items-center justify-center hover:bg-[#fbbf24] transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-[#facc15] focus:ring-opacity-70 p-0"
                  aria-label="Send message"
                >
                  <ArrowUp className="w-4 h-4" strokeWidth={2} />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

ChatInput.propTypes = {
  onSendMessage: PropTypes.func.isRequired,
  onImageUpload: PropTypes.func.isRequired,
  hasMessages: PropTypes.bool.isRequired,
  disabled: PropTypes.bool,
};

ChatInput.defaultProps = {
  disabled: false,
};

export default ChatInput;