import { useEffect, useRef, useState } from 'react';
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
  const [editMembers, setEditMembers] = useState([]); // [{user_id, role, user_name}]
  const [addMemberIds, setAddMemberIds] = useState([]);
  const pollRef = useRef(null);

  const getCurrentUserId = () => {
    try {
      const token = localStorage.getItem('token');
      const payload = JSON.parse(atob((token || '').split('.')[1] || 'e30='));
      return payload?.sub;
    } catch (_) {
      return null;
    }
  };

  useEffect(() => {
    fetchGroups();
    fetchUsers();
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

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
      } catch (_) {}
    };
    load();
    pollRef.current = setInterval(load, 6000);
    return () => pollRef.current && clearInterval(pollRef.current);
  }, [selectedGroup?.id]);

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

  const createGroup = async (e) => {
    e.preventDefault();
    if (!newGroupName.trim()) return;
    try {
      const res = await groupsAPI.create(newGroupName.trim(), selectedMembers);
      setCreating(false);
      setNewGroupName('');
      setSelectedMembers([]);
      await fetchGroups();
      setSelectedGroup(res.data);
    } catch (err) {
      console.error('Create group failed', err);
    }
  };

  const send = async () => {
    const content = input.trim();
    if (!content || !selectedGroup) return;
    try {
      await groupsAPI.sendMessage(selectedGroup.id, content, null);
      setInput('');
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
      // apply role updates sequentially
      const originalByUser = {};
      (selectedGroupDetails?.members || []).forEach(m => { originalByUser[m.user_id] = m; });
      for (const m of editMembers) {
        const orig = originalByUser[m.user_id];
        if (orig && orig.role !== m.role && (m.role === 'admin' || m.role === 'member')) {
          await groupsAPI.setMemberRole(selectedGroup.id, m.user_id, m.role);
        }
      }
      // removals: members missing from editMembers list
      const keepIds = new Set(editMembers.map(m => m.user_id));
      for (const m of (selectedGroupDetails?.members || [])) {
        if (!keepIds.has(m.user_id) && m.role !== 'owner') {
          try { await groupsAPI.removeMember(selectedGroup.id, m.user_id); } catch (_) {}
        }
      }
      // reload details and list
      const res = await groupsAPI.getDetails(selectedGroup.id);
      setSelectedGroupDetails(res.data || null);
      await fetchGroups();
      setEditing(false);
    } catch (err) {
      console.error('Failed to save group edits', err);
    }
  };

  const availableUsersToAdd = users.filter(u => !(editMembers || []).some(m => m.user_id === u.id));

  return (
    <div className="chat-page">
      <div className="chat-sidebar">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <h3 style={{ margin: 0 }}>Groups</h3>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-primary" onClick={() => setCreating(true)}>+ New</button>
            {selectedGroup && isGroupAdmin() && (
              <button className="btn" onClick={openEdit}>Edit</button>
            )}
          </div>
        </div>
        <div className="user-list">
          {groups.map(g => (
            <div key={g.id} className={`user-item ${selectedGroup?.id === g.id ? 'active' : ''}`} onClick={() => setSelectedGroup(g)}>
              <div className="user-avatar">{g.name?.charAt(0)?.toUpperCase()}</div>
              <div className="user-info">
                <div className="user-name">{g.name}</div>
                <div className="user-email">{g.member_count || 0} members</div>
              </div>
            </div>
          ))}
        </div>

        {creating && (
          <form onSubmit={createGroup} style={{ marginTop: 12 }}>
            <input className="form-input" placeholder="Group name" value={newGroupName} onChange={(e) => setNewGroupName(e.target.value)} />
            <div style={{ maxHeight: 160, overflowY: 'auto', marginTop: 8, border: '1px solid var(--border-color)', borderRadius: 6, padding: 6 }}>
              {users.map(u => (
                <label key={u.id} style={{ display: 'flex', gap: 8, alignItems: 'center', padding: '4px 2px' }}>
                  <input type="checkbox" checked={selectedMembers.includes(u.id)} onChange={(e) => {
                    setSelectedMembers(prev => e.target.checked ? [...prev, u.id] : prev.filter(id => id !== u.id));
                  }} />
                  <span>{u.name} ({u.email})</span>
                </label>
              ))}
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
              <button type="submit" className="btn btn-primary">Create</button>
              <button type="button" className="btn" onClick={() => setCreating(false)}>Cancel</button>
            </div>
          </form>
        )}

        {editing && selectedGroupDetails && (
          <div style={{ marginTop: 12, borderTop: '1px solid var(--border-color)', paddingTop: 12 }}>
            <h4 style={{ margin: '0 0 8px' }}>Edit Group</h4>
            <label className="form-label">Name</label>
            <input className="form-input" value={editName} onChange={(e) => setEditName(e.target.value)} />

            <div style={{ marginTop: 10 }}>
              <label className="form-label">Members</label>
              <div style={{ maxHeight: 180, overflowY: 'auto', border: '1px solid var(--border-color)', borderRadius: 6, padding: 6 }}>
                {(editMembers || []).map(m => (
                  <div key={m.user_id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, padding: '4px 2px' }}>
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <strong>{m.user_name}</strong>
                      <span style={{ fontSize: 12, color: '#666' }}>Role: {m.role}</span>
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
                        >
                          <option value="member">Member</option>
                          <option value="admin">Admin</option>
                        </select>
                      )}
                      {m.role !== 'owner' && (
                        <button
                          type="button"
                          className="btn"
                          onClick={() => setEditMembers(prev => prev.filter(x => x.user_id !== m.user_id))}
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
              <label className="form-label">Add Members</label>
              <div style={{ maxHeight: 140, overflowY: 'auto', border: '1px solid var(--border-color)', borderRadius: 6, padding: 6 }}>
                {availableUsersToAdd.map(u => (
                  <label key={u.id} style={{ display: 'flex', gap: 8, alignItems: 'center', padding: '4px 2px' }}>
                    <input
                      type="checkbox"
                      checked={addMemberIds.includes(u.id)}
                      onChange={(e) => setAddMemberIds(prev => e.target.checked ? [...prev, u.id] : prev.filter(id => id !== u.id))}
                    />
                    <span>{u.name} ({u.email})</span>
                  </label>
                ))}
                {availableUsersToAdd.length === 0 && (
                  <div style={{ color: '#666', fontSize: 12 }}>No additional users</div>
                )}
              </div>
            </div>

            <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
              <button className="btn btn-primary" onClick={saveEdit}>Save</button>
              <button className="btn" onClick={() => setEditing(false)}>Cancel</button>
            </div>
          </div>
        )}
      </div>

      <div className="chat-main">
        {selectedGroup ? (
          <div className="messages-container">
            <div className="messages-list">
              {messages.map(m => (
                <div key={m.id} className={`message ${m.sender_id === (JSON.parse(atob(localStorage.getItem('token')?.split('.')[1] || 'e30='))?.sub) ? 'sent' : 'received'}`}>
                  <div className="message-content">
                    <div className="message-text">{m.content}</div>
                    <div className="message-footer">
                      <span className="message-time">{new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            {typing && typing.length > 0 && (
              <div style={{ padding: '6px 12px', color: '#666' }}>
                {typing.map(t => t.name).join(', ')} typing...
              </div>
            )}
            <div className="chat-input">
              <input
                className="chat-text-input"
                placeholder="Type a message"
                value={input}
                onChange={onInputChange}
                onKeyDown={(e) => { if (e.key === 'Enter') send(); }}
              />
              <button className="btn btn-primary" onClick={send}>Send</button>
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#666' }}>
            Select a group or create a new one
          </div>
        )}
      </div>
    </div>
  );
};

export default Groups;
