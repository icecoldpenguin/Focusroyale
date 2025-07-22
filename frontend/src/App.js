import React, { useState, useEffect, createContext, useContext } from "react";
import "./App.css";
import axios from "axios";
import ThreeBackground from "./ThreeBackground";

// Theme Context
const ThemeContext = createContext();
const useTheme = () => useContext(ThemeContext);

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

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

// Floating Doodles Component
const FloatingDoodles = ({ darkMode }) => {
  const doodles = [
    { icon: '⚡', size: '2rem', top: '10%', left: '15%', delay: '0s' },
    { icon: '🎯', size: '1.5rem', top: '20%', right: '20%', delay: '2s' },
    { icon: '⭐', size: '1.8rem', top: '70%', left: '10%', delay: '4s' },
    { icon: '💎', size: '1.6rem', bottom: '15%', right: '15%', delay: '1s' },
    { icon: '🚀', size: '2.2rem', top: '50%', left: '5%', delay: '3s' },
    { icon: '🔥', size: '1.4rem', top: '80%', right: '10%', delay: '5s' },
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
            opacity: darkMode ? 0.3 : 0.2,
          }}
        >
          {doodle.icon}
        </div>
      ))}
    </>
  );
};

// Theme Toggle Component
const ThemeToggle = () => {
  const { darkMode, toggleTheme } = useTheme();
  
  return (
    <div
      className={`theme-toggle ${darkMode ? 'dark' : ''}`}
      onClick={toggleTheme}
      title={`Switch to ${darkMode ? 'light' : 'dark'} mode`}
    />
  );
};

function App() {
  const { darkMode } = useTheme();
  const [currentUser, setCurrentUser] = useState(null);
  const [users, setUsers] = useState([]);
  const [activeUsers, setActiveUsers] = useState([]);
  const [shopItems, setShopItems] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [focusSession, setFocusSession] = useState(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [authMode, setAuthMode] = useState('login');
  const [authForm, setAuthForm] = useState({ username: '', password: '' });
  const [newTask, setNewTask] = useState({ title: '', description: '' });
  const [socialRate, setSocialRate] = useState({ active_users_count: 0, social_multiplier: 1.0, credits_per_hour: 10 });

  // beforeunload handler to prevent tab close during active focus session
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (focusSession) {
        e.preventDefault();
        e.returnValue = 'You have an active focus session. Please end your session before leaving to save your progress.';
        return e.returnValue;
      }
    };

    if (focusSession) {
      window.addEventListener('beforeunload', handleBeforeUnload);
    }

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [focusSession]);

  // Initialize data on component mount
  useEffect(() => {
    initializeData();
  }, []);

  // Set up polling for real-time updates when user is logged in
  useEffect(() => {
    if (currentUser) {
      fetchTasks();
      fetchSocialRate();
      const interval = setInterval(() => {
        fetchActiveUsers();
        fetchUsers();
        fetchNotifications();
        fetchTasks();
        fetchSocialRate();
      }, 3000);

      return () => clearInterval(interval);
    }
  }, [currentUser]);

  const initializeData = async () => {
    try {
      await axios.post(`${API}/init`);
      await fetchShopItems();
      await fetchSocialRate();
      setIsInitialized(true);
    } catch (error) {
      console.error('Failed to initialize:', error);
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

  const fetchSocialRate = async () => {
    try {
      const response = await axios.get(`${API}/focus/social-rate`);
      setSocialRate(response.data);
    } catch (error) {
      console.error('Failed to fetch social rate:', error);
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
      alert('Please fill in all fields');
      return;
    }

    try {
      const endpoint = authMode === 'login' ? 'login' : 'register';
      const response = await axios.post(`${API}/auth/${endpoint}`, {
        username: authForm.username.trim(),
        password: authForm.password
      });
      
      setCurrentUser(response.data.user);
      setAuthForm({ username: '', password: '' });
      await fetchUsers();
      await fetchNotifications();
      await fetchTasks();
      
    } catch (error) {
      console.error('Auth failed:', error);
      alert(error.response?.data?.detail || `${authMode} failed`);
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
      setCurrentUser(updatedUser.data);
      
      await fetchUsers();
      await fetchNotifications();
      
      alert(`Task completed! You earned ${response.data.credits_earned} credits.`);
    } catch (error) {
      console.error('Failed to complete task:', error);
      alert(error.response?.data?.detail || 'Failed to complete task');
    }
  };

  const handleCreateTask = async (e) => {
    e.preventDefault();
    
    if (!newTask.title.trim()) {
      alert('Please enter a task title');
      return;
    }

    try {
      await createTask(newTask.title, newTask.description);
      setNewTask({ title: '', description: '' });
      alert('Task created successfully!');
    } catch (error) {
      console.error('Failed to create task:', error);
      alert(error.response?.data?.detail || 'Failed to create task');
    }
  };

  const startFocusSession = async () => {
    if (!currentUser) return;
    
    try {
      const response = await axios.post(`${API}/focus/start`, { 
        user_id: currentUser.id 
      });
      setFocusSession(response.data);
      await fetchActiveUsers();
    } catch (error) {
      console.error('Failed to start focus session:', error);
      alert(error.response?.data?.detail || 'Failed to start focus session');
    }
  };

  const endFocusSession = async () => {
    if (!currentUser) return;
    
    try {
      const response = await axios.post(`${API}/focus/end`, { 
        user_id: currentUser.id 
      });
      setFocusSession(null);
      
      const updatedUser = await axios.get(`${API}/users/${currentUser.id}`);
      setCurrentUser(updatedUser.data);
      
      await fetchActiveUsers();
      await fetchUsers();
      
      alert(`Session ended! You earned ${response.data.credits_earned} credits in ${response.data.duration_minutes} minutes (Rate: ${response.data.effective_rate.toFixed(1)}x).`);
    } catch (error) {
      console.error('Failed to end focus session:', error);
      alert(error.response?.data?.detail || 'Failed to end focus session');
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
      setCurrentUser(updatedUser.data);
      
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

  if (!isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
        <div className="text-xl">
          <div className="loading-spinner inline-block mr-3"></div>
          Initializing Focus Royale...
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
          <h1 className="login-title text-3xl font-bold text-center mb-2">Focus Royale</h1>
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

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
      {/* Header */}
      <header className="header-container p-4">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold">Focus Royale</h1>
          <div className="flex items-center space-x-6">
            <div className="text-right">
              <div className="text-lg font-semibold flex items-center">
                {currentUser.username}
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
            <ThemeToggle />
            <button
              onClick={() => setCurrentUser(null)}
              className="btn-enhanced px-3 py-1 rounded"
              style={{ backgroundColor: 'var(--bg-tertiary)' }}
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
            {['dashboard', 'shop', 'tasks', 'leaderboard', 'activity'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`nav-tab py-3 px-4 border-b-2 transition-all capitalize ${
                  activeTab === tab 
                    ? 'active border-black font-semibold' 
                    : 'border-transparent opacity-70 hover:opacity-100'
                }`}
                style={{
                  borderColor: activeTab === tab ? 'var(--accent-color)' : 'transparent',
                  color: 'var(--text-primary)'
                }}
              >
                {tab}
              </button>
            ))}
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
                      Earning {(socialRate.social_multiplier * currentUser.credit_rate_multiplier * 10).toFixed(1)} FC per hour
                    </div>
                    <div className="text-xs text-green-600">
                      Social: {socialRate.social_multiplier.toFixed(1)}x • Personal: {currentUser.credit_rate_multiplier.toFixed(1)}x
                    </div>
                  </div>
                  <button
                    onClick={endFocusSession}
                    className="btn-enhanced bg-red-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-red-700"
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
                  {activeUsers.map(user => (
                    <div key={user.id} className="activity-item flex justify-between items-center p-3 rounded">
                      <span className="font-medium flex items-center">
                        {user.username}
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
              {shopItems.map(item => (
                <div key={item.id} className={`card-enhanced rounded-lg p-6 ${
                  item.item_type === 'sabotage' ? 'shop-item-sabotage' :
                  item.item_type === 'special' ? 'shop-item-special' : 'shop-item-boost'
                }`}>
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="text-lg font-bold flex items-center">
                      <span className="text-2xl mr-2">{item.emoji}</span>
                      {item.name}
                    </h3>
                    <div className={`px-3 py-1 rounded text-sm font-semibold text-white ${
                      item.item_type === 'sabotage' ? 'bg-red-600' :
                      item.item_type === 'special' ? 'bg-blue-600' : 'bg-green-600'
                    }`}>
                      {item.price} FC
                    </div>
                  </div>
                  
                  <p className="opacity-80 mb-4 text-sm">{item.description}</p>
                  
                  {item.requires_target ? (
                    <div>
                      <select 
                        id={`target-${item.id}`}
                        className="form-input w-full p-2 rounded mb-3 text-sm"
                        defaultValue=""
                      >
                        <option value="" disabled>Select target user</option>
                        {users.filter(user => user.id !== currentUser.id).map(user => (
                          <option key={user.id} value={user.id}>
                            {user.username} ({user.credits} FC) L{user.level}
                          </option>
                        ))}
                      </select>
                      <button
                        onClick={() => {
                          const targetSelect = document.getElementById(`target-${item.id}`);
                          const targetUserId = targetSelect.value;
                          if (targetUserId) {
                            purchaseItem(item.id, targetUserId);
                          } else {
                            alert('Please select a target user');
                          }
                        }}
                        disabled={currentUser.credits < item.price}
                        className={`btn-enhanced w-full py-2 px-4 rounded font-semibold text-white ${
                          currentUser.credits < item.price 
                            ? 'bg-gray-400 cursor-not-allowed' 
                            : item.item_type === 'sabotage' 
                            ? 'bg-red-600 hover:bg-red-700'
                            : 'bg-blue-600 hover:bg-blue-700'
                        }`}
                      >
                        {currentUser.credits < item.price ? 'Insufficient FC' : 'Use Pass'}
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
              <p className="opacity-70">Create and complete your own tasks to earn 3 FC each</p>
            </div>
            
            {/* Task Creation Form */}
            <div className="card-enhanced p-6 rounded-lg">
              <h3 className="text-lg font-bold mb-4">Create New Task</h3>
              <form onSubmit={handleCreateTask} className="space-y-4">
                <input
                  type="text"
                  placeholder="Task title (e.g., Read for 30 minutes)"
                  value={newTask.title}
                  onChange={(e) => setNewTask({...newTask, title: e.target.value})}
                  className="form-input w-full p-3 rounded focus:outline-none"
                  maxLength={100}
                />
                <textarea
                  placeholder="Task description (optional)"
                  value={newTask.description}
                  onChange={(e) => setNewTask({...newTask, description: e.target.value})}
                  className="form-input w-full p-3 rounded focus:outline-none resize-none"
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
                  {tasks.map(task => (
                    <div key={task.id} className="card-enhanced p-6 rounded-lg">
                      <h4 className="text-lg font-bold mb-2">{task.title}</h4>
                      {task.description && (
                        <p className="opacity-70 mb-4 text-sm">{task.description}</p>
                      )}
                      
                      <div className="flex justify-between items-center">
                        <span className="text-green-600 font-semibold">+{task.credits_reward} FC</span>
                        <button
                          onClick={() => completeTask(task.id)}
                          className="btn-enhanced bg-green-600 text-white px-4 py-2 rounded font-semibold hover:bg-green-700"
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
                          {user.username}
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