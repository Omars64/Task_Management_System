import { useEffect, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { groupsAPI, chatAPI, usersAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useModal } from '../hooks/useModal';
import { FiSend, FiSmile, FiPaperclip, FiX, FiCheck } from 'react-icons/fi';
import ReactionPicker from '../components/ReactionPicker';
import moment from 'moment';
import './Chat.css';

const Groups = () => {
  const { user } = useAuth();
  const { showSuccess, showError } = useModal();
  const [groups, setGroups] = useState([]);
  const [users, setUsers] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [selectedGroupDetails, setSelectedGroupDetails] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [creating, setCreating] = useState(false);
  const [newGroupName, setNewGroupName] = useState('');
  const [selectedMembers, setSelectedMembers] = useState([]);
  const [typing, setTyping] = useState([]);
  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState('');
  const [editMembers, setEditMembers] = useState([]);
  const [addMemberIds, setAddMemberIds] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [replyingTo, setReplyingTo] = useState(null);
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [attachmentFiles, setAttachmentFiles] = useState([]);
  const [editingMessageId, setEditingMessageId] = useState(null);
  const [editingContent, setEditingContent] = useState('');
  const [previewUrls, setPreviewUrls] = useState({});
  const [uploadProgress, setUploadProgress] = useState({});
  const [galleryOpen, setGalleryOpen] = useState(false);
  const [galleryImages, setGalleryImages] = useState([]);
  const [galleryIndex, setGalleryIndex] = useState(0);
  const [showReactionPicker, setShowReactionPicker] = useState(null);
  const [contextPopover, setContextPopover] = useState(null);
  const [activeCount, setActiveCount] = useState(0);
  const [showInvites, setShowInvites] = useState(false);
  const [invitesModalOpen, setInvitesModalOpen] = useState(false);
  const fileInputRef = useRef(null);
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const pollRef = useRef(null);
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const typingTimerRef = useRef(null);
  const hasScrolledRef = useRef(false);
  const invitesButtonRef = useRef(null);

  const getCurrentUserId = () => {
    try {
      const token = localStorage.getItem('token');
      const payload = JSON.parse(atob((token || '').split('.')[1] || 'e30='));
      return payload?.sub;
    } catch (_) {
      return null;
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    fetchGroups();
    fetchUsers();
    fetchInvitations();
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  // Handle deep-linking from notifications
  useEffect(() => {
    const groupId = searchParams.get('groupId');
    if (groupId && groups.length > 0) {
      const group = groups.find(g => g.id === parseInt(groupId));
      if (group) {
        setSelectedGroup(group);
        // Clean up URL
        setSearchParams({});
      }
    }
  }, [groups, searchParams, setSearchParams]);

  useEffect(() => {
    if (pollRef.current) clearInterval(pollRef.current);
    if (!selectedGroup) return;
    hasScrolledRef.current = false;
    // also load group details (members/roles)
    (async () => {
      try {
        const res = await groupsAPI.getDetails(selectedGroup.id);
        const details = res.data || {};
        setSelectedGroupDetails(details);
        setEditName(details?.group?.name || '');
        setEditMembers(Array.isArray(details?.members) ? details.members : []);
        // compute active members (online or recently active)
        try {
          const members = Array.isArray(details?.members) ? details.members : [];
          const presences = await Promise.allSettled(members.map(m => chatAPI.getPresence(m.user_id)));
          const active = presences.reduce((sum, r) => (r.status === 'fulfilled' && r.value?.data?.online) ? sum + 1 : sum, 0);
          setActiveCount(active);
        } catch (_) {}
      } catch (_) {}
    })();
    const load = async () => {
      try {
        const [msgRes, typingRes] = await Promise.all([
          groupsAPI.getMessages(selectedGroup.id),
          groupsAPI.getTyping(selectedGroup.id),
        ]);
        setMessages(msgRes.data || []);
        setTyping((typingRes.data && typingRes.data.typing) || []);
        if (!hasScrolledRef.current) {
          setTimeout(scrollToBottom, 100);
          hasScrolledRef.current = true;
        }
      } catch (_) {}
    };
    load();
    pollRef.current = setInterval(load, 6000);
    return () => pollRef.current && clearInterval(pollRef.current);
  }, [selectedGroup?.id]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const fetchGroups = async () => {
    try {
      const res = await groupsAPI.list();
      setGroups(res.data || []);
    } catch (_) {}
  };

  const fetchUsers = async () => {
    try {
      const res = await chatAPI.getUsers();
      setUsers(res.data || []);
    } catch (_) {}
  };

  const fetchInvitations = async () => {
    try {
      const res = await groupsAPI.listInvitations();
      setInvitations(res.data || []);
    } catch (_) {}
  };

  const createGroup = async (e) => {
    e.preventDefault();
    if (!newGroupName.trim()) return;
    try {
      const res = await groupsAPI.create(newGroupName.trim(), selectedMembers);
      setCreating(false);
      setNewGroupName('');
      setSelectedMembers([]);
      await fetchGroups();
      await fetchInvitations();
      setSelectedGroup(res.data);
    } catch (err) {
      console.error('Create group failed', err);
    }
  };

  const send = async (e) => {
    e?.preventDefault();
    if ((!input.trim() && attachmentFiles.length === 0) || !selectedGroup) return;
    try {
      if (attachmentFiles.length > 0) {
        for (const f of attachmentFiles) {
          try {
            await groupsAPI.uploadAttachment(selectedGroup.id, f, {
              onUploadProgress: (progressEvent) => {
                const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                setUploadProgress(prev => ({ ...prev, [f.name]: percent }));
              }
            });
          } catch (err) {
            showError(`Failed to upload ${f.name}`, 'Upload Error');
          }
        }
      }
      if (input.trim()) {
        await groupsAPI.sendMessage(selectedGroup.id, input.trim(), replyingTo?.id || null);
      }
      setInput('');
      setAttachmentFiles([]);
      setReplyingTo(null);
      setUploadProgress({});
      await groupsAPI.markRead(selectedGroup.id);
      const res = await groupsAPI.getMessages(selectedGroup.id);
      setMessages(res.data || []);
    } catch (err) {
      showError(err.response?.data?.error || 'Failed to send message', 'Error');
    }
  };

  const notifyTyping = () => {
    if (!selectedGroup) return;
    groupsAPI.setTyping(selectedGroup.id, true).catch(() => {});
    if (typingTimerRef.current) clearTimeout(typingTimerRef.current);
    typingTimerRef.current = setTimeout(() => {
      groupsAPI.setTyping(selectedGroup.id, false).catch(() => {});
    }, 3000);
  };

  const handleAddEmoji = (emoji) => {
    setInput((prev) => prev + emoji);
  };

  const handleAttachmentChange = (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    const maxBytes = 50 * 1024 * 1024;
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
      const res = await groupsAPI.downloadAttachment(msg.id);
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
      const res = await groupsAPI.downloadAttachment(msg.id);
      const blob = new Blob([res.data]);
      const url = window.URL.createObjectURL(blob);
      setPreviewUrls((s) => ({ ...s, [msg.id]: url }));
    } catch (e) {
      showError('Failed to preview attachment', 'Preview Error');
    }
  };

  const canModifyMessage = (msg) => {
    if (msg.sender_id !== getCurrentUserId()) return false;
    const created = moment.utc(msg.created_at);
    return moment.utc().diff(created, 'minutes') <= 30;
  };

  const startEditMessage = (msg) => {
    if (!canModifyMessage(msg)) return;
    setEditingMessageId(msg.id);
    setEditingContent(msg.content);
    setContextPopover(null);
  };

  const submitEditMessage = async (msg) => {
    if (!editingContent.trim()) {
      showError('Message cannot be empty', 'Invalid');
      return;
    }
    try {
      await groupsAPI.editMessage(msg.id, editingContent);
      showSuccess('Message updated');
      const res = await groupsAPI.getMessages(selectedGroup.id);
      setMessages(res.data || []);
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to edit message', 'Edit Error');
    } finally {
      setEditingMessageId(null);
      setEditingContent('');
    }
  };

  const deleteForMe = async (msg) => {
    try {
      await groupsAPI.deleteForMe(msg.id);
      setMessages((prev) => prev.filter((m) => m.id !== msg.id));
      setContextPopover(null);
      showSuccess('Message deleted for you');
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to delete message for you', 'Delete Error');
    }
  };

  const deleteForEveryone = async (msg) => {
    if (!canModifyMessage(msg)) return;
    try {
      await groupsAPI.deleteForEveryone(msg.id);
      showSuccess('Message deleted for everyone');
      const res = await groupsAPI.getMessages(selectedGroup.id);
      setMessages(res.data || []);
      setContextPopover(null);
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to delete message for everyone', 'Delete Error');
      setContextPopover(null);
    }
  };

  const handleAddReaction = async (messageId, emoji) => {
    try {
      await groupsAPI.addReaction(messageId, emoji);
      const res = await groupsAPI.getMessages(selectedGroup.id);
      setMessages(res.data || []);
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to add reaction', 'Error');
    }
  };

  const handleRemoveReaction = async (messageId, reactionId) => {
    try {
      await groupsAPI.removeReaction(messageId, reactionId);
      const res = await groupsAPI.getMessages(selectedGroup.id);
      setMessages(res.data || []);
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to remove reaction', 'Error');
    }
  };

  const normalizeEmoji = (emoji) => {
    if (!emoji) return '';
    if (typeof emoji === 'string' && emoji.includes('??')) {
      try {
        const encoded = encodeURIComponent(emoji);
        const decoded = decodeURIComponent(encoded);
        if (decoded && !decoded.includes('??')) {
          return decoded.trim();
        }
      } catch (e) {}
      return '';
    }
    const cleaned = emoji.replace(/\0/g, '').trim();
    if (cleaned && cleaned.length > 0) {
      try {
        const test = new TextEncoder().encode(cleaned);
        const decoded = new TextDecoder('utf-8').decode(test);
        if (decoded && !decoded.includes('?')) {
          return decoded;
        }
      } catch (e) {
        console.warn('Emoji encoding validation failed:', emoji);
      }
      return cleaned;
    }
    return '';
  };

  const openContextPopover = (event, msg) => {
    event.preventDefault();
    const popoverWidth = 220;
    const popoverHeight = 200;
    const padding = 10;
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    let x = event.pageX;
    let y = event.pageY;
    const isSentMessage = msg.sender_id === getCurrentUserId();
    if (isSentMessage) {
      x = x - popoverWidth - 10;
    } else {
      x = x + 10;
    }
    if (x + popoverWidth > viewportWidth - padding) {
      x = viewportWidth - popoverWidth - padding;
    }
    if (x < padding) {
      x = padding;
    }
    if (y + popoverHeight > viewportHeight - padding) {
      y = viewportHeight - popoverHeight - padding;
    }
    if (y < padding) {
      y = padding;
    }
    setContextPopover({ msg, x, y });
  };

  const groupReactions = (reactions) => {
    const grouped = {};
    reactions.forEach(r => {
      if (!r || !r.emoji) return;
      const normalizedEmoji = normalizeEmoji(r.emoji);
      if (!normalizedEmoji || normalizedEmoji.includes('??')) {
        return;
      }
      if (!grouped[normalizedEmoji]) {
        grouped[normalizedEmoji] = [];
      }
      grouped[normalizedEmoji].push(r);
    });
    return grouped;
  };

  useEffect(() => {
    const onDocClick = (e) => {
      if (!e.target.closest) return;
      if (!e.target.closest('.emoji-picker') && !e.target.closest('.emoji-button')) {
        setShowEmojiPicker(false);
      }
      if (!e.target.closest('.message-context-popover')) {
        setContextPopover(null);
      }
      if (!e.target.closest('.reaction-picker-popup') && !e.target.closest('.add-reaction-btn')) {
        setShowReactionPicker(null);
      }
      // Close invite popover when clicking outside
      if (!e.target.closest('[data-invites-popover]') && !e.target.closest('[data-invites-button]')) {
        setShowInvites(false);
      }
    };
    document.addEventListener('click', onDocClick);
    return () => document.removeEventListener('click', onDocClick);
  }, []);

  const isGroupAdmin = () => {
    const myId = getCurrentUserId();
    const myMember = (selectedGroupDetails?.members || []).find(m => m.user_id === myId);
    return myMember && (myMember.role === 'owner' || myMember.role === 'admin');
  };

  const openEdit = () => {
    if (!selectedGroupDetails) return;
    setEditName(selectedGroupDetails?.group?.name || '');
    setEditMembers(Array.isArray(selectedGroupDetails?.members) ? selectedGroupDetails.members : []);
    setAddMemberIds([]);
    setEditing(true);
  };

  const saveEdit = async () => {
    try {
      if (editName.trim() && editName.trim() !== selectedGroupDetails?.group?.name) {
        await groupsAPI.rename(selectedGroup.id, editName.trim());
      }
      if (addMemberIds.length > 0) {
        await groupsAPI.addMembers(selectedGroup.id, addMemberIds);
      }
      const originalByUser = {};
      (selectedGroupDetails?.members || []).forEach(m => { originalByUser[m.user_id] = m; });
      for (const m of editMembers) {
        const orig = originalByUser[m.user_id];
        if (orig && orig.role !== m.role && (m.role === 'admin' || m.role === 'member')) {
          await groupsAPI.setMemberRole(selectedGroup.id, m.user_id, m.role);
        }
      }
      const keepIds = new Set(editMembers.map(m => m.user_id));
      for (const m of (selectedGroupDetails?.members || [])) {
        if (!keepIds.has(m.user_id) && m.role !== 'owner') {
          try { await groupsAPI.removeMember(selectedGroup.id, m.user_id); } catch (_) {}
        }
      }
      const res = await groupsAPI.getDetails(selectedGroup.id);
      setSelectedGroupDetails(res.data || null);
      await fetchGroups();
      setEditing(false);
    } catch (err) {
      console.error('Failed to save group edits', err);
    }
  };

  const handleInvitationResponse = async (invId, status) => {
    try {
      await groupsAPI.respondInvitation(invId, status);
      await fetchInvitations();
      if (status === 'accepted') {
        await fetchGroups();
      }
    } catch (err) {
      console.error('Failed to respond to invitation', err);
    }
  };

  const availableUsersToAdd = users.filter(u => !(editMembers || []).some(m => m.user_id === u.id));

  // Get sender initials helper
  const getSenderInitials = (senderName) => {
    if (!senderName) return '?';
    const parts = senderName.trim().split(' ');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return senderName.charAt(0).toUpperCase();
  };

  return (
    <div className="chat-page">
      <div className="chat-container">
        <div className="chat-sidebar">
          <div className="sidebar-section">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, position: 'relative' }}>
              <h3>Groups</h3>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <button
                  className="btn btn-sm"
                  data-invites-button
                  onClick={(e) => { e.stopPropagation(); setInvitesModalOpen(true); }}
                  style={{ position: 'relative', padding: '6px 10px', fontSize: 12 }}
                  title="Pending group invites"
                >
                  Invites
                  {invitations.length > 0 && (
                    <span style={{
                      marginLeft: 6,
                      background: '#ef4444',
                      color: '#fff',
                      borderRadius: 10,
                      padding: '1px 6px',
                      fontSize: 11,
                      fontWeight: 700
                    }}>{invitations.length}</span>
                  )}
                </button>
                <button className="btn btn-primary btn-sm" onClick={() => setCreating(true)}>+ New</button>
              </div>
              {/* Invites popover removed - handled via modal */}
            </div>

            {/* Groups List */}
            {groups.length === 0 ? (
              <p className="empty-state-text">No groups yet</p>
            ) : (
              <div className="user-list">
                {groups.map(g => (
                  <div 
                    key={g.id} 
                    className={`conversation-item ${selectedGroup?.id === g.id ? 'active' : ''}`} 
                    onClick={() => setSelectedGroup(g)}
                  >
                    <div className="conversation-avatar">{g.name?.charAt(0)?.toUpperCase()}</div>
                    <div className="conversation-info">
                      <div className="conversation-name">{g.name}</div>
                      <div className="conversation-preview">{g.member_count || 0} members</div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Edit Group Section */}
            {editing && selectedGroupDetails && (
              <div style={{ marginTop: 16, borderTop: '1px solid var(--border-color)', paddingTop: 16 }}>
                <h4 style={{ margin: '0 0 8px', fontSize: 14 }}>Edit Group</h4>
                <label className="form-label" style={{ fontSize: 12 }}>Name</label>
                <input className="form-input" value={editName} onChange={(e) => setEditName(e.target.value)} style={{ fontSize: 13 }} />
                <div style={{ marginTop: 10 }}>
                  <label className="form-label" style={{ fontSize: 12 }}>Members</label>
                  <div style={{ maxHeight: 120, overflowY: 'auto', border: '1px solid var(--border-color)', borderRadius: 6, padding: 6 }}>
                    {(editMembers || []).map(m => (
                      <div key={m.user_id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, padding: '4px 2px' }}>
                        <div>
                          <strong style={{ fontSize: 12 }}>{m.user_name}</strong>
                          <div style={{ fontSize: 11, color: '#666' }}>Role: {m.role}</div>
                        </div>
                        <div style={{ display: 'flex', gap: 6 }}>
                          {m.role !== 'owner' && (
                            <select
                              className="form-input"
                              value={m.role}
                              onChange={(e) => {
                                const value = e.target.value;
                                setEditMembers(prev => prev.map(x => x.user_id === m.user_id ? { ...x, role: value } : x));
                              }}
                              style={{ fontSize: 11, padding: '2px 4px' }}
                            >
                              <option value="member">Member</option>
                              <option value="admin">Admin</option>
                            </select>
                          )}
                          {m.role !== 'owner' && (
                            <button
                              type="button"
                              className="btn btn-sm"
                              onClick={() => setEditMembers(prev => prev.filter(x => x.user_id !== m.user_id))}
                              style={{ fontSize: 11, padding: '4px 8px' }}
                            >
                              Remove
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div style={{ marginTop: 10 }}>
                  <label className="form-label" style={{ fontSize: 12 }}>Add Members</label>
                  <div style={{ maxHeight: 100, overflowY: 'auto', border: '1px solid var(--border-color)', borderRadius: 6, padding: 6 }}>
                    {availableUsersToAdd.map(u => (
                      <label key={u.id} style={{ display: 'flex', gap: 8, alignItems: 'center', padding: '4px 2px' }}>
                        <input
                          type="checkbox"
                          checked={addMemberIds.includes(u.id)}
                          onChange={(e) => setAddMemberIds(prev => e.target.checked ? [...prev, u.id] : prev.filter(id => id !== u.id))}
                        />
                        <span style={{ fontSize: 12 }}>{u.name} ({u.email})</span>
                      </label>
                    ))}
                    {availableUsersToAdd.length === 0 && (
                      <div style={{ color: '#666', fontSize: 11 }}>No additional users</div>
                    )}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                  <button className="btn btn-primary btn-sm" onClick={saveEdit} style={{ fontSize: 12, padding: '6px 12px' }}>Save</button>
                  <button className="btn btn-sm" onClick={() => setEditing(false)} style={{ fontSize: 12, padding: '6px 12px' }}>Cancel</button>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="chat-main">
          {selectedGroup ? (
            <>
              <div className="chat-header-bar">
                <div className="chat-user-info">
                  <div className="chat-avatar">{selectedGroup.name?.charAt(0)?.toUpperCase()}</div>
                  <div>
                    <div className="chat-user-name">{selectedGroup.name}</div>
                    <div className="chat-user-status">{activeCount} active</div>
                  </div>
                </div>
                {(() => {
                  const myId = getCurrentUserId();
                  const me = (selectedGroupDetails?.members || []).find(m => m.user_id === myId);
                  return me?.role === 'owner' ? (
                    <button className="btn btn-sm" onClick={openEdit} style={{ fontSize: 12, marginLeft: 'auto' }}>Edit</button>
                  ) : null;
                })()}
              </div>
              <div className="messages-container" ref={messagesContainerRef}>
                <div className="messages-list">
                  {messages.map(m => {
                    const isSent = m.sender_id === getCurrentUserId();
                    const senderInitials = getSenderInitials(m.sender_name);
                    return (
                      <div
                        key={m.id}
                        className={`message ${isSent ? 'sent' : 'received'}`}
                        style={{ marginBottom: '8px' }}
                        onContextMenu={(e) => openContextPopover(e, m)}
                        onClick={(e) => {
                          if (!e.target.closest('.message-reactions')) {
                            openContextPopover(e, m);
                          }
                        }}
                      >
                        {!isSent && (
                          <div className="message-sender-avatar">
                            {senderInitials}
                          </div>
                        )}
                        <div className="message-content">
                          {!isSent && (
                            <div className="message-sender-name">{m.sender_name}</div>
                          )}
                          {m.reply_to && (
                            <div className="message-reply-preview">
                              <div className="reply-indicator"></div>
                              <div className="reply-content">
                                <div className="reply-sender">{m.reply_to.sender_name}</div>
                                <div className="reply-text">{m.reply_to.content}</div>
                              </div>
                            </div>
                          )}
                          {editingMessageId === m.id ? (
                            <div className="message-editing">
                              <input
                                className="message-edit-input"
                                value={editingContent}
                                onChange={(e) => setEditingContent(e.target.value)}
                              />
                              <div className="message-edit-actions">
                                <button type="button" className="btn-small" onClick={() => submitEditMessage(m)}>Save</button>
                                <button type="button" className="btn-small secondary" onClick={() => { setEditingMessageId(null); setEditingContent(''); }}>Cancel</button>
                              </div>
                            </div>
                          ) : (
                            (() => {
                              let rendered = null;
                              if (m.is_deleted) {
                                return (
                                  <div className="message-deleted">This message was deleted</div>
                                );
                              }
                              try {
                                const data = typeof m.content === 'string' ? JSON.parse(m.content) : m.content;
                                if (data && data.type === 'file') {
                                  const sizeKb = Math.max(1, Math.round((data.size || 0) / 1024));
                                  const url = previewUrls[m.id];
                                  const ext = (data.name || '').split('.').pop().toLowerCase();
                                  const isImage = ['jpg','jpeg','png','gif','webp'].includes(ext);
                                  const isVideo = ['mp4','webm','ogg','mov'].includes(ext);
                                  const isPdf = ext === 'pdf';
                                  rendered = (
                                    <div className="message-text">
                                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                                        <button type="button" className="linklike" onClick={() => handleDownloadAttachment(m, data.name)}>
                                          <span style={{ marginRight: 6, display: 'inline-flex', verticalAlign: 'middle' }}><FiPaperclip /></span>
                                          {data.name || 'Download file'} ({sizeKb} KB)
                                        </button>
                                        {(isImage || isVideo || isPdf) && (
                                          <>
                                            {!url && (
                                              <button type="button" className="btn-small secondary" onClick={() => handlePreviewAttachment(m, data.name)}>Preview</button>
                                            )}
                                            {url && isImage && (
                                              <img src={url} alt={data.name} style={{ maxWidth: 260, borderRadius: 8, cursor: 'zoom-in' }} onClick={() => {
                                                const imgs = messages.flatMap(msg => {
                                                  try {
                                                    const d = typeof msg.content === 'string' ? JSON.parse(msg.content) : msg.content;
                                                    const e = (d?.name || '').split('.').pop().toLowerCase();
                                                    if (d && d.type === 'file' && ['jpg','jpeg','png','gif','webp'].includes(e)) {
                                                      const purl = previewUrls[msg.id];
                                                      if (purl) return [{ id: msg.id, name: d.name, url: purl }];
                                                    }
                                                  } catch (err) {}
                                                  return [];
                                                });
                                                setGalleryImages(imgs);
                                                const idx = imgs.findIndex(i => i.id === m.id);
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
                                    {m.content}
                                    {m.is_edited && <span className="message-edited-indicator"> (edited)</span>}
                                  </div>
                                );
                              }
                              return rendered;
                            })()
                          )}
                          <div className="message-footer">
                            <div className="message-time-status">
                              <span className="message-time">
                                {new Date(m.created_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })}
                              </span>
                            </div>
                          </div>
                          {m.reactions && m.reactions.length > 0 && (
                            <div className="message-reactions">
                              {Object.entries(groupReactions(m.reactions)).map(([emoji, reactionList]) => {
                                const userReacted = reactionList.some(r => r.user_id === getCurrentUserId());
                                const userReaction = reactionList.find(r => r.user_id === getCurrentUserId());
                                return (
                                  <button
                                    key={emoji}
                                    type="button"
                                    className={`reaction-bubble ${userReacted ? 'user-reacted' : ''}`}
                                    onClick={() => {
                                      if (userReacted && userReaction) {
                                        handleRemoveReaction(m.id, userReaction.id);
                                      } else {
                                        handleAddReaction(m.id, emoji);
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
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                  <div ref={messagesEndRef} />
                </div>
                {typing && typing.length > 0 && (
                  <div style={{ padding: '6px 12px', color: '#666', fontSize: 12 }}>
                    {typing.map(t => t.name).join(', ')} typing...
                  </div>
                )}
              </div>
              <form className="message-input-form" onSubmit={send}
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
                    const replyMsg = messages.find(msg => msg.id === replyingTo.id);
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
                    value={input}
                    onChange={(e) => { setInput(e.target.value); notifyTyping(); }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        send(e);
                      }
                    }}
                    rows={1}
                  />
                  <div className="input-right-controls">
                    <button type="submit" className="send-button" disabled={!input.trim() && attachmentFiles.length === 0}>
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
                </form>
            </>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#666' }}>
              Select a group or create a new one
            </div>
          )}
        </div>
      </div>

      {/* Gallery Overlay */}
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

      {/* WhatsApp-style context popover near the clicked message */}
      {contextPopover && (
        <div
          className="message-context-popover"
          style={{ top: contextPopover.y, left: contextPopover.x, position: 'fixed' }}
        >
          <div className="popover-reactions">
            {['👍','❤️','😂','😮','😢','🙏'].map(emo => {
              const hasReaction = contextPopover.msg.reactions?.some(r => {
                const normalized = normalizeEmoji(r.emoji);
                return normalized === emo && r.user_id === getCurrentUserId();
              });
              return (
                <button
                  key={emo}
                  type="button"
                  className={`reaction-btn ${hasReaction ? 'active' : ''}`}
                  onClick={() => {
                    if (hasReaction) {
                      const userReaction = contextPopover.msg.reactions.find(r => {
                        const normalized = normalizeEmoji(r.emoji);
                        return normalized === emo && r.user_id === getCurrentUserId();
                      });
                      if (userReaction) handleRemoveReaction(contextPopover.msg.id, userReaction.id);
                    } else {
                      handleAddReaction(contextPopover.msg.id, emo);
                    }
                    setContextPopover(null);
                  }}
                  title={emo}
                >
                  {emo}
                </button>
              );
            })}
          </div>
          <div className="popover-actions">
            <button type="button" onClick={() => { setReplyingTo(contextPopover.msg); setContextPopover(null); }}>Reply</button>
            {contextPopover.msg.sender_id === getCurrentUserId() && (
              <button type="button" disabled={!canModifyMessage(contextPopover.msg) || contextPopover.msg.is_deleted} onClick={() => { startEditMessage(contextPopover.msg); setContextPopover(null); }}>Edit</button>
            )}
            <button type="button" onClick={() => { deleteForMe(contextPopover.msg); setContextPopover(null); }}>Delete for me</button>
            {contextPopover.msg.sender_id === getCurrentUserId() && (
              <button type="button" disabled={!canModifyMessage(contextPopover.msg) || contextPopover.msg.is_deleted} onClick={() => { deleteForEveryone(contextPopover.msg); setContextPopover(null); }}>Delete for everyone</button>
            )}
          </div>
        </div>
      )}

      {/* Invitations Modal */}
      {invitesModalOpen && (
        <div className="modal-overlay" onClick={() => setInvitesModalOpen(false)} style={{ 
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ 
            background: 'white',
            borderRadius: 8,
            padding: 0,
            maxWidth: 600,
            width: '92%',
            maxHeight: '90vh',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
          }}>
            <div className="modal-header" style={{ 
              padding: '16px 20px',
              borderBottom: '1px solid #e5e7eb',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <h3 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>Pending Invitations</h3>
              <button 
                className="modal-close" 
                onClick={() => setInvitesModalOpen(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: 24,
                  cursor: 'pointer',
                  color: '#666',
                  padding: 0,
                  width: 24,
                  height: 24,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                ×
              </button>
            </div>
            <div className="modal-body" style={{ padding: 20, overflowY: 'auto', flex: 1 }}>
              {invitations.length === 0 ? (
                <div style={{ color: '#6b7280', fontSize: 14 }}>No pending invitations.</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {invitations.map(inv => (
                    <div key={inv.id} style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      alignItems: 'center', 
                      padding: '10px 12px',
                      background: '#f9fafb',
                      borderRadius: 6,
                      border: '1px solid #e5e7eb'
                    }}>
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontWeight: 600, fontSize: 14, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {inv.group_name || 'Group'}
                        </div>
                        <div style={{ color: '#6b7280', fontSize: 12 }}>
                          {new Date(inv.created_at).toLocaleDateString()} {new Date(inv.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: 8, marginLeft: 8, flexShrink: 0 }}>
                        <button 
                          className="btn btn-success btn-sm" 
                          onClick={() => handleInvitationResponse(inv.id, 'accepted')}
                          style={{ fontSize: 12, padding: '6px 10px' }}
                        >
                          Accept
                        </button>
                        <button 
                          className="btn btn-danger btn-sm" 
                          onClick={() => handleInvitationResponse(inv.id, 'rejected')}
                          style={{ fontSize: 12, padding: '6px 10px' }}
                        >
                          Reject
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="modal-footer" style={{ 
              padding: '16px 20px',
              borderTop: '1px solid #e5e7eb',
              display: 'flex',
              justifyContent: 'flex-end',
              gap: 8
            }}>
              <button 
                type="button"
                className="btn btn-secondary" 
                onClick={() => setInvitesModalOpen(false)}
                style={{ padding: '8px 16px' }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Group Modal */}
      {creating && (
        <div className="modal-overlay" onClick={() => setCreating(false)} style={{ 
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ 
            background: 'white',
            borderRadius: 8,
            padding: 0,
            maxWidth: 500,
            width: '90%',
            maxHeight: '90vh',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
          }}>
            <div className="modal-header" style={{ 
              padding: '16px 20px',
              borderBottom: '1px solid #e5e7eb',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <h3 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>Create Group</h3>
              <button 
                className="modal-close" 
                onClick={() => setCreating(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: 24,
                  cursor: 'pointer',
                  color: '#666',
                  padding: 0,
                  width: 24,
                  height: 24,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                ×
              </button>
            </div>
            <form onSubmit={createGroup}>
              <div className="modal-body" style={{ padding: '20px', overflowY: 'auto', flex: 1 }}>
                <div className="form-group">
                  <label className="form-label">Group name</label>
                  <input 
                    className="form-input" 
                    placeholder="Enter group name" 
                    value={newGroupName} 
                    onChange={(e) => setNewGroupName(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group" style={{ marginTop: 16 }}>
                  <label className="form-label">Select Members to Invite</label>
                  <div style={{ 
                    maxHeight: 200, 
                    overflowY: 'auto', 
                    border: '1px solid var(--border-color)', 
                    borderRadius: 6, 
                    padding: 8,
                    background: '#f9fafb'
                  }}>
                    {users.length === 0 ? (
                      <div style={{ color: '#666', fontSize: 13, padding: 8 }}>No users available</div>
                    ) : (
                      users.map(u => (
                        <label 
                          key={u.id} 
                          style={{ 
                            display: 'flex', 
                            gap: 8, 
                            alignItems: 'center', 
                            padding: '6px 4px',
                            cursor: 'pointer'
                          }}
                        >
                          <input 
                            type="checkbox" 
                            checked={selectedMembers.includes(u.id)} 
                            onChange={(e) => {
                              setSelectedMembers(prev => e.target.checked ? [...prev, u.id] : prev.filter(id => id !== u.id));
                            }} 
                          />
                          <span style={{ fontSize: 13 }}>{u.name} ({u.email})</span>
                        </label>
                      ))
                    )}
                  </div>
                </div>
              </div>
              <div className="modal-footer" style={{ 
                padding: '16px 20px',
                borderTop: '1px solid #e5e7eb',
                display: 'flex',
                justifyContent: 'flex-end',
                gap: 8
              }}>
                <button 
                  type="button"
                  className="btn btn-secondary" 
                  onClick={() => setCreating(false)}
                  style={{ padding: '8px 16px' }}
                >
                  Cancel
                </button>
                <button 
                  type="submit"
                  className="btn btn-primary" 
                  disabled={!newGroupName.trim()}
                  style={{ padding: '8px 16px' }}
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Groups;
