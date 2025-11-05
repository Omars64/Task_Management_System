import React from 'react';
import './ReactionPicker.css';

const COMMON_REACTIONS = [
  '👍', '❤️', '😂', '😮', '😢', '😡', 
  '🙏', '👏', '🔥', '🎉', '💯', '✅'
];

const ReactionPicker = ({ onSelect, onClose }) => {
  const handleSelect = (emoji) => {
    onSelect(emoji);
    onClose();
  };

  return (
    <div className="reaction-picker-popup">
      <div className="reaction-picker-grid">
        {COMMON_REACTIONS.map((emoji) => (
          <button
            key={emoji}
            type="button"
            className="reaction-emoji-btn"
            onClick={() => handleSelect(emoji)}
            title={emoji}
          >
            {emoji}
          </button>
        ))}
      </div>
    </div>
  );
};

export default ReactionPicker;

