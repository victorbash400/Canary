import PropTypes from 'prop-types';

export default function ChatBubble({ message, isUser, timestamp }) {
  // Define base classes for bubbles and text
  const bubbleBaseClasses = "px-4 py-2.5 rounded-xl shadow-sm";
  const textBaseClasses = "text-sm whitespace-pre-wrap break-words m-0 leading-relaxed";

  // Define classes for user bubbles (using previous AI gray background)
  const userBubbleClasses = `bg-[#373A3F] text-gray-100 ${bubbleBaseClasses}`; // User: Dark gray background, gray-100 text
  const userTimestampClasses = "text-xs text-gray-400"; // User: Gray timestamp for consistency

  // Define classes for AI bubbles (no background, blends into chat background)
  const aiBubbleClasses = `px-4 py-2.5`; // No background or shadow, just padding
  const aiTextClasses = `text-gray-100 ${textBaseClasses}`; // AI: Same light gray text
  const aiTimestampClasses = "text-xs text-gray-400"; // AI: Medium-light gray timestamp

  return (
    <div className={`flex w-full mb-3 sm:mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {/* Container for the bubble and its timestamp, controlling max width */}
      <div className={`max-w-[85%] sm:max-w-[70%] md:max-w-[65%] ${isUser ? 'ml-auto' : ''}`}>
        {/* Timestamp display */}
        {timestamp && (
          <div className={`text-xs ${isUser ? 'text-right' : 'text-left'} mb-0.5 px-1`}>
            <span className={isUser ? userTimestampClasses : aiTimestampClasses}>
              {timestamp}
            </span>
          </div>
        )}

        {/* Bubble content */}
        <div className={isUser ? userBubbleClasses : aiBubbleClasses}>
          <p className={isUser ? textBaseClasses : aiTextClasses}>
            {message}
          </p>
        </div>
      </div>
    </div>
  );
}

ChatBubble.propTypes = {
  message: PropTypes.string.isRequired,
  isUser: PropTypes.bool.isRequired,
  timestamp: PropTypes.string,
};