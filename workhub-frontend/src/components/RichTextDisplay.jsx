import React from 'react';
import DOMPurify from 'dompurify';
import './RichTextDisplay.css';

const RichTextDisplay = ({ content, className = '' }) => {
  if (!content) return null;

  // Sanitize HTML content to prevent XSS
  const sanitizedContent = DOMPurify.sanitize(content, {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'u', 'b', 'i', 's', 'strike', 
                   'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'a'],
    ALLOWED_ATTR: ['href', 'title', 'target'],
    ALLOW_DATA_ATTR: false
  });

  // Highlight @mentions in the content
  const highlightMentions = (html) => {
    return html.replace(
      /@([A-Za-z0-9_.'-]{2,50})/g,
      '<span class="mention-highlight">@$1</span>'
    );
  };

  const finalContent = highlightMentions(sanitizedContent);

  return (
    <div 
      className={`rich-text-display ${className}`}
      dangerouslySetInnerHTML={{ __html: finalContent }}
    />
  );
};

export default RichTextDisplay;

