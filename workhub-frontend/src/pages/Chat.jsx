import React, { useState, useEffect, useRef } from 'react';
import { chatAPI, usersAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { FiSend, FiCheck, FiUserPlus, FiMessageCircle, FiSmile, FiPaperclip, FiMoreVertical, FiX } from 'react-icons/fi';
import Modal from '../components/Modal';
import { useModal } from '../hooks/useModal';
import ReactionPicker from '../components/ReactionPicker';
import moment from 'moment';
import './Chat.css';

const Chat = () => {
  const { user } = useAuth();
  const { showSuccess, showError } = useModal();
  const [users, setUsers] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [attachmentFiles, setAttachmentFiles] = useState([]);
  const [messageActionId, setMessageActionId] = useState(null);
  const [editingMessageId, setEditingMessageId] = useState(null);
  const [editingContent, setEditingContent] = useState('');
  const [pendingRequests, setPendingRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [previewUrls, setPreviewUrls] = useState({}); // messageId -> object URL
  const [otherTyping, setOtherTyping] = useState(false);
  const typingTimerRef = useRef(null);
  const [uploadProgress, setUploadProgress] = useState({}); // filename -> percent
  const [galleryOpen, setGalleryOpen] = useState(false);
  const [galleryImages, setGalleryImages] = useState([]); // {id, name, url}
  const [galleryIndex, setGalleryIndex] = useState(0);
  const [showReactionPicker, setShowReactionPicker] = useState(null); // messageId or null
  const [replyingTo, setReplyingTo] = useState(null); // messageId or null
  const messagesEndRef = useRef(null);
  const messageIntervalRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const hasScrolledRef = useRef(false);

  useEffect(() => {
    fetchData();
    
    // Poll for new messages every 3 seconds
    messageIntervalRef.current = setInterval(() => {
      if (selectedConversation) {
        fetchMessages(selectedConversation.id);
      }
      fetchConversations();
    }, 3000);
    
    return () => {
      if (messageIntervalRef.current) {
        clearInterval(messageIntervalRef.current);
      }
    };
  }, [selectedConversation]);

  // Presence heartbeat
  useEffect(() => {
    const beat = () => chatAPI.heartbeat().catch(() => {});
    beat();
    const t = setInterval(beat, 20000);
    return () => clearInterval(t);
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [usersRes, conversationsRes] = await Promise.all([
        chatAPI.getUsers(),
        chatAPI.getConversations()
      ]);
      
      setUsers(usersRes.data || []);
      const convs = conversationsRes.data || [];
      setConversations(convs);
      // Only show pending requests where current user is NOT the requester (they can't accept their own requests)
      setPendingRequests(convs.filter(c => c.status === 'pending' && c.requested_by !== user.id));
    } catch (error) {
      console.error('Failed to fetch chat data:', error);
      showError('Failed to load chat data. Please refresh the page.', 'Chat Error');
    } finally {
      setLoading(false);
    }
  };

  const fetchConversations = async () => {
    try {
      const conversationsRes = await chatAPI.getConversations();
      const convs = conversationsRes.data || [];
      setConversations(convs);
      setPendingRequests(convs.filter(c => c.status === 'pending' && c.requested_by !== user.id));
    } catch (error) {
      console.error('Failed to fetch conversations:', error);
    }
  };

  const fetchMessages = async (conversationId) => {
    try {
      const response = await chatAPI.getMessages(conversationId);
      const msgs = response.data || [];
      setMessages(msgs);
      
      // Mark messages as delivered (when recipient receives them)
      msgs.forEach(msg => {
        if (msg.recipient_id === user.id) {
          if (msg.delivery_status === 'sent') {
            // Mark as delivered (double gray tick)
            chatAPI.markDelivered(msg.id).catch(console.error);
          }
          if (!msg.is_read) {
            // Mark as read when viewing conversation (double colored tick)
            chatAPI.markRead(msg.id).catch(console.error);
          }
        }
      });
      
      // Mark all messages in conversation as read when viewing
      chatAPI.markConversationRead(conversationId).catch(console.error);
    } catch (error) {
      console.error('Failed to fetch messages:', error);
    }
  };

  const handleRequestChat = async (userId) => {
    try {
      await chatAPI.requestChat(userId);
      showSuccess('Chat request sent!');
      fetchData();
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to send chat request', 'Chat Request Error');
    }
  };

  const handleAcceptRequest = async (conversationId) => {
    try {
      await chatAPI.acceptChat(conversationId);
      // Refresh conversations and immediately open the accepted one
      const refreshed = await chatAPI.getConversations();
      const convs = refreshed.data || [];
      setConversations(convs);
      const accepted = convs.find(c => c.id === conversationId) || null;
      if (accepted) {
        setSelectedConversation(accepted);
        fetchMessages(conversationId);
      }
      showSuccess('Chat request accepted');
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to accept chat request', 'Error');
    }
  };

  const handleRejectRequest = async (conversationId) => {
    try {
      await chatAPI.rejectChat(conversationId);
      fetchData();
      showSuccess('Chat request rejected');
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to reject chat request', 'Error');
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if ((!newMessage.trim() && attachmentFiles.length === 0) || !selectedConversation) return;
    
    // Prevent sending messages if conversation is not accepted
    if (selectedConversation.status !== 'accepted') {
      showError('Chat request must be accepted before sending messages', 'Error');
      return;
    }
    
    try {
      if (attachmentFiles.length > 0) {
        for (const f of attachmentFiles) {
          // eslint-disable-next-line no-await-in-loop
          await chatAPI.uploadAttachment(selectedConversation.id, f);
        }
      }
      if (newMessage.trim()) {
        await chatAPI.sendMessage(selectedConversation.id, newMessage, replyingTo);
      }
      setNewMessage('');
      setAttachmentFiles([]);
      setReplyingTo(null);
      await fetchMessages(selectedConversation.id);
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to send message', 'Error Sending Message');
    }
  };

  const handleSelectConversation = (conversation) => {
    if (conversation.status !== 'accepted') {
      showError('Conversation not accepted yet', 'Error');
      return;
    }
    setSelectedConversation(conversation);
    fetchMessages(conversation.id);
    // Clear unread count server-side for this conversation
    chatAPI.markConversationRead(conversation.id).catch(() => {});
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'auto' });
  };

  // Scroll to bottom when conversation is first selected (only once, not on every message update)
  useEffect(() => {
    if (selectedConversation && messages.length > 0 && !hasScrolledRef.current) {
      // Small delay to ensure messages are rendered in DOM
      setTimeout(() => {
        scrollToBottom();
        hasScrolledRef.current = true;
      }, 50);
    }
  }, [selectedConversation?.id, messages.length]); // Trigger when conversation changes or messages load
  
  // Reset scroll flag when conversation changes
  useEffect(() => {
    hasScrolledRef.current = false;
  }, [selectedConversation?.id]);

  // Close popovers when clicking outside
  useEffect(() => {
    const onDocClick = (e) => {
      if (!e.target.closest) return;
      if (!e.target.closest('.emoji-picker') && !e.target.closest('.emoji-button')) {
        setShowEmojiPicker(false);
      }
      if (!e.target.closest('.message-actions') && !e.target.closest('.message-actions-toggle')) {
        setMessageActionId(null);
      }
      if (!e.target.closest('.reaction-picker-popup') && !e.target.closest('.add-reaction-btn')) {
        setShowReactionPicker(null);
      }
    };
    document.addEventListener('click', onDocClick);
    return () => document.removeEventListener('click', onDocClick);
  }, []);

  const handleAddEmoji = (emoji) => {
    setNewMessage((prev) => prev + emoji);
    // keep picker open for multiple selections; closed by outside click
  };

  const handleAttachmentChange = (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    const maxBytes = 50 * 1024 * 1024; // 50 MB
    const valid = files.filter(f => {
      if (f.size > maxBytes) {
        showError(`${f.name} exceeds 50 MB`, 'Attachment Too Large');
        return false;
      }
      return true;
    });
    setAttachmentFiles(prev => [...prev, ...valid]);
    e.target.value = '';
  };

  const handleRemoveAttachment = (idx) => {
    setAttachmentFiles(prev => prev.filter((_, i) => i !== idx));
  };

  const handleDownloadAttachment = async (msg, filename) => {
    try {
      const res = await chatAPI.downloadAttachment(msg.id);
      const blob = new Blob([res.data]);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || 'download';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      showError('Failed to download attachment', 'Download Error');
    }
  };

  const handlePreviewAttachment = async (msg, filename) => {
    try {
      const res = await chatAPI.downloadAttachment(msg.id);
      const blob = new Blob([res.data]);
      const url = window.URL.createObjectURL(blob);
      setPreviewUrls((s) => ({ ...s, [msg.id]: url }));
    } catch (e) {
      showError('Failed to preview attachment', 'Preview Error');
    }
  };

  // Typing indicator
  const notifyTyping = () => {
    if (!selectedConversation) return;
    chatAPI.setTyping(selectedConversation.id, true).catch(() => {});
    if (typingTimerRef.current) clearTimeout(typingTimerRef.current);
    typingTimerRef.current = setTimeout(() => {
      chatAPI.setTyping(selectedConversation.id, false).catch(() => {});
    }, 3000);
  };

  useEffect(() => {
    if (!selectedConversation) return;
    const interval = setInterval(async () => {
      try {
        const r = await chatAPI.getTyping(selectedConversation.id);
        setOtherTyping(Boolean(r.data?.typing));
      } catch (e) {}
    }, 2000);
    return () => clearInterval(interval);
  }, [selectedConversation]);

  const canModifyMessage = (msg) => {
    if (msg.sender_id !== user.id) return false;
    const created = moment.utc(msg.created_at);
    return moment.utc().diff(created, 'minutes') <= 30;
  };

  const startEditMessage = (msg) => {
    if (!canModifyMessage(msg)) return;
    setEditingMessageId(msg.id);
    setEditingContent(msg.content);
    setMessageActionId(null);
  };

  const submitEditMessage = async (msg) => {
    if (!editingContent.trim()) {
      showError('Message cannot be empty', 'Invalid');
      return;
    }
    try {
      await chatAPI.editMessage(msg.id, editingContent);
      showSuccess('Message updated');
      fetchMessages(selectedConversation.id);
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to edit message', 'Edit Error');
    } finally {
      setEditingMessageId(null);
      setEditingContent('');
    }
  };

  const deleteForMe = async (msg) => {
    try {
      await chatAPI.deleteForMe(msg.id);
      // Remove from local state
      setMessages((prev) => prev.filter((m) => m.id !== msg.id));
      setMessageActionId(null);
      showSuccess('Message deleted for you');
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to delete message for you', 'Delete Error');
    }
  };

  const deleteForEveryone = async (msg) => {
    if (!canModifyMessage(msg)) return;
    try {
      await chatAPI.deleteForEveryone(msg.id);
      showSuccess('Message deleted for everyone');
      fetchMessages(selectedConversation.id);
      setMessageActionId(null);
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to delete message for everyone', 'Delete Error');
      setMessageActionId(null);
    }
  };

  const handleAddReaction = async (messageId, emoji) => {
    try {
      await chatAPI.addReaction(messageId, emoji);
      // Refresh messages to get updated reactions
      if (selectedConversation) {
        await fetchMessages(selectedConversation.id);
      }
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to add reaction', 'Error');
    }
  };

  const handleRemoveReaction = async (messageId, reactionId) => {
    try {
      await chatAPI.removeReaction(messageId, reactionId);
      // Refresh messages to get updated reactions
      if (selectedConversation) {
        await fetchMessages(selectedConversation.id);
      }
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to remove reaction', 'Error');
    }
  };

  const getDeliveryIcon = (message) => {
    if (message.sender_id !== user.id) return null;
    
    if (message.is_read) {
      return (
        <span className="icon-double-checked">
          <FiCheck />
          <FiCheck />
        </span>
      );
    } else if (message.delivery_status === 'delivered' || message.delivery_status === 'read') {
      return (
        <span className="icon-double-gray">
          <FiCheck />
          <FiCheck />
        </span>
      );
    } else if (message.delivery_status === 'sent') {
      return <FiCheck className="icon-single-gray" />;
    }
    return <FiCheck className="icon-single-gray" />;
  };

  // Helper function to normalize and validate emoji
  const normalizeEmoji = (emoji) => {
    if (!emoji) return '';
    // Remove any null bytes or invalid characters
    const cleaned = emoji.replace(/\0/g, '').trim();
    // Ensure it's a valid Unicode string
    try {
      // If emoji is corrupted, try to decode it
      if (cleaned.includes('??') || cleaned.length === 0) {
        return cleaned; // Return as-is if already corrupted
      }
      return cleaned;
    } catch (e) {
      return cleaned;
    }
  };

  const groupReactions = (reactions) => {
    const grouped = {};
    reactions.forEach(r => {
      if (!r || !r.emoji) return;
      const normalizedEmoji = normalizeEmoji(r.emoji);
      if (!normalizedEmoji || normalizedEmoji.includes('??')) {
        // Skip corrupted emojis
        console.warn('Skipping corrupted emoji reaction:', r.emoji);
        return;
      }
      if (!grouped[normalizedEmoji]) {
        grouped[normalizedEmoji] = [];
      }
      grouped[normalizedEmoji].push(r);
    });
    return grouped;
  };

  if (loading) {
    return <div className="spinner" />;
  }

  return (
    <>
    <div className="chat-page">
      <div className="chat-header">
        <h1>Chat</h1>
      </div>

      {pendingRequests.length > 0 && (
        <div className="pending-requests">
          <h3>Pending Chat Requests</h3>
          {pendingRequests.map(req => (
            <div key={req.id} className="request-item">
              <div className="request-info">
                <strong>{req.other_user.name}</strong> wants to chat with you
              </div>
              <div className="request-actions">
                <button className="btn btn-primary btn-sm" onClick={() => handleAcceptRequest(req.id)}>
                  Accept
                </button>
                <button className="btn btn-outline btn-sm" onClick={() => handleRejectRequest(req.id)}>
                  Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="chat-container">
        <div className="chat-sidebar">
          <div className="sidebar-section">
            <h3>Conversations</h3>
            {conversations.length === 0 ? (
              <p className="empty-state-text">No conversations yet</p>
            ) : (
              conversations
                .filter(c => c.status === 'accepted')
                .map(conv => (
                  <div
                    key={conv.id}
                    className={`conversation-item ${selectedConversation?.id === conv.id ? 'active' : ''}`}
                    onClick={() => handleSelectConversation(conv)}
                  >
                    <div className="conversation-avatar">
                      {conv.other_user.name.charAt(0).toUpperCase()}
                    </div>
                    <div className="conversation-info">
                      <div className="conversation-name">{conv.other_user.name}</div>
                      <div className="conversation-preview">
                        {conv.last_message || (conv.status === 'accepted' ? 'No messages yet' : conv.status)}
                      </div>
                    </div>
                    {conv.unread_count > 0 && (
                      <div className="unread-badge">{conv.unread_count}</div>
                    )}
                  </div>
                ))
            )}
          </div>

          <div className="sidebar-section">
            <h3>All Users</h3>
            {users.length === 0 ? (
              <p className="empty-state-text">No users available</p>
            ) : (
              users.map(u => {
              // Find conversation where current user and this user are participants
              const existingConv = conversations.find(c => {
                // Check if other_user matches (this is how the API returns it)
                if (c.other_user && c.other_user.id === u.id) return true;
                return false;
              });
              
              return (
                <div key={u.id} className="user-item">
                  <div className="user-avatar">{u.name.charAt(0).toUpperCase()}</div>
                  <div className="user-info">
                    <div className="user-name">{u.name}</div>
                    <div className="user-email">{u.email}</div>
                  </div>
                  {(() => {
                    // Show add button if:
                    // 1. No conversation exists, OR
                    // 2. Conversation was rejected (so user can retry), OR
                    // 3. Conversation is pending and current user is the requester (waiting for response)
                    const showAddButton = !existingConv || 
                      (existingConv.status === 'rejected') ||
                      (existingConv.status === 'pending' && existingConv.requested_by === user.id);
                    
                    // Show pending badge if conversation is pending and user is the requester
                    const showPendingBadge = existingConv && 
                      existingConv.status === 'pending' && 
                      existingConv.requested_by === user.id;
                    
                    // Show accept/reject buttons if conversation is pending and user is NOT the requester
                    const showAcceptReject = existingConv && 
                      existingConv.status === 'pending' && 
                      existingConv.requested_by !== user.id;
                    
                    return (
                      <>
                        {showAddButton && (
                          <button
                            className="btn-icon-small"
                            onClick={() => handleRequestChat(u.id)}
                            title={existingConv && existingConv.status === 'rejected' ? 'Retry Chat Request' : 'Request Chat'}
                          >
                            <FiUserPlus />
                          </button>
                        )}
                        {showPendingBadge && (
                          <span className="status-badge pending">Pending</span>
                        )}
                        {showAcceptReject && (
                          <div className="request-actions-inline">
                            <button
                              className="btn-icon-small accept"
                              onClick={() => handleAcceptRequest(existingConv.id)}
                              title="Accept"
                            >
                              ✓
                            </button>
                            <button
                              className="btn-icon-small reject"
                              onClick={() => handleRejectRequest(existingConv.id)}
                              title="Reject"
                            >
                              ✕
                            </button>
                          </div>
                        )}
                      </>
                    );
                  })()}
                </div>
              );
            })
            )}
          </div>
        </div>

        <div className="chat-main">
          {selectedConversation ? (
            <>
              <div className="chat-header-bar">
                <div className="chat-user-info">
                  <div className="chat-avatar">
                    {selectedConversation.other_user.name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <div className="chat-user-name">{selectedConversation.other_user.name}</div>
                    <div className="chat-user-status">{otherTyping ? 'Typing…' : 'Online'}</div>
                  </div>
                </div>
              </div>

              <div className="messages-container" ref={messagesContainerRef}>
                {messages.map(msg => (
                  <div
                    key={msg.id}
                    className={`message ${msg.sender_id === user.id ? 'sent' : 'received'}`}
                  >
                    <div className="message-content">
                      {msg.sender_id !== user.id && (
                        <div className="message-sender">{msg.sender_name}</div>
                      )}
                      {msg.reply_to && (
                        <div className="message-reply-preview">
                          <div className="reply-indicator"></div>
                          <div className="reply-content">
                            <div className="reply-sender">{msg.reply_to.sender_name}</div>
                            <div className="reply-text">{msg.reply_to.content}</div>
                          </div>
                        </div>
                      )}
                      {editingMessageId === msg.id ? (
                        <div className="message-editing">
                          <input
                            className="message-edit-input"
                            value={editingContent}
                            onChange={(e) => setEditingContent(e.target.value)}
                          />
                          <div className="message-edit-actions">
                            <button type="button" className="btn-small" onClick={() => submitEditMessage(msg)}>Save</button>
                            <button type="button" className="btn-small secondary" onClick={() => { setEditingMessageId(null); setEditingContent(''); }}>Cancel</button>
                          </div>
                        </div>
                      ) : (
                        (() => {
                          let rendered = null;
                          try {
                            const data = typeof msg.content === 'string' ? JSON.parse(msg.content) : msg.content;
                            if (data && data.type === 'file') {
                              const sizeKb = Math.max(1, Math.round((data.size || 0) / 1024));
                              const url = previewUrls[msg.id];
                              const ext = (data.name || '').split('.').pop().toLowerCase();
                              const isImage = ['jpg','jpeg','png','gif','webp'].includes(ext);
                              const isVideo = ['mp4','webm','ogg','mov'].includes(ext);
                              const isPdf = ext === 'pdf';
                              rendered = (
                                <div className="message-text">
                                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                                    <button type="button" className="linklike" onClick={() => handleDownloadAttachment(msg, data.name)}>
                                      <span style={{ marginRight: 6, display: 'inline-flex', verticalAlign: 'middle' }}><FiPaperclip /></span>
                                      {data.name || 'Download file'} ({sizeKb} KB)
                                    </button>
                                    {(isImage || isVideo || isPdf) && (
                                      <>
                                        {!url && (
                                          <button type="button" className="btn-small secondary" onClick={() => handlePreviewAttachment(msg, data.name)}>Preview</button>
                                        )}
                                        {url && isImage && (
                                          <img src={url} alt={data.name} style={{ maxWidth: 260, borderRadius: 8, cursor: 'zoom-in' }} onClick={() => {
                                            const imgs = messages.flatMap(m => {
                                              try {
                                                const d = typeof m.content === 'string' ? JSON.parse(m.content) : m.content;
                                                const e = (d?.name || '').split('.').pop().toLowerCase();
                                                if (d && d.type === 'file' && ['jpg','jpeg','png','gif','webp'].includes(e)) {
                                                  const purl = previewUrls[m.id];
                                                  if (purl) return [{ id: m.id, name: d.name, url: purl }];
                                                }
                                              } catch (err) {}
                                              return [];
                                            });
                                            setGalleryImages(imgs);
                                            const idx = imgs.findIndex(i => i.id === msg.id);
                                            setGalleryIndex(Math.max(0, idx));
                                            setGalleryOpen(true);
                                          }} />
                                        )}
                                        {url && isVideo && (
                                          <video src={url} style={{ maxWidth: 260, borderRadius: 8 }} controls />
                                        )}
                                        {url && isPdf && (
                                          <iframe src={url} title={data.name} style={{ width: 260, height: 200, border: 'none', borderRadius: 8 }} />
                                        )}
                                      </>
                                    )}
                                  </div>
                                </div>
                              );
                            }
                          } catch (e) {}
                          if (!rendered) {
                            rendered = (
                              <div className="message-text">
                                {msg.content}
                                {msg.is_edited && <span className="message-edited-indicator"> (edited)</span>}
                              </div>
                            );
                          }
                          return rendered;
                        })()
                      )}
                      <div className="message-footer">
                        <div className="message-time-actions">
                          <span className="message-time">
                            {new Date(msg.created_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })}
                          </span>
                          <div className="message-actions">
                            <button
                              type="button"
                              className="message-actions-toggle"
                              onClick={(e) => {
                                e.stopPropagation();
                                setMessageActionId(messageActionId === msg.id ? null : msg.id);
                              }}
                              title="More actions"
                            >
                              <FiMoreVertical />
                            </button>
                            {messageActionId === msg.id && (
                              <div className="message-actions-menu">
                                <button type="button" onClick={() => { setReplyingTo(msg.id); setMessageActionId(null); }}>Reply</button>
                                {msg.sender_id === user.id && (
                                  <button type="button" disabled={!canModifyMessage(msg) || msg.is_deleted} onClick={() => startEditMessage(msg)}>Edit</button>
                                )}
                                <button type="button" onClick={() => deleteForMe(msg)}>Delete for me</button>
                                {msg.sender_id === user.id && (
                                  <button type="button" disabled={!canModifyMessage(msg) || msg.is_deleted} onClick={() => deleteForEveryone(msg)}>Delete for everyone</button>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="message-status">
                          {getDeliveryIcon(msg)}
                        </div>
                      </div>
                      {msg.reactions && msg.reactions.length > 0 && (
                        <div className="message-reactions">
                          {Object.entries(groupReactions(msg.reactions)).map(([emoji, reactionList]) => {
                            const userReacted = reactionList.some(r => r.user_id === user.id);
                            const userReaction = reactionList.find(r => r.user_id === user.id);
                            return (
                              <button
                                key={emoji}
                                type="button"
                                className={`reaction-bubble ${userReacted ? 'user-reacted' : ''}`}
                                onClick={() => {
                                  if (userReacted && userReaction) {
                                    handleRemoveReaction(msg.id, userReaction.id);
                                  } else {
                                    handleAddReaction(msg.id, emoji);
                                  }
                                }}
                                title={reactionList.map(r => r.user_name).join(', ')}
                              >
                                <span className="reaction-emoji" role="img" aria-label="emoji">
                                  {normalizeEmoji(emoji) || '❓'}
                                </span>
                                <span className="reaction-count">{reactionList.length}</span>
                              </button>
                            );
                          })}
                          <button
                            type="button"
                            className="add-reaction-btn"
                            onClick={(e) => {
                              e.stopPropagation();
                              setShowReactionPicker(showReactionPicker === msg.id ? null : msg.id);
                            }}
                            title="Add reaction"
                          >
                            <FiSmile />
                          </button>
                          {showReactionPicker === msg.id && (
                            <ReactionPicker
                              onSelect={(emoji) => handleAddReaction(msg.id, emoji)}
                              onClose={() => setShowReactionPicker(null)}
                            />
                          )}
                        </div>
                      )}
                      {(!msg.reactions || msg.reactions.length === 0) && (
                        <div className="message-reactions-empty">
                          <button
                            type="button"
                            className="add-reaction-btn"
                            onClick={(e) => {
                              e.stopPropagation();
                              setShowReactionPicker(showReactionPicker === msg.id ? null : msg.id);
                            }}
                            title="Add reaction"
                          >
                            <FiSmile />
                          </button>
                          {showReactionPicker === msg.id && (
                            <ReactionPicker
                              onSelect={(emoji) => handleAddReaction(msg.id, emoji)}
                              onClose={() => setShowReactionPicker(null)}
                            />
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>

              <form className="message-input-form" onSubmit={handleSendMessage}
                onDragOver={(e) => { e.preventDefault(); }}
                onDrop={(e) => {
                  e.preventDefault();
                  if (!e.dataTransfer || !e.dataTransfer.files || e.dataTransfer.files.length === 0) return;
                  const maxBytes = 50 * 1024 * 1024;
                  const files = Array.from(e.dataTransfer.files).filter(f => {
                    if (f.size > maxBytes) { showError(`${f.name} exceeds 50 MB`, 'Attachment Too Large'); return false; }
                    return true;
                  });
                  setAttachmentFiles(prev => [...prev, ...files]);
                }}
              >
                <div className="input-left-controls">
                  <button type="button" className="emoji-button" onClick={() => setShowEmojiPicker(v => !v)} title="Emoji">
                    <FiSmile />
                  </button>
                  <label className="attach-button" title="Attach file" style={{ position: 'relative' }}>
                    <FiPaperclip />
                    {attachmentFiles.length > 0 && (
                      <span className="attachment-badge">{attachmentFiles.length}</span>
                    )}
                    <input type="file" onChange={handleAttachmentChange} style={{ display: 'none' }} multiple />
                  </label>
                </div>
                {replyingTo && (() => {
                  const replyMsg = messages.find(m => m.id === replyingTo);
                  return replyMsg ? (
                    <div className="reply-preview-bar">
                      <div className="reply-preview-content">
                        <div className="reply-preview-sender">Replying to {replyMsg.sender_name}</div>
                        <div className="reply-preview-text">{replyMsg.content.length > 50 ? replyMsg.content.substring(0, 50) + '...' : replyMsg.content}</div>
                      </div>
                      <button type="button" className="reply-preview-close" onClick={() => setReplyingTo(null)}>×</button>
                    </div>
                  ) : null;
                })()}
                <textarea
                  className="message-input"
                  placeholder={replyingTo ? "Type a reply..." : "Type a message..."}
                  value={newMessage}
                  onChange={(e) => { setNewMessage(e.target.value); notifyTyping(); }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage(e);
                    }
                  }}
                  onPaste={(e) => {
                    const items = e.clipboardData && e.clipboardData.items;
                    if (!items) return;
                    const maxBytes = 50 * 1024 * 1024;
                    for (const it of items) {
                      if (it.type.startsWith('image/')) {
                        const file = it.getAsFile();
                        if (file && file.size <= maxBytes) {
                          setAttachmentFiles(prev => [...prev, file]);
                        }
                      }
                    }
                  }}
                  rows={1}
                />
                <div className="input-right-controls">
                  <button type="submit" className="send-button" disabled={!newMessage.trim() && attachmentFiles.length === 0}>
                    <FiSend />
                  </button>
                </div>
                {showEmojiPicker && (
                  <div className="emoji-picker">
                    {['😀','😂','😉','😊','😍','😘','🤔','👍','🙏','🎉','🔥','💯','😢','😮','🙌','🤝','🥳','👏'].map(e => (
                      <button key={e} type="button" className="emoji-item" onClick={() => handleAddEmoji(e)}>{e}</button>
                    ))}
                  </div>
                )}
                {attachmentFiles && attachmentFiles.length > 0 && (
                  <div className="attachment-list">
                    {attachmentFiles.map((f, idx) => (
                      <div key={idx} className="attachment-chip">
                        <span className="attachment-name">{f.name}</span>
                        <div className="progress"><span style={{ width: `${uploadProgress[f.name] || 0}%` }} /></div>
                        <span className="percent">{uploadProgress[f.name] ? `${uploadProgress[f.name]}%` : ''}</span>
                        <button type="button" className="attachment-remove" onClick={() => handleRemoveAttachment(idx)} title="Remove">
                          <FiX />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
                {(() => {
                  const names = attachmentFiles.map(f => f.name).filter(n => uploadProgress[n] != null);
                  if (names.length === 0) return null;
                  const avg = Math.round(names.reduce((s, n) => s + (uploadProgress[n] || 0), 0) / names.length);
                  return (
                    <div className="overall-progress">
                      <div className="bar"><span style={{ width: `${avg}%` }} /></div>
                      <span>{`Uploading ${names.length}/${attachmentFiles.length} (${avg}%)`}</span>
                    </div>
                  );
                })()}
              </form>
            </>
          ) : (
            <div className="chat-placeholder">
              <FiMessageCircle size={64} />
              <p>Select a conversation to start chatting</p>
            </div>
          )}
        </div>
      </div>
    </div>
    {galleryOpen && (
      <div className="gallery-overlay" onClick={() => setGalleryOpen(false)}>
        <button className="gallery-close" onClick={() => setGalleryOpen(false)}>×</button>
        {galleryImages[galleryIndex] && (
          <img className="gallery-content" src={galleryImages[galleryIndex].url} alt={galleryImages[galleryIndex].name} />
        )}
        <div className="gallery-nav">
          <span style={{ marginLeft: 16 }} onClick={(e) => { e.stopPropagation(); setGalleryIndex(i => Math.max(0, i - 1)); }}>‹</span>
          <span style={{ marginRight: 16 }} onClick={(e) => { e.stopPropagation(); setGalleryIndex(i => Math.min(galleryImages.length - 1, i + 1)); }}>›</span>
        </div>
      </div>
    )}
    </>
  );
};

export default Chat;

