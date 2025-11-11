import { useEffect, useRef, useState } from 'react';
import { groupsAPI, chatAPI, usersAPI } from '../services/api';
import './Chat.css';

const Groups = () => {
  const [groups, setGroups] = useState([]);
  const [users, setUsers] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [creating, setCreating] = useState(false);
  const [newGroupName, setNewGroupName] = useState('');
  const [selectedMembers, setSelectedMembers] = useState([]);
  const [typing, setTyping] = useState([]);
  const pollRef = useRef(null);

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

  return (
    <div className="chat-page">
      <div className="chat-sidebar">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <h3 style={{ margin: 0 }}>Groups</h3>
          <button className="btn btn-primary" onClick={() => setCreating(true)}>+ New</button>
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
