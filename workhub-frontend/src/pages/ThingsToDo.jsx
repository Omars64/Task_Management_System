import React, { useState, useEffect } from 'react';
import { FiPlus, FiTrash2, FiCheck, FiCircle } from 'react-icons/fi';

const ThingsToDo = () => {
  const [items, setItems] = useState([]);
  const [newItem, setNewItem] = useState('');
  const [filter, setFilter] = useState('all'); // all, active, completed

  // Load items from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('thingsToDo');
    if (saved) {
      try {
        setItems(JSON.parse(saved));
      } catch (error) {
        console.error('Failed to load things to do:', error);
      }
    }
  }, []);

  // Save items to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('thingsToDo', JSON.stringify(items));
  }, [items]);

  const addItem = (e) => {
    e.preventDefault();
    if (newItem.trim()) {
      const item = {
        id: Date.now(),
        text: newItem.trim(),
        completed: false,
        createdAt: new Date().toISOString()
      };
      setItems([item, ...items]);
      setNewItem('');
    }
  };

  const toggleItem = (id) => {
    setItems(items.map(item =>
      item.id === id ? { ...item, completed: !item.completed } : item
    ));
  };

  const deleteItem = (id) => {
    setItems(items.filter(item => item.id !== id));
  };

  const clearCompleted = () => {
    setItems(items.filter(item => !item.completed));
  };

  const filteredItems = items.filter(item => {
    if (filter === 'active') return !item.completed;
    if (filter === 'completed') return item.completed;
    return true;
  });

  const activeCount = items.filter(item => !item.completed).length;
  const completedCount = items.filter(item => item.completed).length;

  return (
    <div>
      <div className="page-header">
        <h1>Things to do</h1>
        <p style={{ color: 'var(--text-light)', fontSize: '0.95rem', marginTop: '8px' }}>
          Your personal quick notes and checklist
        </p>
      </div>

      <div className="card" style={{ maxWidth: '800px' }}>
        {/* Add new item form */}
        <form onSubmit={addItem} style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', gap: '12px' }}>
            <input
              type="text"
              className="form-input"
              placeholder="What do you need to do?"
              value={newItem}
              onChange={(e) => setNewItem(e.target.value)}
              style={{ flex: 1 }}
              maxLength={200}
            />
            <button
              type="submit"
              className="btn btn-primary"
              disabled={!newItem.trim()}
              style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
            >
              <FiPlus /> Add
            </button>
          </div>
          {newItem && (
            <div style={{ fontSize: '0.875rem', color: 'var(--text-light)', marginTop: '4px' }}>
              {newItem.length} / 200 characters
            </div>
          )}
        </form>

        {/* Filter tabs */}
        <div style={{ 
          display: 'flex', 
          gap: '16px', 
          borderBottom: '1px solid var(--border-color)', 
          marginBottom: '20px' 
        }}>
          <button
            onClick={() => setFilter('all')}
            style={{
              padding: '8px 12px',
              background: 'none',
              border: 'none',
              borderBottom: filter === 'all' ? '2px solid var(--primary-color)' : 'none',
              color: filter === 'all' ? 'var(--primary-color)' : 'var(--text-light)',
              cursor: 'pointer',
              fontWeight: 500,
              fontSize: '0.95rem'
            }}
          >
            All ({items.length})
          </button>
          <button
            onClick={() => setFilter('active')}
            style={{
              padding: '8px 12px',
              background: 'none',
              border: 'none',
              borderBottom: filter === 'active' ? '2px solid var(--primary-color)' : 'none',
              color: filter === 'active' ? 'var(--primary-color)' : 'var(--text-light)',
              cursor: 'pointer',
              fontWeight: 500,
              fontSize: '0.95rem'
            }}
          >
            Active ({activeCount})
          </button>
          <button
            onClick={() => setFilter('completed')}
            style={{
              padding: '8px 12px',
              background: 'none',
              border: 'none',
              borderBottom: filter === 'completed' ? '2px solid var(--primary-color)' : 'none',
              color: filter === 'completed' ? 'var(--primary-color)' : 'var(--text-light)',
              cursor: 'pointer',
              fontWeight: 500,
              fontSize: '0.95rem'
            }}
          >
            Completed ({completedCount})
          </button>
        </div>

        {/* Items list */}
        {filteredItems.length === 0 ? (
          <div style={{ 
            textAlign: 'center', 
            padding: '48px 20px', 
            color: 'var(--text-light)' 
          }}>
            {filter === 'all' && (
              <>
                <FiCircle size={48} style={{ opacity: 0.3, marginBottom: '16px' }} />
                <p>No items yet. Add your first thing to do above!</p>
              </>
            )}
            {filter === 'active' && <p>No active items. Great job! 🎉</p>}
            {filter === 'completed' && <p>No completed items yet.</p>}
          </div>
        ) : (
          <>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {filteredItems.map(item => (
                <div
                  key={item.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '12px',
                    backgroundColor: item.completed ? 'var(--background-light)' : 'transparent',
                    borderRadius: '8px',
                    border: '1px solid var(--border-color)',
                    transition: 'all 0.2s'
                  }}
                >
                  <button
                    onClick={() => toggleItem(item.id)}
                    style={{
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      padding: '4px',
                      display: 'flex',
                      alignItems: 'center',
                      color: item.completed ? 'var(--success-color)' : 'var(--text-light)'
                    }}
                    title={item.completed ? 'Mark as active' : 'Mark as completed'}
                  >
                    {item.completed ? <FiCheck size={20} /> : <FiCircle size={20} />}
                  </button>
                  
                  <div style={{ flex: 1 }}>
                    <p style={{
                      margin: 0,
                      color: item.completed ? 'var(--text-light)' : 'var(--text-color)',
                      textDecoration: item.completed ? 'line-through' : 'none',
                      wordBreak: 'break-word'
                    }}>
                      {item.text}
                    </p>
                    <p style={{
                      margin: '4px 0 0 0',
                      fontSize: '0.8rem',
                      color: 'var(--text-light)'
                    }}>
                      {new Date(item.createdAt).toLocaleDateString()} at {new Date(item.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                  
                  <button
                    onClick={() => deleteItem(item.id)}
                    style={{
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      padding: '4px',
                      display: 'flex',
                      alignItems: 'center',
                      color: 'var(--danger-color)',
                      opacity: 0.6
                    }}
                    title="Delete item"
                    onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
                    onMouseLeave={(e) => e.currentTarget.style.opacity = '0.6'}
                  >
                    <FiTrash2 size={18} />
                  </button>
                </div>
              ))}
            </div>

            {/* Footer actions */}
            {completedCount > 0 && (
              <div style={{ 
                marginTop: '20px', 
                paddingTop: '20px', 
                borderTop: '1px solid var(--border-color)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <span style={{ color: 'var(--text-light)', fontSize: '0.9rem' }}>
                  {completedCount} completed item{completedCount !== 1 ? 's' : ''}
                </span>
                <button
                  onClick={clearCompleted}
                  className="btn"
                  style={{
                    fontSize: '0.9rem',
                    padding: '6px 12px'
                  }}
                >
                  Clear Completed
                </button>
              </div>
            )}
          </>
        )}
      </div>

      <style jsx>{`
        .btn:hover {
          opacity: 0.9;
        }
        
        .btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  );
};

export default ThingsToDo;

