import { useEffect, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { groupsAPI, chatAPI, usersAPI } from '../services/api';
import './Chat.css';

const Groups = () => {
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
  const [replyTo, setReplyTo] = useState(null);
  const fileInputRef = useRef(null);
  const [onlineCount, setOnlineCount] = useState(0);
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const pollRef = useRef(null);
  const messagesEndRef = useRef(null);

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
    // also load group details (members/roles)
    (async () => {
      try {
        const res = await groupsAPI.getDetails(selectedGroup.id);
        const details = res.data || {};
        setSelectedGroupDetails(details);
        setEditName(details?.group?.name || '');
        setEditMembers(Array.isArray(details?.members) ? details.members : []);
        // compute online
        try {
          const members = Array.isArray(details?.members) ? details.members : [];
          const presences = await Promise.allSettled(members.map(m => chatAPI.getPresence(m.user_id)));
          const active = presences.reduce((sum, r) => (r.status === 'fulfilled' && r.value?.data?.online) ? sum + 1 : sum, 0);
          setOnlineCount(active);
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
        setTimeout(scrollToBottom, 100);
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

  const send = async () => {
    const content = input.trim();
    if (!content || !selectedGroup) return;
    try {
      await groupsAPI.sendMessage(selectedGroup.id, content, replyTo?.id || null);
      setInput('');
      setReplyTo(null);
      await groupsAPI.markRead(selectedGroup.id);
      const res = await groupsAPI.getMessages(selectedGroup.id);
      setMessages(res.data || []);
    } catch (err) {
      console.error('Send failed', err);
    }
  };

  const onInputChange = async (e) => {
    setInput(e.target.value);
    if (selectedGroup) {
      try { await groupsAPI.setTyping(selectedGroup.id, true); } catch (_) {}
    }
  };

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
  const currentUserId = getCurrentUserId();

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
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <h3>Groups</h3>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                {invitations.length > 0 && (
                  <div style={{ 
                    position: 'relative',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 4
                  }}>
                    <span style={{ 
                      position: 'absolute',
                      top: -4,
                      right: -4,
                      background: '#ef4444',
                      color: 'white',
                      borderRadius: '50%',
                      width: 18,
                      height: 18,
                      fontSize: 11,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 'bold'
                    }}>
                      {invitations.length}
                    </span>
                    <span style={{ fontSize: 12, color: '#666', fontWeight: 500 }}>PENDING</span>
                  </div>
                )}
                <button className="btn btn-primary btn-sm" onClick={() => setCreating(true)}>+ New</button>
              </div>
            </div>
            
            {/* Pending Invitations Container */}
            {invitations.length > 0 && (
              <div style={{ 
                marginBottom: 16, 
                padding: 12, 
                background: '#fff3cd', 
                border: '1px solid #ffc107', 
                borderRadius: 6 
              }}>
                <h4 style={{ margin: '0 0 8px 0', fontSize: 14, fontWeight: 600 }}>Pending Invitations</h4>
                <div style={{ maxHeight: 150, overflowY: 'auto' }}>
                  {invitations.map(inv => (
                    <div key={inv.id} style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      alignItems: 'center', 
                      padding: '6px 4px',
                      marginBottom: 4,
                      background: 'white',
                      borderRadius: 4,
                      border: '1px solid #e5e7eb'
                    }}>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontWeight: 500, fontSize: 13 }}>{inv.group_name || 'Group'}</div>
                        <div style={{ color: '#666', fontSize: 11 }}>
                          {new Date(inv.created_at).toLocaleDateString()} {new Date(inv.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: 4 }}>
                        <button 
                          className="btn btn-success btn-sm" 
                          onClick={() => handleInvitationResponse(inv.id, 'accepted')}
                          style={{ fontSize: 11, padding: '4px 8px' }}
                        >
                          Accept
                        </button>
                        <button 
                          className="btn btn-danger btn-sm" 
                          onClick={() => handleInvitationResponse(inv.id, 'rejected')}
                          style={{ fontSize: 11, padding: '4px 8px' }}
                        >
                          Reject
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

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
                    <div className="chat-user-status">{selectedGroupDetails?.members?.length || 0} members • {onlineCount} online</div>
                  </div>
                </div>
                {(() => {
                  const myId = getCurrentUserId();
                  const me = (selectedGroupDetails?.members || []).find(m => m.user_id === myId);
                  return me?.role === 'owner' ? (
                    <button className="btn btn-sm" onClick={openEdit} style={{ fontSize: 12 }}>Edit</button>
                  ) : null;
                })()}
              </div>
              <div className="messages-container">
                <div className="messages-list">
                  {messages.map(m => {
                    const isSent = m.sender_id === currentUserId;
                    const senderInitials = getSenderInitials(m.sender_name);
                    return (
                      <div key={m.id} className={`message ${isSent ? 'sent' : 'received'}`}>
                        {!isSent && (
                          <div className="message-sender-avatar" style={{
                            width: 28,
                            height: 28,
                            borderRadius: '50%',
                            background: '#68939d',
                            color: 'white',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: 11,
                            fontWeight: 600,
                            marginRight: 8,
                            flexShrink: 0
                          }}>
                            {senderInitials}
                          </div>
                        )}
                        <div className="message-content">
                          {!isSent && (
                            <div className="message-sender-name" style={{ 
                              fontSize: 12, 
                              fontWeight: 600, 
                              color: '#68939d',
                              marginBottom: 2
                            }}>
                              {m.sender_name}
                            </div>
                          )}
                          <div className="message-text">{m.content}</div>
                          <div className="message-footer">
                            <span className="message-time">
                              {new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                          </div>
                          <div className="message-actions" style={{ marginTop: 4, display: 'flex', gap: 6 }}>
                            <button className="btn btn-small secondary" onClick={() => setReplyTo(m)} style={{ fontSize: 11 }}>Reply</button>
                            {isSent ? (
                              <>
                                <button className="btn btn-small secondary" onClick={async () => {
                                  const updated = prompt('Edit message', m.content);
                                  if (updated != null) { await groupsAPI.editMessage(m.id, updated); const res = await groupsAPI.getMessages(selectedGroup.id); setMessages(res.data || []); }
                                }} style={{ fontSize: 11 }}>Edit</button>
                                <button className="btn btn-small secondary" onClick={async () => {
                                  await groupsAPI.deleteForEveryone(m.id);
                                  const res = await groupsAPI.getMessages(selectedGroup.id); setMessages(res.data || []);
                                }} style={{ fontSize: 11 }}>Delete for everyone</button>
                                <button className="btn btn-small secondary" onClick={() => groupsAPI.deleteForMe(m.id)} style={{ fontSize: 11 }}>Delete for me</button>
                              </>
                            ) : (
                              <button className="btn btn-small secondary" onClick={() => groupsAPI.deleteForMe(m.id)} style={{ fontSize: 11 }}>Delete for me</button>
                            )}
                            <div style={{ display: 'flex', gap: 4, marginLeft: 6 }}>
                              {['👍','❤️','😂','😮','🙏'].map(emo => (
                                <button key={emo} className="btn btn-small secondary" onClick={async () => {
                                  await groupsAPI.addReaction(m.id, emo);
                                  const res = await groupsAPI.getMessages(selectedGroup.id); setMessages(res.data || []);
                                }} style={{ fontSize: 12, padding: '2px 6px' }}>{emo}</button>
                              ))}
                            </div>
                          </div>
                          {Array.isArray(m.reactions) && m.reactions.length > 0 && (
                            <div className="message-reactions" style={{ marginTop: 6, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                              {m.reactions.map(r => (
                                <span key={r.id} className="reaction-bubble" style={{ background: '#f3f4f6', borderRadius: 12, padding: '2px 6px', fontSize: 12 }}>
                                  {r.emoji} {r.user_name && r.user_name.split(' ')[0]}
                                </span>
                              ))}
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
                <div className="message-input-form">
                  <button className="send-button" title="Attach file" type="button" onClick={() => fileInputRef.current?.click()}>📎</button>
                  <input ref={fileInputRef} type="file" style={{ display: 'none' }} onChange={async (e) => {
                    const file = e.target.files?.[0];
                    if (!file || !selectedGroup) return;
                    try {
                      await groupsAPI.uploadAttachment(selectedGroup.id, file);
                      const res = await groupsAPI.getMessages(selectedGroup.id);
                      setMessages(res.data || []);
                    } catch (_) {}
                  }} />
                  <button className="send-button" title="Emoji" type="button" onClick={() => setInput(prev => prev + ' 😊')}>😊</button>
                  <input
                    className="message-input"
                    placeholder={replyTo ? `Replying to ${replyTo.sender_name}...` : 'Type a message...'}
                    value={input}
                    onChange={onInputChange}
                    onKeyDown={(e) => { if (e.key === 'Enter') send(); }}
                  />
                  <button className="send-button" title="Send" type="button" onClick={send}>➤</button>
                </div>
              </div>
            </>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#666' }}>
              Select a group or create a new one
            </div>
          )}
        </div>
      </div>

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
