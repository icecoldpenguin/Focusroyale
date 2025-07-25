import React, { useState, useEffect, createContext, useContext } from "react";
import "./App.css";
import axios from "axios";
import ThreeBackground from "./ThreeBackground";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
} from 'chart.js';
import { Bar, Pie, Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement
);

// Theme Context
const ThemeContext = createContext();
const useTheme = () => useContext(ThemeContext);

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL || 'https://successful-contentment-production.up.railway.app';
const API = `${BACKEND_URL}/api`;

console.log('Backend URL:', BACKEND_URL);
console.log('API URL:', API);

// Theme Provider Component
const ThemeProvider = ({ children }) => {
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('theme');
    return saved ? saved === 'dark' : false;
  });

  const toggleTheme = () => {
    setDarkMode(prev => {
      const newMode = !prev;
      localStorage.setItem('theme', newMode ? 'dark' : 'light');
      return newMode;
    });
  };

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', darkMode ? 'dark' : 'light');
  }, [darkMode]);

  return (
    <ThemeContext.Provider value={{ darkMode, toggleTheme }}>
      <div className={`App ${darkMode ? 'dark' : 'light'}`}>
        {children}
      </div>
    </ThemeContext.Provider>
  );
};

// Theme Toggle Component
const ThemeToggle = () => {
  const { darkMode, toggleTheme } = useTheme();
  
  return (
    <button
      onClick={toggleTheme}
      className="theme-toggle-btn btn-enhanced p-2 rounded-lg transition-all duration-300"
      style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}
      title={`Switch to ${darkMode ? 'light' : 'dark'} mode`}
    >
      {darkMode ? '☀️' : '🌙'}
    </button>
  );
};

// Floating Doodles Component
const FloatingDoodles = ({ darkMode }) => {
  const doodles = [
    { icon: '⚡', size: '2rem', top: '10%', left: '15%', delay: '0s' },
    { icon: '🎯', size: '1.5rem', top: '20%', right: '20%', delay: '2s' },
    { icon: '⭐', size: '1.8rem', top: '70%', left: '10%', delay: '4s' },
    { icon: '💎', size: '1.6rem', bottom: '15%', right: '15%', delay: '1s' },
    { icon: '🚀', size: '2.2rem', top: '50%', left: '5%', delay: '3s' },
    { icon: '🔥', size: '1.4rem', top: '80%', right: '10%', delay: '5s' },
    { icon: '💪', size: '1.7rem', top: '30%', left: '8%', delay: '6s' },
    { icon: '⚔️', size: '1.9rem', bottom: '30%', left: '20%', delay: '7s' },
    { icon: '🏆', size: '1.6rem', top: '60%', right: '25%', delay: '8s' },
    { icon: '⚡', size: '1.3rem', bottom: '50%', right: '5%', delay: '9s' },
    { icon: '🎪', size: '1.8rem', top: '15%', left: '25%', delay: '10s' },
    { icon: '🎭', size: '1.5rem', bottom: '20%', left: '8%', delay: '11s' },
    { icon: '🎨', size: '1.4rem', top: '85%', left: '30%', delay: '12s' },
    { icon: '🎲', size: '1.6rem', top: '40%', right: '8%', delay: '13s' },
    { icon: '⭐', size: '1.2rem', bottom: '60%', left: '12%', delay: '14s' },
  ];

  return (
    <>
      {doodles.map((doodle, index) => (
        <div
          key={index}
          className="floating-doodle"
          style={{
            ...doodle,
            fontSize: doodle.size,
            animationDelay: doodle.delay,
            opacity: darkMode ? 0.4 : 0.3,
          }}
        >
          {doodle.icon}
        </div>
      ))}
    </>
  );
};

// Locked Tab Component
const LockedTabContent = ({ requiredLevel }) => {
  return (
    <div className="locked-tab-content">
      <div className="locked-background"></div>
      <div className="lock-overlay">
        <div className="lock-icon">🔒</div>
        <div className="lock-text">Unlocks at level {requiredLevel}</div>
      </div>
    </div>
  );
};

// Custom User Dropdown Component for Shop
const UserDropdown = ({ item, users, currentUser, onSelectUser, selectedUserId }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  
  const availableUsers = users.filter(user => user.id !== currentUser.id);
  
  const handleUserSelect = (user) => {
    setSelectedUser(user);
    onSelectUser(user.id);
    setIsOpen(false);
  };

  useEffect(() => {
    if (selectedUserId) {
      const user = availableUsers.find(u => u.id === selectedUserId);
      setSelectedUser(user);
    }
  }, [selectedUserId, availableUsers]);

  return (
    <div className="relative mb-3">
      <div
        onClick={() => setIsOpen(!isOpen)}
        className={`custom-dropdown-trigger ${isOpen ? 'open' : ''}`}
        style={{
          backgroundColor: 'var(--bg-secondary)',
          border: '2px solid var(--border-color)',
          borderRadius: '8px',
          padding: '12px 16px',
          cursor: 'pointer',
          transition: 'all 0.3s ease',
          position: 'relative'
        }}
      >
        {selectedUser ? (
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {selectedUser.profile_picture ? (
                <img 
                  src={selectedUser.profile_picture} 
                  alt={selectedUser.username}
                  className="w-8 h-8 rounded-full object-cover"
                />
              ) : (
                <div 
                  className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
                  style={{ 
                    backgroundColor: 'var(--accent-color)', 
                    color: 'var(--bg-primary)' 
                  }}
                >
                  {selectedUser.username.charAt(0).toUpperCase()}
                </div>
              )}
              <div>
                <div className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                  {selectedUser.username}
                </div>
                <div className="text-xs flex items-center space-x-2" style={{ color: 'var(--text-muted)' }}>
                  <span>{selectedUser.credits} FC</span>
                  {selectedUser.level > 1 && (
                    <span className="bg-yellow-500 text-black px-1.5 py-0.5 rounded text-xs">
                      L{selectedUser.level}
                    </span>
                  )}
                </div>
              </div>
            </div>
            <div 
              className={`dropdown-arrow ${isOpen ? 'rotate-180' : ''}`}
              style={{ 
                transition: 'transform 0.3s ease',
                color: 'var(--text-secondary)'
              }}
            >
              ▼
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-between">
            <span style={{ color: 'var(--text-muted)' }}>Select target user</span>
            <div 
              className={`dropdown-arrow ${isOpen ? 'rotate-180' : ''}`}
              style={{ 
                transition: 'transform 0.3s ease',
                color: 'var(--text-secondary)'
              }}
            >
              ▼
            </div>
          </div>
        )}
      </div>

      {isOpen && (
        <div 
          className="custom-dropdown-menu"
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            backgroundColor: 'var(--bg-secondary)',
            border: '2px solid var(--border-color)',
            borderRadius: '8px',
            marginTop: '4px',
            zIndex: 1000,
            maxHeight: '200px',
            overflowY: 'auto',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            animation: 'slideIn 0.2s ease-out'
          }}
        >
          {availableUsers.length === 0 ? (
            <div 
              className="px-4 py-3 text-center"
              style={{ color: 'var(--text-muted)' }}
            >
              No other users available
            </div>
          ) : (
            availableUsers.map((user, index) => (
              <div
                key={user.id}
                onClick={() => handleUserSelect(user)}
                className="dropdown-item flex items-center space-x-3 px-4 py-3 cursor-pointer transition-all duration-200"
                style={{
                  borderBottom: index < availableUsers.length - 1 ? '1px solid var(--border-color)' : 'none',
                  backgroundColor: 'transparent'
                }}
                onMouseEnter={(e) => {
                  e.target.style.backgroundColor = 'var(--bg-tertiary)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.backgroundColor = 'transparent';
                }}
              >
                {user.profile_picture ? (
                  <img 
                    src={user.profile_picture} 
                    alt={user.username}
                    className="w-8 h-8 rounded-full object-cover"
                  />
                ) : (
                  <div 
                    className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
                    style={{ 
                      backgroundColor: 'var(--accent-color)', 
                      color: 'var(--bg-primary)' 
                    }}
                  >
                    {user.username.charAt(0).toUpperCase()}
                  </div>
                )}
                <div className="flex-1">
                  <div className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                    {user.username}
                  </div>
                  <div className="text-xs flex items-center space-x-2" style={{ color: 'var(--text-muted)' }}>
                    <span>{user.credits} FC</span>
                    {user.level > 1 && (
                      <span className="bg-yellow-400 text-black px-1.5 py-0.5 rounded text-xs">
                        L{user.level}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

// User Profile Modal
const UserProfileModal = ({ user, isOpen, onClose }) => {
  if (!isOpen || !user) return null;

  return (
    <div 
      className="modal-overlay fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div 
        className="modal-content card-enhanced p-6 rounded-lg max-w-md w-full mx-4 relative"
        onClick={(e) => e.stopPropagation()}
        style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)' }}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-2xl opacity-70 hover:opacity-100"
          style={{ color: 'var(--text-primary)' }}
        >
          ×
        </button>
        
        <div className="text-center mb-6">
          {user.profile_picture ? (
            <img 
              src={user.profile_picture} 
              alt={user.username}
              className="w-20 h-20 rounded-full mx-auto mb-4 object-cover"
            />
          ) : (
            <div 
              className="w-20 h-20 rounded-full mx-auto mb-4 flex items-center justify-center text-2xl font-bold"
              style={{ 
                backgroundColor: 'var(--accent-color)', 
                color: 'var(--bg-primary)' 
              }}
            >
              {user.username.charAt(0).toUpperCase()}
            </div>
          )}
          
          <h2 className="text-2xl font-bold flex items-center justify-center">
            {user.username}
            {user.level > 1 && (
              <span className="ml-2 bg-yellow-500 text-black px-2 py-1 rounded text-sm">
                L{user.level}
              </span>
            )}
          </h2>
          
          {user.bio && (
            <p className="text-sm opacity-80 mt-2">{user.bio}</p>
          )}
        </div>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="stats-item text-center p-3 rounded" style={{ backgroundColor: 'var(--bg-secondary)' }}>
              <div className="text-xl font-bold">{user.credits}</div>
              <div className="text-sm opacity-70">Focus Credits</div>
            </div>
            <div className="stats-item text-center p-3 rounded" style={{ backgroundColor: 'var(--bg-secondary)' }}>
              <div className="text-xl font-bold">{user.total_focus_time}</div>
              <div className="text-sm opacity-70">Minutes Focused</div>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="stats-item text-center p-3 rounded" style={{ backgroundColor: 'var(--bg-secondary)' }}>
              <div className="text-xl font-bold">{user.credit_rate_multiplier.toFixed(1)}x</div>
              <div className="text-sm opacity-70">Credit Rate</div>
            </div>
            <div className="stats-item text-center p-3 rounded" style={{ backgroundColor: 'var(--bg-secondary)' }}>
              <div className="text-xl font-bold">{user.completed_tasks || 0}</div>
              <div className="text-sm opacity-70">Tasks Done</div>
            </div>
          </div>
        </div>
        
        <div className="mt-6 text-center">
          <button
            onClick={onClose}
            className="btn-enhanced px-6 py-2 rounded-lg"
            style={{ backgroundColor: 'var(--accent-color)', color: 'var(--bg-primary)' }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

// User Settings Modal
const UserSettingsModal = ({ isOpen, onClose, currentUser, onUpdateUser }) => {
  const [settings, setSettings] = useState({
    username: '',
    bio: '',
    profilePicture: '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  useEffect(() => {
    if (currentUser && isOpen) {
      setSettings({
        username: currentUser.username || '',
        bio: currentUser.bio || '',
        profilePicture: currentUser.profile_picture || '',
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      });
    }
  }, [currentUser, isOpen]);

  const handleSaveSettings = async () => {
    if (settings.newPassword && settings.newPassword !== settings.confirmPassword) {
      alert('New passwords do not match');
      return;
    }

    try {
      const updateData = {
        user_id: currentUser.id,
        username: settings.username,
        bio: settings.bio,
        profile_picture: settings.profilePicture
      };

      if (settings.currentPassword && settings.newPassword) {
        updateData.current_password = settings.currentPassword;
        updateData.new_password = settings.newPassword;
      }

      const response = await axios.put(`${API}/users/update`, updateData);
      onUpdateUser(response.data.user);
      alert('Settings updated successfully!');
      onClose();
    } catch (error) {
      console.error('Failed to update settings:', error);
      alert(error.response?.data?.detail || 'Failed to update settings');
    }
  };

  if (!isOpen) return null;

  return (
    <div 
      className="modal-overlay fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div 
        className="modal-content card-enhanced p-6 rounded-lg max-w-md w-full mx-4 relative max-h-screen overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
        style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)' }}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-2xl opacity-70 hover:opacity-100"
          style={{ color: 'var(--text-primary)' }}
        >
          ×
        </button>
        
        <h2 className="text-2xl font-bold mb-6">Settings</h2>

        <div className="settings-section mb-6">
          <h3 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>Profile Information</h3>
          <input
            type="text"
            placeholder="Username"
            value={settings.username}
            onChange={(e) => setSettings(prev => ({ ...prev, username: e.target.value }))}
            className="form-input form-input-animated w-full p-3 rounded mb-4"
          />
          <input
            type="text"
            placeholder="Profile Picture URL (optional)"
            value={settings.profilePicture}
            onChange={(e) => setSettings(prev => ({ ...prev, profilePicture: e.target.value }))}
            className="form-input form-input-animated w-full p-3 rounded mb-4"
          />
          <textarea
            placeholder="Bio (optional)"
            value={settings.bio}
            onChange={(e) => setSettings(prev => ({ ...prev, bio: e.target.value }))}
            className="form-input form-input-animated w-full p-3 rounded resize-none"
            rows="3"
            maxLength="200"
          />
        </div>

        <div className="settings-section">
          <h3 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>Change Password</h3>
          <input
            type="password"
            placeholder="Current Password"
            value={settings.currentPassword}
            onChange={(e) => setSettings(prev => ({ ...prev, currentPassword: e.target.value }))}
            className="form-input form-input-animated w-full p-3 rounded mb-4"
          />
          <input
            type="password"
            placeholder="New Password"
            value={settings.newPassword}
            onChange={(e) => setSettings(prev => ({ ...prev, newPassword: e.target.value }))}
            className="form-input form-input-animated w-full p-3 rounded mb-4"
          />
          <input
            type="password"
            placeholder="Confirm New Password"
            value={settings.confirmPassword}
            onChange={(e) => setSettings(prev => ({ ...prev, confirmPassword: e.target.value }))}
            className="form-input form-input-animated w-full p-3 rounded"
          />
        </div>

        <div className="flex space-x-4 mt-6">
          <button
            onClick={handleSaveSettings}
            className="btn-enhanced flex-1 py-3 rounded-lg font-semibold"
            style={{ backgroundColor: 'var(--accent-color)', color: 'var(--bg-primary)' }}
          >
            Save Changes
          </button>
          <button
            onClick={onClose}
            className="btn-enhanced flex-1 py-3 rounded-lg font-semibold"
            style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

// Notification Container Component
const NotificationContainer = ({ notifications, onRemove }) => {
  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`notification-box p-4 rounded-lg shadow-lg transform transition-all duration-300 ease-in-out animate-slideInRight cursor-pointer min-w-[300px] max-w-[400px] ${
            notification.type === 'success' 
              ? 'bg-gradient-to-r from-green-500 to-green-600 text-white' 
              : notification.type === 'error'
              ? 'bg-gradient-to-r from-red-500 to-red-600 text-white'
              : 'bg-gradient-to-r from-blue-500 to-blue-600 text-white'
          }`}
          onClick={() => onRemove(notification.id)}
        >
          <div className="flex items-start space-x-2">
            <div className="flex-shrink-0 mt-0.5">
              {notification.type === 'success' && <span className="text-lg">✅</span>}
              {notification.type === 'error' && <span className="text-lg">❌</span>}
              {notification.type === 'info' && <span className="text-lg">ℹ️</span>}
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium leading-5">{notification.message}</p>
            </div>
            <button 
              onClick={(e) => {
                e.stopPropagation();
                onRemove(notification.id);
              }}
              className="flex-shrink-0 text-white/80 hover:text-white transition-colors"
            >
              ✕
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

function App() {
  const { darkMode } = useTheme();
  const [currentUser, setCurrentUser] = useState(null);
  const [users, setUsers] = useState([]);
  const [activeUsers, setActiveUsers] = useState([]);
  const [shopItems, setShopItems] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [weeklyTasks, setWeeklyTasks] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [focusSession, setFocusSession] = useState(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [authMode, setAuthMode] = useState('login');
  const [authForm, setAuthForm] = useState({ username: '', password: '' });
  const [newTask, setNewTask] = useState({ title: '', description: '' });
  const [newWeeklyTask, setNewWeeklyTask] = useState({ title: '', description: '', tags: [], dayOfWeek: 0 });
  const [socialRate, setSocialRate] = useState({ active_users_count: 0, social_multiplier: 1.0, credits_per_hour: 30 });
  const [selectedUser, setSelectedUser] = useState(null);
  const [showUserProfile, setShowUserProfile] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [selectedTargetUsers, setSelectedTargetUsers] = useState({}); // Track selected users for each shop item
  const [statistics, setStatistics] = useState(null);
  const [currentWeekOffset, setCurrentWeekOffset] = useState(0);
  const [wheelStatus, setWheelStatus] = useState(null);
  const [isSpinning, setIsSpinning] = useState(false);
  const [wheelResult, setWheelResult] = useState(null);
  
  // Notification system state
  const [appNotifications, setAppNotifications] = useState([]);
  
  // Timer state (for focus sessions)
  const [timer, setTimer] = useState({
    duration: 30, // default 30 minutes
    timeLeft: 30 * 60, // in seconds
    isRunning: false,
    isSet: false
  });

  // Trade requests state
  const [tradeRequests, setTradeRequests] = useState([]);

  // Notification system functions
  const showNotification = (message, type = 'info') => {
    const id = Date.now() + Math.random();
    const notification = { id, message, type };
    setAppNotifications(prev => [...prev, notification]);
    
    // Auto remove after 4 seconds
    setTimeout(() => {
      setAppNotifications(prev => prev.filter(n => n.id !== id));
    }, 4000);
  };

  const removeNotification = (id) => {
    setAppNotifications(prev => prev.filter(n => n.id !== id));
  };

  // Timer functions
  const setTimerDuration = (minutes) => {
    setTimer(prev => ({
      ...prev,
      duration: minutes,
      timeLeft: minutes * 60,
      isRunning: false,
      isSet: false
    }));
  };

  const startTimer = () => {
    setTimer(prev => ({ ...prev, isRunning: true, isSet: true }));
  };

  const pauseTimer = () => {
    setTimer(prev => ({ ...prev, isRunning: false }));
  };

  const resetTimer = () => {
    setTimer(prev => ({
      ...prev,
      timeLeft: prev.duration * 60,
      isRunning: false,
      isSet: false
    }));
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Timer countdown effect
  useEffect(() => {
    let interval = null;
    if (timer.isRunning && timer.timeLeft > 0) {
      interval = setInterval(() => {
        setTimer(prev => {
          if (prev.timeLeft <= 1) {
            // Timer finished
            // Play notification sound and show notification
            const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBWgcLbcmWwFcTCcbJOIFdQFpQyoT');
            audio.play().catch(e => console.log('Audio play failed:', e));
            
            showNotification('⏰ Timer finished! Time to take a break.', 'success');
            return { ...prev, timeLeft: 0, isRunning: false };
          }
          return { ...prev, timeLeft: prev.timeLeft - 1 };
        });
      }, 1000);
    } else if (!timer.isRunning) {
      clearInterval(interval);
    }
    return () => clearInterval(interval);
  }, [timer.isRunning, timer.timeLeft]);

  // Session Management Functions
  const saveUserSession = (user) => {
    try {
      localStorage.setItem('relvl_user', JSON.stringify(user));
      localStorage.setItem('relvl_login_timestamp', Date.now().toString());
      console.log('User session saved to localStorage');
    } catch (error) {
      console.error('Failed to save user session:', error);
    }
  };

  const updateUserSession = (updatedUser) => {
    setCurrentUser(updatedUser);
    saveUserSession(updatedUser);
  };

  const restoreUserSession = () => {
    try {
      const savedUser = localStorage.getItem('relvl_user');
      const loginTimestamp = localStorage.getItem('relvl_login_timestamp');
      
      if (savedUser && loginTimestamp) {
        // Check if session is not older than 30 days (optional expiration)
        const sessionAge = Date.now() - parseInt(loginTimestamp);
        const thirtyDays = 30 * 24 * 60 * 60 * 1000; // 30 days in milliseconds
        
        if (sessionAge < thirtyDays) {
          const user = JSON.parse(savedUser);
          setCurrentUser(user);
          console.log('User session restored from localStorage:', user.username);
          showNotification(`Welcome back, ${user.username}!`, 'success');
        } else {
          // Session expired, clear old data
          clearUserSession();
          console.log('User session expired, cleared localStorage');
        }
      }
    } catch (error) {
      console.error('Failed to restore user session:', error);
      // Clear corrupted data
      clearUserSession();
    }
  };

  const clearUserSession = () => {
    try {
      localStorage.removeItem('relvl_user');
      localStorage.removeItem('relvl_login_timestamp');
      console.log('User session cleared from localStorage');
    } catch (error) {
      console.error('Failed to clear user session:', error);
    }
  };

  const handleLogout = () => {
    setCurrentUser(null);
    setAuthForm({ username: '', password: '' });
    setFocusSession(null);
    setActiveTab('dashboard');
    clearUserSession();
    showNotification('Logged out successfully', 'info');
  };

  // Get tab requirements
  const getTabRequirements = (tab) => {
    switch (tab) {
      case 'statistics':
        return { requiredLevel: 3, unlocked: currentUser?.level >= 3 };
      case 'weekly-planner':
        return { requiredLevel: 5, unlocked: currentUser?.level >= 5 };
      case 'wheel':
        return { requiredLevel: 6, unlocked: currentUser?.level >= 6 };
      default:
        return { requiredLevel: 1, unlocked: true };
    }
  };

  // beforeunload handler to prevent tab close during active focus session
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (focusSession && currentUser) {
        // Try to end the session before leaving (best effort)
        navigator.sendBeacon(`${API}/focus/end`, JSON.stringify({
          user_id: currentUser.id
        }));
        
        e.preventDefault();
        e.returnValue = 'You have an active focus session. Your session will be saved automatically.';
        return e.returnValue;
      }
    };

    if (focusSession) {
      window.addEventListener('beforeunload', handleBeforeUnload);
    }

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [focusSession, currentUser]);

  // Initialize data and restore user session on component mount
  useEffect(() => {
    restoreUserSession();
    initializeData();
  }, []);

  // Set up polling for real-time updates when user is logged in
  useEffect(() => {
    if (currentUser) {
      fetchTasks();
      fetchWeeklyTasks();
      fetchSocialRate();
      fetchStatistics();
      fetchWheelStatus();
      
      // Check for active sessions when user logs in
      checkForActiveSession();
      
      const interval = setInterval(() => {
        fetchActiveUsers();
        fetchUsers();
        fetchNotifications();
        fetchTasks();
        fetchWeeklyTasks();
        fetchSocialRate();
        fetchWheelStatus();
      }, 3000);

      return () => clearInterval(interval);
    }
  }, [currentUser, currentWeekOffset]);

  const initializeData = async () => {
    try {
      console.log('Initializing app data...');
      console.log('API endpoint:', `${API}/init`);
      
      await axios.post(`${API}/init`);
      await fetchShopItems();
      await fetchSocialRate();
      
      // Check for active sessions on page load
      await checkForActiveSession();
      
      setIsInitialized(true);
      console.log('App initialized successfully');
    } catch (error) {
      console.error('Failed to initialize:', error);
      console.error('Error details:', error.response?.data);
      
      // Try to continue even if initialization fails
      setIsInitialized(true);
    }
  };

  const checkForActiveSession = async () => {
    if (!currentUser) return;
    
    try {
      console.log('Checking for active focus session...');
      
      // Get current user data to check session status
      const response = await axios.get(`${API}/users`);
      const user = response.data.find(u => u.id === currentUser.id);
      
      if (user && user.current_session_start && user.is_focusing) {
        console.log('Found active focus session, resuming...');
        
        // Calculate session duration
        const startTime = new Date(user.current_session_start);
        const currentTime = new Date();
        const durationMinutes = Math.floor((currentTime - startTime) / (1000 * 60));
        
        // Set focus session state to resume the session
        setFocusSession({
          id: 'resumed-session',
          start_time: user.current_session_start,
          user_id: user.id,
          is_active: true
        });
        
        // Show notification about resumed session
        showNotification(`Resumed focus session (${durationMinutes} minutes elapsed)`, 'info');
        
      } else if (user && user.current_session_start && !user.is_focusing) {
        console.log('Found stuck session, ending automatically...');
        
        // End the stuck session
        try {
          const endResponse = await axios.post(`${API}/focus/end`, {
            user_id: currentUser.id
          });
          
          showNotification(`Previous session ended: earned ${endResponse.data.credits_earned} FC for ${endResponse.data.duration_minutes} minutes`, 'success');
          
          // Update user data
          updateUserSession({
            ...currentUser,
            credits: endResponse.data.total_credits,
            is_focusing: false,
            current_session_start: null
          });
          
        } catch (endError) {
          console.error('Failed to end stuck session:', endError);
          showNotification('Found previous session but failed to end it automatically', 'error');
        }
      }
      
    } catch (error) {
      console.error('Failed to check for active session:', error);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      setUsers(response.data);
    } catch (error) {
      console.error('Failed to fetch users:', error);
    }
  };

  const fetchActiveUsers = async () => {
    try {
      const response = await axios.get(`${API}/focus/active`);
      setActiveUsers(response.data);
    } catch (error) {
      console.error('Failed to fetch active users:', error);
    }
  };

  const fetchShopItems = async () => {
    try {
      const response = await axios.get(`${API}/shop/items`);
      setShopItems(response.data);
    } catch (error) {
      console.error('Failed to fetch shop items:', error);
    }
  };

  const fetchTasks = async () => {
    if (!currentUser) return;
    try {
      const response = await axios.get(`${API}/tasks/${currentUser.id}`);
      setTasks(response.data);
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    }
  };

  const fetchWeeklyTasks = async () => {
    if (!currentUser) return;
    try {
      const response = await axios.get(`${API}/weekly-tasks/${currentUser.id}?week_offset=${currentWeekOffset}`);
      setWeeklyTasks(response.data);
    } catch (error) {
      console.error('Failed to fetch weekly tasks:', error);
    }
  };

  const fetchSocialRate = async () => {
    try {
      const response = await axios.get(`${API}/focus/social-rate`);
      setSocialRate(response.data);
    } catch (error) {
      console.error('Failed to fetch social rate:', error);
    }
  };

  const fetchStatistics = async () => {
    if (!currentUser) return;
    try {
      const response = await axios.get(`${API}/statistics/${currentUser.id}`);
      setStatistics(response.data);
    } catch (error) {
      console.error('Failed to fetch statistics:', error);
    }
  };

  const fetchWheelStatus = async () => {
    if (!currentUser) return;
    try {
      const response = await axios.get(`${API}/wheel/status/${currentUser.id}`);
      setWheelStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch wheel status:', error);
    }
  };

  const spinWheel = async () => {
    if (!currentUser || !wheelStatus?.can_spin) return;
    
    try {
      setIsSpinning(true);
      setWheelResult(null);
      
      // Simulate spinning animation delay
      setTimeout(async () => {
        try {
          const response = await axios.post(`${API}/wheel/spin`, {
            user_id: currentUser.id
          });
          
          setWheelResult(response.data);
          
          // Update user credits
          const updatedUser = await axios.get(`${API}/users/${currentUser.id}`);
          updateUserSession(updatedUser.data);
          
          // Refresh wheel status
          await fetchWheelStatus();
          await fetchNotifications();
          
        } catch (error) {
          console.error('Failed to spin wheel:', error);
          alert(error.response?.data?.detail || 'Failed to spin wheel');
        } finally {
          setIsSpinning(false);
        }
      }, 2000); // 2 second spinning animation
      
    } catch (error) {
      console.error('Failed to spin wheel:', error);
      setIsSpinning(false);
    }
  };

  const createTask = async (title, description) => {
    if (!currentUser) return;
    
    try {
      const response = await axios.post(`${API}/tasks`, {
        user_id: currentUser.id,
        title: title.trim(),
        description: description.trim()
      });
      
      await fetchTasks();
      return response.data;
    } catch (error) {
      console.error('Failed to create task:', error);
      throw error;
    }
  };

  const createWeeklyTask = async (title, description, tags, dayOfWeek) => {
    if (!currentUser) return;
    
    try {
      const response = await axios.post(`${API}/weekly-tasks`, {
        user_id: currentUser.id,
        title: title.trim(),
        description: description.trim(),
        tags: tags,
        day_of_week: dayOfWeek
      });
      
      await fetchWeeklyTasks();
      return response.data;
    } catch (error) {
      console.error('Failed to create weekly task:', error);
      throw error;
    }
  };

  const fetchNotifications = async () => {
    if (!currentUser) return;
    try {
      const response = await axios.get(`${API}/notifications/${currentUser.id}`);
      setNotifications(response.data);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    }
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    
    if (!authForm.username.trim() || !authForm.password.trim()) {
      showNotification('Please fill in all fields', 'error');
      return;
    }

    try {
      console.log(`Attempting ${authMode} with:`, {
        username: authForm.username.trim(),
        endpoint: `${API}/auth/${authMode === 'login' ? 'login' : 'register'}`
      });
      
      const endpoint = authMode === 'login' ? 'login' : 'register';
      const response = await axios.post(`${API}/auth/${endpoint}`, {
        username: authForm.username.trim(),
        password: authForm.password
      });
      
      console.log(`${authMode} successful:`, response.data);
      
      const user = response.data.user;
      setCurrentUser(user);
      saveUserSession(user); // Save to localStorage
      setAuthForm({ username: '', password: '' });
      
      showNotification(`${authMode === 'login' ? 'Logged in' : 'Registered'} successfully!`, 'success');
      
      // Fetch additional data, but don't fail registration if these fail
      try {
        await fetchUsers();
      } catch (error) {
        console.error('Failed to fetch users after auth:', error);
      }
      
      try {
        await fetchNotifications();
      } catch (error) {
        console.error('Failed to fetch notifications after auth:', error);
      }
      
      try {
        await fetchTasks();
      } catch (error) {
        console.error('Failed to fetch tasks after auth:', error);
      }
      
      try {
        await fetchWeeklyTasks();
      } catch (error) {
        console.error('Failed to fetch weekly tasks after auth:', error);
      }
      
    } catch (error) {
      console.error('Auth failed:', error);
      console.error('Error details:', {
        status: error.response?.status,
        data: error.response?.data,
        message: error.message
      });
      showNotification(error.response?.data?.detail || `${authMode} failed`, 'error');
    }
  };

  const completeTask = async (taskId) => {
    if (!currentUser) return;
    
    try {
      const response = await axios.post(`${API}/tasks/complete`, {
        user_id: currentUser.id,
        task_id: taskId
      });
      
      const updatedUser = await axios.get(`${API}/users/${currentUser.id}`);
      updateUserSession(updatedUser.data);
      
      await fetchUsers();
      await fetchNotifications();
      
      showNotification(`Task completed! You earned ${response.data.credits_earned} credits.`, 'success');
    } catch (error) {
      console.error('Failed to complete task:', error);
      showNotification(error.response?.data?.detail || 'Failed to complete task', 'error');
    }
  };

  const completeWeeklyTask = async (taskId) => {
    if (!currentUser) return;
    
    try {
      const response = await axios.post(`${API}/weekly-tasks/complete`, {
        user_id: currentUser.id,
        task_id: taskId
      });
      
      const updatedUser = await axios.get(`${API}/users/${currentUser.id}`);
      updateUserSession(updatedUser.data);
      
      await fetchUsers();
      await fetchWeeklyTasks();
      
      alert(`Weekly task completed! You earned ${response.data.credits_earned} credits.`);
    } catch (error) {
      console.error('Failed to complete weekly task:', error);
      alert(error.response?.data?.detail || 'Failed to complete weekly task');
    }
  };

  const deleteWeeklyTask = async (taskId) => {
    if (!currentUser) return;
    
    try {
      await axios.delete(`${API}/weekly-tasks/${taskId}?user_id=${currentUser.id}`);
      await fetchWeeklyTasks();
    } catch (error) {
      console.error('Failed to delete weekly task:', error);
      alert(error.response?.data?.detail || 'Failed to delete weekly task');
    }
  };

  const handleCreateTask = async (e) => {
    e.preventDefault();
    
    if (!newTask.title.trim()) {
      showNotification('Please enter a task title', 'error');
      return;
    }

    try {
      await createTask(newTask.title, newTask.description);
      setNewTask({ title: '', description: '' });
      showNotification('Task created successfully!', 'success');
    } catch (error) {
      console.error('Failed to create task:', error);
      showNotification(error.response?.data?.detail || 'Failed to create task', 'error');
    }
  };

  const handleCreateWeeklyTask = async (e) => {
    e.preventDefault();
    
    if (!newWeeklyTask.title.trim()) {
      alert('Please enter a task title');
      return;
    }

    try {
      await createWeeklyTask(
        newWeeklyTask.title, 
        newWeeklyTask.description, 
        newWeeklyTask.tags,
        newWeeklyTask.dayOfWeek
      );
      setNewWeeklyTask({ title: '', description: '', tags: [], dayOfWeek: 0 });
      alert('Weekly task created successfully!');
    } catch (error) {
      console.error('Failed to create weekly task:', error);
      alert(error.response?.data?.detail || 'Failed to create weekly task');
    }
  };

  const startFocusSession = async () => {
    if (!currentUser) return;
    
    try {
      const response = await axios.post(`${API}/focus/start`, { 
        user_id: currentUser.id 
      });
      setFocusSession(response.data);
      // Reset timer when starting new focus session
      resetTimer();
      await fetchActiveUsers();
    } catch (error) {
      console.error('Failed to start focus session:', error);
      showNotification(error.response?.data?.detail || 'Failed to start focus session', 'error');
    }
  };

  const endFocusSession = async () => {
    if (!currentUser) return;
    
    try {
      const response = await axios.post(`${API}/focus/end`, { 
        user_id: currentUser.id 
      });
      setFocusSession(null);
      // Reset timer when ending focus session
      resetTimer();
      
      const updatedUser = await axios.get(`${API}/users/${currentUser.id}`);
      updateUserSession(updatedUser.data);
      
      await fetchActiveUsers();
      await fetchUsers();
      await fetchStatistics();
      
      showNotification(`Session ended! You earned ${response.data.credits_earned} credits in ${response.data.duration_minutes} minutes (Rate: ${response.data.effective_rate.toFixed(1)}x).`, 'success');
    } catch (error) {
      console.error('Failed to end focus session:', error);
      showNotification(error.response?.data?.detail || 'Failed to end focus session', 'error');
    }
  };

  const purchaseItem = async (itemId, targetUserId = null) => {
    if (!currentUser) return;
    
    try {
      const response = await axios.post(`${API}/shop/purchase`, {
        user_id: currentUser.id,
        item_id: itemId,
        target_user_id: targetUserId
      });
      
      const updatedUser = await axios.get(`${API}/users/${currentUser.id}`);
      updateUserSession(updatedUser.data);
      
      await fetchUsers();
      await fetchNotifications();
      
      let message = `Successfully purchased ${response.data.item_name}!`;
      if (response.data.requires_consent) {
        message += ` Waiting for consent from target user.`;
      }
      alert(message);
    } catch (error) {
      console.error('Failed to purchase item:', error);
      alert(error.response?.data?.detail || 'Failed to purchase item');
    }
  };

  const handleUserClick = (user) => {
    setSelectedUser(user);
    setShowUserProfile(true);
  };

  const handleUpdateUser = (updatedUser) => {
    setCurrentUser(updatedUser);
    fetchUsers(); // Refresh users list
  };

  const handleTabClick = (tab) => {
    const requirements = getTabRequirements(tab);
    
    // Always allow tab to be set (for locked preview functionality)
    setActiveTab(tab);
    
    if (requirements.unlocked) {
      // Only fetch data if tab is unlocked
      if (tab === 'statistics') {
        fetchStatistics();
      } else if (tab === 'wheel') {
        fetchWheelStatus();
      }
    }
  };

  // Enhanced Chart configurations with gradients, glows, and animations
  const getChartOptions = (chartType = 'default') => {
    const baseConfig = {
      responsive: true,
      interaction: {
        intersect: false,
        mode: 'index',
      },
      animation: {
        duration: 2000,
        easing: 'easeInOutQuart',
        delay: (context) => {
          let delay = 0;
          if (context.type === 'data' && context.mode === 'default') {
            delay = context.dataIndex * 50 + context.datasetIndex * 100;
          }
          return delay;
        },
      },
      plugins: {
        legend: {
          position: 'top',
          labels: {
            color: 'var(--text-primary)',
            padding: 20,
            font: {
              size: 12,
              weight: 'bold'
            },
            usePointStyle: true,
            pointStyle: 'circle'
          }
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.9)',
          titleColor: '#ffffff',
          bodyColor: '#ffffff',
          borderColor: 'var(--accent-color)',
          borderWidth: 2,
          cornerRadius: 12,
          padding: 16,
          boxShadow: '0 10px 30px rgba(0, 0, 0, 0.3)',
          titleFont: {
            size: 14,
            weight: 'bold'
          },
          bodyFont: {
            size: 13
          },
          displayColors: true,
          callbacks: {
            label: function(context) {
              return `${context.dataset.label}: ${context.parsed.y}${chartType === 'bar' ? ' minutes' : ''}`;
            }
          }
        }
      },
      scales: {
        x: {
          ticks: {
            color: 'var(--text-secondary)',
            font: {
              size: 11,
              weight: '500'
            }
          },
          grid: {
            color: 'rgba(100, 100, 100, 0.1)',
            lineWidth: 1,
            drawBorder: false
          },
          border: {
            display: false
          }
        },
        y: {
          ticks: {
            color: 'var(--text-secondary)',
            font: {
              size: 11,
              weight: '500'
            },
            callback: function(value) {
              return chartType === 'bar' ? value + 'm' : value;
            }
          },
          grid: {
            color: 'rgba(100, 100, 100, 0.1)',
            lineWidth: 1,
            drawBorder: false
          },
          border: {
            display: false
          },
          beginAtZero: true
        }
      }
    };

    return baseConfig;
  };

  // Create gradient for bar charts
  const createBarGradient = (ctx, chartArea) => {
    if (!chartArea) return null;
    
    const gradient = ctx.createLinearGradient(0, chartArea.bottom, 0, chartArea.top);
    gradient.addColorStop(0, 'rgba(59, 130, 246, 0.1)');
    gradient.addColorStop(0.5, 'rgba(59, 130, 246, 0.6)');
    gradient.addColorStop(1, 'rgba(59, 130, 246, 1)');
    return gradient;
  };

  // Create gradient for line charts
  const createLineGradient = (ctx, chartArea, colors) => {
    if (!chartArea) return null;
    
    const gradient = ctx.createLinearGradient(0, chartArea.bottom, 0, chartArea.top);
    gradient.addColorStop(0, colors.start);
    gradient.addColorStop(1, colors.end);
    return gradient;
  };

  if (!isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
        <div className="text-xl">
          <div className="loading-spinner inline-block mr-3"></div>
          Initializing RELVL...
        </div>
      </div>
    );
  }

  if (!currentUser) {
    return (
      <div className="min-h-screen flex items-center justify-center login-container" style={{ backgroundColor: 'var(--bg-primary)' }}>
        <ThreeBackground darkMode={darkMode} />
        <FloatingDoodles darkMode={darkMode} />
        
        {/* Theme Toggle in top-right corner */}
        <div className="absolute top-6 right-6 z-50">
          <ThemeToggle />
        </div>
        
        <div className="login-card p-8 rounded-xl shadow-2xl max-w-md w-full mx-4 relative z-10">
          <h1 className="login-title text-3xl font-bold text-center mb-2">RELVL</h1>
          <p className="login-tagline text-center mb-6 opacity-80">
            Turn focus into currency. Strategy decides who rises.
          </p>
          
          {/* Auth Mode Toggle */}
          <div className="auth-toggle flex rounded-lg p-1 mb-6" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
            <button
              onClick={() => setAuthMode('login')}
              className={`flex-1 py-2 px-4 rounded-md transition-all btn-enhanced ${
                authMode === 'login' 
                  ? darkMode 
                    ? 'bg-white text-black' 
                    : 'bg-white text-black'
                  : 'opacity-70 hover:opacity-100'
              }`}
            >
              Login
            </button>
            <button
              onClick={() => setAuthMode('register')}
              className={`flex-1 py-2 px-4 rounded-md transition-all btn-enhanced ${
                authMode === 'register' 
                  ? darkMode 
                    ? 'bg-white text-black' 
                    : 'bg-white text-black'
                  : 'opacity-70 hover:opacity-100'
              }`}
            >
              Register
            </button>
          </div>
          
          <form className="auth-form" onSubmit={handleAuth}>
            <input
              type="text"
              placeholder="Username"
              value={authForm.username}
              onChange={(e) => setAuthForm({...authForm, username: e.target.value})}
              className="form-input w-full p-3 rounded mb-4 focus:outline-none"
              required
            />
            <input
              type="password"
              placeholder="Password"
              value={authForm.password}
              onChange={(e) => setAuthForm({...authForm, password: e.target.value})}
              className="form-input w-full p-3 rounded mb-4 focus:outline-none"
              required
            />
            <button
              type="submit"
              className="btn-enhanced w-full p-3 rounded font-semibold"
              style={{ 
                backgroundColor: darkMode ? 'var(--accent-color)' : 'white',
                color: darkMode ? 'var(--bg-primary)' : 'black'
              }}
            >
              {authMode === 'login' ? 'Enter the Arena' : 'Join the Battle'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  const unreadNotifications = notifications.filter(n => !n.is_read && n.user_id === currentUser.id);

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', requiredLevel: 1 },
    { id: 'shop', label: 'Shop', requiredLevel: 1 },
    { id: 'tasks', label: 'Tasks', requiredLevel: 1 },
    { id: 'statistics', label: 'Statistics', requiredLevel: 3 },
    { id: 'weekly-planner', label: 'Weekly Planner', requiredLevel: 5 },
    { id: 'wheel', label: 'Daily Wheel', requiredLevel: 6 },
    { id: 'leaderboard', label: 'Leaderboard', requiredLevel: 1 },
    { id: 'activity', label: 'Activity', requiredLevel: 1 }
  ];

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
      {/* Notification Container */}
      <NotificationContainer 
        notifications={appNotifications} 
        onRemove={removeNotification} 
      />
      
      {/* Header */}
      <header className="header-container p-4">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold">RELVL</h1>
          <div className="flex items-center space-x-6">
            <div className="text-right">
              <div className="text-lg font-semibold flex items-center">
                <span 
                  className="clickable-username"
                  onClick={() => handleUserClick(currentUser)}
                >
                  {currentUser.username}
                </span>
                {currentUser.level > 1 && (
                  <span className="ml-2 bg-yellow-500 text-black px-2 py-1 rounded-full text-xs font-bold">
                    L{currentUser.level}
                  </span>
                )}
              </div>
              <div className="opacity-80">{currentUser.credits} FC</div>
              <div className="text-sm opacity-70">
                Effective Rate: {(socialRate.social_multiplier * currentUser.credit_rate_multiplier).toFixed(1)}x
              </div>
              <div className="text-xs opacity-60">
                Social: {socialRate.social_multiplier.toFixed(1)}x • Personal: {currentUser.credit_rate_multiplier.toFixed(1)}x
              </div>
            </div>
            {unreadNotifications.length > 0 && (
              <div className="notification-badge bg-red-500 text-white px-2 py-1 rounded-full text-xs">
                {unreadNotifications.length}
              </div>
            )}
            <button
              onClick={() => setShowSettings(true)}
              className="btn-enhanced px-3 py-1 rounded"
              style={{ backgroundColor: 'var(--bg-tertiary)' }}
              title="Settings"
            >
              ⚙️
            </button>
            <ThemeToggle />
            <button
              onClick={handleLogout}
              className="btn-enhanced px-3 py-1 rounded"
              style={{ backgroundColor: 'var(--bg-tertiary)' }}
              title="Logout"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="nav-container border-b">
        <div className="max-w-6xl mx-auto">
          <div className="flex space-x-8">
            {tabs.map(tab => {
              const isUnlocked = currentUser.level >= tab.requiredLevel;
              return (
                <button
                  key={tab.id}
                  onClick={() => handleTabClick(tab.id)}
                  className={`nav-tab nav-tab-animated py-3 px-4 border-b-2 transition-all capitalize relative ${
                    activeTab === tab.id 
                      ? 'active border-black font-semibold' 
                      : 'border-transparent opacity-70 hover:opacity-100'
                  } ${!isUnlocked ? 'locked-tab' : ''}`}
                  style={{
                    borderColor: activeTab === tab.id ? 'var(--accent-color)' : 'transparent',
                    color: isUnlocked ? 'var(--text-primary)' : 'var(--text-muted)',
                    cursor: isUnlocked ? 'pointer' : 'not-allowed'
                  }}
                >
                  {tab.label}
                  {!isUnlocked && (
                    <span className="ml-1 text-xs">🔒</span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto p-6">
        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {/* Focus Timer */}
            <div className={`focus-timer-container card-enhanced p-6 rounded-lg ${
              focusSession ? 'focus-session-active' : 'focus-session-inactive'
            }`}>
              <h2 className="text-xl font-bold mb-4">Focus Session</h2>
              
              {!focusSession ? (
                <div className="text-center">
                  <p className="mb-2 opacity-80">
                    Ready to earn some Focus Credits (FC)?
                  </p>
                  <div className="card-enhanced p-3 mb-4" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                    <div className="font-semibold mb-1 focus-credits-animation">
                      Social Rate: {socialRate.social_multiplier.toFixed(1)}x ({socialRate.credits_per_hour} FC/hour)
                    </div>
                    <div className="text-xs opacity-70">
                      {socialRate.active_users_count} users focusing = {socialRate.social_multiplier.toFixed(1)}x multiplier
                    </div>
                    <div className="text-xs opacity-70 mt-1">
                      Your personal rate: {(socialRate.social_multiplier * currentUser.credit_rate_multiplier).toFixed(1)}x
                    </div>
                  </div>
                  <button
                    onClick={startFocusSession}
                    className="btn-enhanced px-8 py-3 rounded-lg font-semibold"
                    style={{ backgroundColor: 'var(--accent-color)', color: 'var(--bg-primary)' }}
                  >
                    Start Focus Session
                  </button>
                </div>
              ) : (
                <div className="text-center">
                  <div className="p-4 rounded-lg mb-4" style={{ backgroundColor: 'rgba(16, 185, 129, 0.2)', border: '2px solid #10b981' }}>
                    <div className="text-2xl font-bold text-green-800 mb-2">FOCUSING</div>
                    <div className="text-green-700">
                      Started at {new Date(focusSession.start_time).toLocaleTimeString()}
                    </div>
                    <div className="text-sm text-green-600 mt-2">
                      Earning {(socialRate.social_multiplier * currentUser.credit_rate_multiplier * 30).toFixed(1)} FC per hour
                    </div>
                    <div className="text-xs text-green-600">
                      Social: {socialRate.social_multiplier.toFixed(1)}x • Personal: {currentUser.credit_rate_multiplier.toFixed(1)}x
                    </div>
                  </div>
                  
                  {/* Timer Component - Only available during focus sessions */}
                  <div className="timer-container">
                    <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
                      Focus Timer
                    </h3>
                    
                    {/* Duration Selector */}
                    <div className="timer-duration-selector">
                      {[10, 20, 30, 45, 60, 90, 120, 180, 240].map((minutes) => (
                        <button
                          key={minutes}
                          onClick={() => setTimerDuration(minutes)}
                          className={`timer-duration-btn ${timer.duration === minutes ? 'active' : ''}`}
                          disabled={timer.isRunning}
                        >
                          {minutes >= 60 ? `${Math.floor(minutes/60)}h${minutes%60 ? ` ${minutes%60}m` : ''}` : `${minutes}m`}
                        </button>
                      ))}
                    </div>
                    
                    {/* Timer Display */}
                    <div className="timer-display">
                      {formatTime(timer.timeLeft)}
                    </div>
                    
                    {/* Timer Controls */}
                    <div className="timer-controls">
                      {!timer.isRunning ? (
                        <button
                          onClick={startTimer}
                          className="timer-btn start"
                          disabled={timer.timeLeft === 0}
                        >
                          ▶️ {timer.isSet ? 'Resume' : 'Start'}
                        </button>
                      ) : (
                        <button
                          onClick={pauseTimer}
                          className="timer-btn pause"
                        >
                          ⏸️ Pause
                        </button>
                      )}
                      
                      <button
                        onClick={resetTimer}
                        className="timer-btn reset"
                        disabled={!timer.isSet}
                      >
                        🔄 Reset
                      </button>
                    </div>
                    
                    <div className="text-xs mt-2 opacity-70" style={{ color: 'var(--text-secondary)' }}>
                      {timer.isRunning ? '🟢 Timer is running' : timer.isSet ? '⏸️ Timer is paused' : '⏱️ Set a timer to stay focused'}
                    </div>
                  </div>
                  
                  <button
                    onClick={endFocusSession}
                    className="btn-enhanced bg-red-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-red-700 mt-4"
                  >
                    End Session
                  </button>
                </div>
              )}
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {[
                { label: 'Focus Credits', value: currentUser.credits },
                { label: 'Focus Minutes', value: currentUser.total_focus_time },
                { label: 'Credit Rate', value: `${currentUser.credit_rate_multiplier.toFixed(1)}x` },
                { label: 'Tasks Done', value: currentUser.completed_tasks }
              ].map((stat, index) => (
                <div key={index} className="stats-card card-enhanced p-4 rounded-lg text-center" style={{ backgroundColor: 'var(--accent-color)', color: 'var(--bg-primary)' }}>
                  <div className="text-2xl font-bold">{stat.value}</div>
                  <div className="opacity-80">{stat.label}</div>
                </div>
              ))}
            </div>

            {/* Active Users */}
            {activeUsers.length > 0 && (
              <div className="card-enhanced p-6 rounded-lg">
                <h3 className="text-lg font-semibold mb-3">Currently Focusing</h3>
                <div className="space-y-2">
                  {activeUsers.map((user, index) => (
                    <div key={user.id} className="active-user-item activity-item flex justify-between items-center p-3 rounded" style={{ animationDelay: `${index * 0.1}s` }}>
                      <span className="font-medium flex items-center">
                        <span 
                          className="clickable-username"
                          onClick={() => handleUserClick(user)}
                        >
                          {user.username}
                        </span>
                        {user.level > 1 && (
                          <span className="ml-2 bg-yellow-400 text-black px-1.5 py-0.5 rounded text-xs">
                            L{user.level}
                          </span>
                        )}
                      </span>
                      <div className="flex items-center space-x-3">
                        <span className="text-sm opacity-70">{user.credits} FC</span>
                        <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Shop Tab */}
        {activeTab === 'shop' && (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold">Strategic Arsenal</h2>
              <p className="opacity-70">Boost yourself or target others with passes</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {shopItems.map((item, index) => (
                <div key={item.id} className={`shop-item-animated card-enhanced rounded-lg p-6 ${
                  item.item_type === 'sabotage' ? 'shop-item-sabotage' :
                  item.item_type === 'special' ? 'shop-item-special' : 
                  item.item_type === 'defensive' ? 'shop-item-defensive' : 'shop-item-boost'
                }`} style={{ animationDelay: `${index * 0.1}s` }}>
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="text-lg font-bold flex items-center">
                      <span className="text-2xl mr-2">{item.emoji}</span>
                      {item.name}
                    </h3>
                    <div className={`px-3 py-1 rounded text-sm font-semibold text-white ${
                      item.item_type === 'sabotage' ? 'bg-red-600' :
                      item.item_type === 'special' ? 'bg-blue-600' : 
                      item.item_type === 'defensive' ? 'bg-purple-600' : 'bg-green-600'
                    }`}>
                      {item.price} FC
                    </div>
                  </div>
                  
                  <p className="opacity-80 mb-4 text-sm">{item.description}</p>
                  
                  {item.requires_target ? (
                    <div>
                      <UserDropdown
                        item={item}
                        users={users}
                        currentUser={currentUser}
                        selectedUserId={selectedTargetUsers[item.id]}
                        onSelectUser={(userId) => {
                          setSelectedTargetUsers(prev => ({
                            ...prev,
                            [item.id]: userId
                          }));
                        }}
                      />
                      <button
                        onClick={() => {
                          const targetUserId = selectedTargetUsers[item.id];
                          if (targetUserId) {
                            purchaseItem(item.id, targetUserId);
                            // Clear selection after purchase
                            setSelectedTargetUsers(prev => ({
                              ...prev,
                              [item.id]: null
                            }));
                          } else {
                            alert('Please select a target user');
                          }
                        }}
                        disabled={currentUser.credits < item.price || !selectedTargetUsers[item.id]}
                        className={`btn-enhanced w-full py-3 px-4 rounded-lg font-semibold text-white transition-all duration-300 ${
                          currentUser.credits < item.price || !selectedTargetUsers[item.id]
                            ? 'bg-gray-400 cursor-not-allowed opacity-60' 
                            : item.item_type === 'sabotage' 
                            ? 'bg-red-600 hover:bg-red-700 hover:scale-105'
                            : 'bg-blue-600 hover:bg-blue-700 hover:scale-105'
                        }`}
                      >
                        {currentUser.credits < item.price ? 'Insufficient FC' : 
                         !selectedTargetUsers[item.id] ? 'Select Target' : 'Use Pass'}
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => purchaseItem(item.id)}
                      disabled={currentUser.credits < item.price}
                      className={`btn-enhanced w-full py-2 px-4 rounded font-semibold text-white ${
                        currentUser.credits < item.price 
                          ? 'bg-gray-400 cursor-not-allowed' 
                          : 'bg-green-600 hover:bg-green-700'
                      }`}
                    >
                      {currentUser.credits < item.price ? 'Insufficient FC' : 'Purchase'}
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tasks Tab */}
        {activeTab === 'tasks' && (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold">Personal Tasks</h2>
              <p className="opacity-70">Create and complete your own tasks to earn 10 FC each</p>
            </div>
            
            {/* Task Creation Form */}
            <div className="form-animated card-enhanced p-6 rounded-lg">
              <h3 className="text-lg font-bold mb-4">Create New Task</h3>
              <form onSubmit={handleCreateTask} className="space-y-4">
                <input
                  type="text"
                  placeholder="Task title (e.g., Read for 30 minutes)"
                  value={newTask.title}
                  onChange={(e) => setNewTask({...newTask, title: e.target.value})}
                  className="form-input form-input-animated w-full p-3 rounded focus:outline-none"
                  maxLength={100}
                />
                <textarea
                  placeholder="Task description (optional)"
                  value={newTask.description}
                  onChange={(e) => setNewTask({...newTask, description: e.target.value})}
                  className="form-input form-input-animated w-full p-3 rounded focus:outline-none resize-none"
                  rows="3"
                  maxLength={300}
                />
                <button
                  type="submit"
                  className="btn-enhanced px-6 py-2 rounded-lg font-semibold"
                  style={{ backgroundColor: 'var(--accent-color)', color: 'var(--bg-primary)' }}
                >
                  Create Task
                </button>
              </form>
            </div>
            
            {/* Tasks List */}
            <div>
              <h3 className="text-lg font-semibold mb-4">Your Active Tasks</h3>
              {tasks.length === 0 ? (
                <div className="text-center py-8 opacity-70">
                  <p>No tasks yet. Create your first task above!</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {tasks.map((task, index) => (
                    <div key={task.id} className="task-card card-enhanced p-6 rounded-lg" style={{ animationDelay: `${index * 0.1}s` }}>
                      <h4 className="text-lg font-bold mb-2">{task.title}</h4>
                      {task.description && (
                        <p className="opacity-70 mb-4 text-sm">{task.description}</p>
                      )}
                      
                      <div className="flex justify-between items-center">
                        <span className="text-green-600 font-semibold">+{task.credits_reward} FC</span>
                        <button
                          onClick={() => completeTask(task.id)}
                          className="task-complete-btn bg-green-600 text-white px-4 py-2 rounded font-semibold hover:bg-green-700"
                        >
                          Complete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Statistics Tab */}
        {activeTab === 'statistics' && (
          currentUser.level >= 3 ? (
            <div className="space-y-6">
              <div className="text-center mb-6">
                <h2 className="text-2xl font-bold">Study Statistics</h2>
                <p className="opacity-70">Your focus and productivity insights</p>
              </div>
              
              {statistics && (
                <>
                  {/* Overview Stats */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                    {[
                      { label: 'Total Focus Time', value: `${statistics.user_stats.total_focus_time} min` },
                      { label: 'Total Credits', value: statistics.user_stats.total_credits },
                      { label: 'Tasks Completed', value: statistics.user_stats.total_tasks_completed },
                      { label: 'Current Level', value: statistics.user_stats.current_level }
                    ].map((stat, index) => (
                      <div key={index} className="stats-card card-enhanced p-4 rounded-lg text-center" style={{ backgroundColor: 'var(--accent-color)', color: 'var(--bg-primary)' }}>
                        <div className="text-2xl font-bold">{stat.value}</div>
                        <div className="opacity-80">{stat.label}</div>
                      </div>
                    ))}
                  </div>

                  {/* Charts Grid */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Daily Focus Time Bar Chart */}
                    <div className="card-enhanced p-6 rounded-lg chart-glow">
                      <h3 className="text-lg font-bold mb-4 chart-title">📊 Daily Focus Time (Last 7 Days)</h3>
                      <div className="chart-container">
                        <Bar
                          data={{
                            labels: Object.keys(statistics.daily_focus_time).slice(-7),
                            datasets: [{
                              label: 'Minutes Focused',
                              data: Object.values(statistics.daily_focus_time).slice(-7),
                              backgroundColor: (context) => {
                                const chart = context.chart;
                                const {ctx, chartArea} = chart;
                                if (!chartArea) return 'rgba(59, 130, 246, 0.8)';
                                return createBarGradient(ctx, chartArea);
                              },
                              borderColor: 'rgba(59, 130, 246, 1)',
                              borderWidth: 2,
                              borderRadius: 8,
                              borderSkipped: false,
                              hoverBackgroundColor: 'rgba(59, 130, 246, 0.9)',
                              hoverBorderColor: 'rgba(37, 99, 235, 1)',
                              hoverBorderWidth: 3,
                              shadowColor: 'rgba(59, 130, 246, 0.5)',
                              shadowBlur: 15,
                              shadowOffsetX: 0,
                              shadowOffsetY: 8
                            }]
                          }}
                          options={{
                            ...getChartOptions('bar'),
                            plugins: {
                              ...getChartOptions('bar').plugins,
                              beforeDraw: (chart) => {
                                const ctx = chart.ctx;
                                ctx.save();
                                ctx.shadowColor = 'rgba(59, 130, 246, 0.3)';
                                ctx.shadowBlur = 20;
                                ctx.shadowOffsetX = 2;
                                ctx.shadowOffsetY = 4;
                              }
                            }
                          }}
                        />
                      </div>
                    </div>

                    {/* Task Completion Pie Chart */}
                    <div className="card-enhanced p-6 rounded-lg">
                      <h3 className="text-lg font-bold mb-4">Task Completion Breakdown</h3>
                      <div className="chart-container">
                        <Pie
                          data={{
                            labels: ['Regular Tasks', 'Weekly Tasks'],
                            datasets: [{
                              data: [
                                statistics.user_stats.regular_tasks_completed,
                                statistics.user_stats.weekly_tasks_completed
                              ],
                              backgroundColor: [
                                'rgba(34, 197, 94, 0.8)',
                                'rgba(168, 85, 247, 0.8)'
                              ],
                              borderColor: [
                                'rgba(34, 197, 94, 1)',
                                'rgba(168, 85, 247, 1)'
                              ],
                              borderWidth: 2
                            }]
                          }}
                          options={{
                            responsive: true,
                            plugins: {
                              legend: {
                                position: 'bottom',
                                labels: {
                                  color: 'var(--text-primary)'
                                }
                              },
                              tooltip: {
                                backgroundColor: 'var(--bg-secondary)',
                                titleColor: 'var(--text-primary)',
                                bodyColor: 'var(--text-primary)',
                                borderColor: 'var(--border-color)',
                                borderWidth: 1
                              }
                            }
                          }}
                        />
                      </div>
                    </div>

                    {/* Weekly Progress Line Chart */}
                    <div className="card-enhanced p-6 rounded-lg">
                      <h3 className="text-lg font-bold mb-4">Weekly Progress</h3>
                      <div className="chart-container">
                        <Line
                          data={{
                            labels: statistics.weekly_breakdown.map(w => new Date(w.week_start).toLocaleDateString()),
                            datasets: [
                              {
                                label: 'Focus Minutes',
                                data: statistics.weekly_breakdown.map(w => w.focus_minutes),
                                borderColor: 'rgba(34, 197, 94, 1)',
                                backgroundColor: 'rgba(34, 197, 94, 0.1)',
                                fill: true,
                                tension: 0.4
                              },
                              {
                                label: 'Credits Earned',
                                data: statistics.weekly_breakdown.map(w => w.credits_earned),
                                borderColor: 'rgba(59, 130, 246, 1)',
                                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                                fill: true,
                                tension: 0.4
                              }
                            ]
                          }}
                          options={getChartOptions()}
                        />
                      </div>
                    </div>

                    {/* Credits Earned Bar Chart */}
                    <div className="card-enhanced p-6 rounded-lg">
                      <h3 className="text-lg font-bold mb-4">Daily Credits Earned</h3>
                      <div className="chart-container">
                        <Bar
                          data={{
                            labels: Object.keys(statistics.daily_credits).slice(-7),
                            datasets: [{
                              label: 'Credits Earned',
                              data: Object.values(statistics.daily_credits).slice(-7),
                              backgroundColor: 'rgba(168, 85, 247, 0.8)',
                              borderColor: 'rgba(168, 85, 247, 1)',
                              borderWidth: 1
                            }]
                          }}
                          options={getChartOptions()}
                        />
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          ) : (
            <LockedTabContent requiredLevel={3} />
          )
        )}

        {/* Weekly Planner Tab */}
        {activeTab === 'weekly-planner' && (
          currentUser.level >= 5 ? (
            <div className="space-y-6">
              <div className="text-center mb-6">
                <h2 className="text-2xl font-bold">Weekly Planner</h2>
                <p className="opacity-70">Plan your tasks for each day of the week</p>
              </div>

              {/* Week Navigation */}
              <div className="flex justify-center items-center space-x-4 mb-6">
                <button
                  onClick={() => setCurrentWeekOffset(currentWeekOffset - 1)}
                  className="btn-enhanced px-4 py-2 rounded"
                  style={{ backgroundColor: 'var(--bg-tertiary)' }}
                >
                  ← Previous Week
                </button>
                <span className="font-semibold">
                  {currentWeekOffset === 0 ? 'Current Week' : 
                   currentWeekOffset > 0 ? `${currentWeekOffset} week${currentWeekOffset > 1 ? 's' : ''} ahead` :
                   `${Math.abs(currentWeekOffset)} week${Math.abs(currentWeekOffset) > 1 ? 's' : ''} ago`}
                </span>
                <button
                  onClick={() => setCurrentWeekOffset(currentWeekOffset + 1)}
                  className="btn-enhanced px-4 py-2 rounded"
                  style={{ backgroundColor: 'var(--bg-tertiary)' }}
                >
                  Next Week →
                </button>
              </div>
              
              {/* Task Creation Form */}
              <div className="form-animated card-enhanced p-6 rounded-lg">
                <h3 className="text-lg font-bold mb-4">Add New Weekly Task</h3>
                <form onSubmit={handleCreateWeeklyTask} className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <input
                      type="text"
                      placeholder="Task title"
                      value={newWeeklyTask.title}
                      onChange={(e) => setNewWeeklyTask({...newWeeklyTask, title: e.target.value})}
                      className="form-input form-input-animated w-full p-3 rounded focus:outline-none"
                      maxLength={100}
                    />
                    <select
                      value={newWeeklyTask.dayOfWeek}
                      onChange={(e) => setNewWeeklyTask({...newWeeklyTask, dayOfWeek: parseInt(e.target.value)})}
                      className="form-input form-input-animated w-full p-3 rounded focus:outline-none"
                    >
                      <option value={0}>Monday</option>
                      <option value={1}>Tuesday</option>
                      <option value={2}>Wednesday</option>
                      <option value={3}>Thursday</option>
                      <option value={4}>Friday</option>
                      <option value={5}>Saturday</option>
                      <option value={6}>Sunday</option>
                    </select>
                  </div>
                  <textarea
                    placeholder="Task description (optional)"
                    value={newWeeklyTask.description}
                    onChange={(e) => setNewWeeklyTask({...newWeeklyTask, description: e.target.value})}
                    className="form-input form-input-animated w-full p-3 rounded focus:outline-none resize-none"
                    rows="3"
                    maxLength={300}
                  />
                  <input
                    type="text"
                    placeholder="Tags (comma-separated, optional)"
                    value={newWeeklyTask.tags.join(', ')}
                    onChange={(e) => setNewWeeklyTask({
                      ...newWeeklyTask, 
                      tags: e.target.value.split(',').map(tag => tag.trim()).filter(tag => tag)
                    })}
                    className="form-input form-input-animated w-full p-3 rounded focus:outline-none"
                  />
                  <button
                    type="submit"
                    className="btn-enhanced px-6 py-2 rounded-lg font-semibold"
                    style={{ backgroundColor: 'var(--accent-color)', color: 'var(--bg-primary)' }}
                  >
                    Add Task
                  </button>
                </form>
              </div>
              
              {/* Weekly Calendar */}
              <div className="grid grid-cols-1 md:grid-cols-7 gap-4">
                {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].map((day, index) => {
                  const dayTasks = weeklyTasks.filter(task => task.day_of_week === index);
                  return (
                    <div key={day} className="card-enhanced p-4 rounded-lg">
                      <h3 className="font-bold mb-3 text-center" style={{ color: 'var(--accent-color)' }}>
                        {day}
                      </h3>
                      <div className="space-y-2">
                        {dayTasks.length === 0 ? (
                          <p className="text-center text-sm opacity-60">No tasks</p>
                        ) : (
                          dayTasks.map((task, taskIndex) => (
                            <div key={task.id} className={`task-card p-3 rounded text-sm border ${
                              task.is_completed ? 'opacity-60 line-through' : ''
                            }`} style={{ borderColor: 'var(--border-color)' }}>
                              <div className="font-semibold mb-1">{task.title}</div>
                              {task.description && (
                                <div className="opacity-70 mb-2 text-xs">{task.description}</div>
                              )}
                              {task.tags.length > 0 && (
                                <div className="flex flex-wrap gap-1 mb-2">
                                  {task.tags.map((tag, i) => (
                                    <span key={i} className="bg-blue-500 text-white px-1 py-0.5 rounded text-xs">
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                              )}
                              <div className="flex justify-between items-center">
                                <span className="text-green-600 font-semibold text-xs">+10 FC</span>
                                <div className="flex space-x-1">
                                  {!task.is_completed ? (
                                    <button
                                      onClick={() => completeWeeklyTask(task.id)}
                                      className="bg-green-600 text-white px-2 py-1 rounded text-xs hover:bg-green-700"
                                    >
                                      ✓
                                    </button>
                                  ) : (
                                    <span className="text-green-600 text-xs">✓ Done</span>
                                  )}
                                  <button
                                    onClick={() => deleteWeeklyTask(task.id)}
                                    className="bg-red-600 text-white px-2 py-1 rounded text-xs hover:bg-red-700"
                                  >
                                    ×
                                  </button>
                                </div>
                              </div>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <LockedTabContent requiredLevel={5} />
          )
        )}

        {/* Daily Wheel Tab */}
        {activeTab === 'wheel' && (
          currentUser.level >= 6 ? (
            <div className="space-y-6">
              <div className="text-center mb-6">
                <h2 className="text-2xl font-bold">🎰 Daily Wheel</h2>
                <p className="opacity-70">Spin the wheel once per day to earn 10-100 FC!</p>
              </div>

              <div className="max-w-md mx-auto">
                <div className="card-enhanced p-8 rounded-lg text-center">
                  {/* Wheel Visual */}
                  <div className="relative mx-auto mb-6" style={{ width: '200px', height: '200px' }}>
                    <div 
                      className={`wheel-spinner ${isSpinning ? 'spinning' : ''}`}
                      style={{
                        width: '100%',
                        height: '100%',
                        borderRadius: '50%',
                        background: 'conic-gradient(from 0deg, #ff6b6b 0deg 45deg, #4ecdc4 45deg 90deg, #45b7d1 90deg 135deg, #96ceb4 135deg 180deg, #feca57 180deg 225deg, #ff9ff3 225deg 270deg, #54a0ff 270deg 315deg, #5f27cd 315deg 360deg)',
                        border: '4px solid var(--accent-color)',
                        position: 'relative',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                    >
                      <div className="text-white font-bold text-lg">🎰</div>
                      {/* Pointer */}
                      <div 
                        style={{
                          position: 'absolute',
                          top: '-10px',
                          left: '50%',
                          transform: 'translateX(-50%)',
                          width: '0',
                          height: '0',
                          borderLeft: '10px solid transparent',
                          borderRight: '10px solid transparent',
                          borderBottom: '15px solid var(--accent-color)',
                          zIndex: 10
                        }}
                      />
                    </div>
                  </div>

                  {/* Wheel Status */}
                  <div className="mb-6">
                    {wheelStatus?.can_spin ? (
                      <div className="text-green-500 font-semibold">
                        ✅ Ready to spin!
                      </div>
                    ) : wheelStatus?.reason === 'already_spun_today' ? (
                      <div className="text-orange-500">
                        <div className="font-semibold">Already spun today!</div>
                        <div className="text-sm mt-1">
                          Next spin: {new Date(wheelStatus.next_spin_available).toLocaleString()}
                        </div>
                      </div>
                    ) : wheelStatus?.reason === 'requires_level_6' ? (
                      <div className="text-red-500">
                        <div className="font-semibold">Requires Level 6</div>
                        <div className="text-sm mt-1">Current Level: {wheelStatus.user_level}</div>
                      </div>
                    ) : (
                      <div className="text-gray-500">Loading...</div>
                    )}
                  </div>

                  {/* Spin Button */}
                  <button
                    onClick={spinWheel}
                    disabled={!wheelStatus?.can_spin || isSpinning}
                    className={`btn-enhanced px-8 py-4 rounded-lg font-bold text-lg transition-all ${
                      wheelStatus?.can_spin && !isSpinning
                        ? 'hover:scale-110 cursor-pointer'
                        : 'opacity-50 cursor-not-allowed'
                    }`}
                    style={{
                      backgroundColor: wheelStatus?.can_spin && !isSpinning ? 'var(--accent-color)' : 'var(--bg-tertiary)',
                      color: wheelStatus?.can_spin && !isSpinning ? 'var(--bg-primary)' : 'var(--text-muted)'
                    }}
                  >
                    {isSpinning ? 'Spinning...' : 'Spin the Wheel!'}
                  </button>

                  {/* Result Display */}
                  {wheelResult && (
                    <div className="mt-6 p-4 rounded-lg" style={{ backgroundColor: 'var(--bg-secondary)' }}>
                      <div className="text-xl font-bold text-green-500 mb-2">
                        🎉 Congratulations!
                      </div>
                      <div className="text-lg">
                        You won <span className="font-bold text-yellow-500">{wheelResult.reward} FC</span>!
                      </div>
                    </div>
                  )}

                  {/* Possible Rewards Info */}
                  <div className="mt-8 text-sm opacity-70">
                    <div className="font-semibold mb-2">Possible Rewards:</div>
                    <div>10 FC - 100 FC (Random)</div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <LockedTabContent requiredLevel={6} />
          )
        )}

        {/* Leaderboard Tab */}
        {activeTab === 'leaderboard' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-center">Leaderboard</h2>
            
            <div className="card-enhanced rounded-lg overflow-hidden">
              {users
                .sort((a, b) => b.credits - a.credits)
                .slice(0, 10)
                .map((user, index) => (
                  <div key={user.id} className={`leaderboard-item flex justify-between items-center p-4 border-b last:border-b-0 ${
                    user.id === currentUser.id ? 'bg-yellow-100' : ''
                  } ${
                    index === 0 ? 'leaderboard-gold' :
                    index === 1 ? 'leaderboard-silver' :
                    index === 2 ? 'leaderboard-bronze' : ''
                  }`}>
                    <div className="flex items-center space-x-4">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                        index < 3 ? 'text-white' : ''
                      }`} style={{ 
                        backgroundColor: index >= 3 ? 'var(--bg-tertiary)' : 'transparent',
                        color: index >= 3 ? 'var(--text-primary)' : 'inherit'
                      }}>
                        {index + 1}
                      </div>
                      <div>
                        <div className="font-semibold flex items-center">
                          <span 
                            className="clickable-username"
                            onClick={() => handleUserClick(user)}
                          >
                            {user.username}
                          </span>
                          {user.level > 1 && (
                            <span className="ml-2 bg-yellow-400 text-black px-2 py-1 rounded text-xs font-bold">
                              L{user.level}
                            </span>
                          )}
                        </div>
                        <div className="text-sm opacity-70">
                          {user.total_focus_time} min focused • {user.credit_rate_multiplier.toFixed(1)}x rate • {user.completed_tasks} tasks
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xl font-bold">{user.credits}</div>
                      <div className="text-sm opacity-70">FC</div>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* Activity Tab */}
        {activeTab === 'activity' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-center">Activity Feed</h2>
            
            <div className="card-enhanced rounded-lg overflow-hidden">
              {notifications.length === 0 ? (
                <div className="p-8 text-center opacity-70">
                  No recent activity. Start focusing or complete tasks to see updates!
                </div>
              ) : (
                notifications.map((notification, index) => (
                  <div key={notification.id} className={`activity-item p-4 border-b last:border-b-0 ${
                    notification.user_id === currentUser.id && !notification.is_read ? 'bg-yellow-50' : ''
                  }`} style={{ animationDelay: `${index * 0.1}s` }}>
                    <div className="flex justify-between items-start">
                      <div>
                        <div className={`font-medium ${
                          notification.notification_type === 'pass_used' ? 'text-red-600' :
                          notification.notification_type === 'task_completed' ? 'text-green-600' :
                          notification.notification_type === 'ally_formed' ? 'text-blue-600' :
                          ''
                        }`} style={{ color: 'var(--text-primary)' }}>
                          {notification.message}
                        </div>
                        <div className="text-xs opacity-60 mt-1">
                          {notification.notification_type.replace('_', ' ').toUpperCase()}
                        </div>
                      </div>
                      <div className="text-right text-sm opacity-70">
                        <div>{new Date(notification.timestamp).toLocaleString()}</div>
                        {notification.user_id === currentUser.id && !notification.is_read && (
                          <div className="text-xs text-red-500 mt-1">NEW</div>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>

      {/* User Profile Modal */}
      <UserProfileModal 
        user={selectedUser} 
        isOpen={showUserProfile} 
        onClose={() => setShowUserProfile(false)} 
      />

      {/* User Settings Modal */}
      <UserSettingsModal 
        isOpen={showSettings} 
        onClose={() => setShowSettings(false)}
        currentUser={currentUser}
        onUpdateUser={handleUpdateUser}
      />
    </div>
  );
}

// Main App Component with Theme Provider
const AppWithTheme = () => {
  return (
    <ThemeProvider>
      <App />
    </ThemeProvider>
  );
};

export default AppWithTheme;