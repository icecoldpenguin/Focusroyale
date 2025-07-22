import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [users, setUsers] = useState([]);
  const [activeUsers, setActiveUsers] = useState([]);
  const [shopItems, setShopItems] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [focusSession, setFocusSession] = useState(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [authMode, setAuthMode] = useState('login'); // 'login' or 'register'
  const [authForm, setAuthForm] = useState({ username: '', password: '' });
  const [newTask, setNewTask] = useState({ title: '', description: '' });

  // Initialize data on component mount
  useEffect(() => {
    initializeData();
  }, []);

  // Set up polling for real-time updates when user is logged in
  useEffect(() => {
    if (currentUser) {
      fetchTasks(); // Initial fetch when user logs in
      const interval = setInterval(() => {
        fetchActiveUsers();
        fetchUsers();
        fetchNotifications();
        fetchTasks();
      }, 3000);

      return () => clearInterval(interval);
    }
  }, [currentUser]);

  const initializeData = async () => {
    try {
      // Initialize shop items
      await axios.post(`${API}/init`);
      await fetchShopItems();
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

  const createTask = async (title, description) => {
    if (!currentUser) return;
    
    try {
      const response = await axios.post(`${API}/tasks`, {
        user_id: currentUser.id,
        title: title.trim(),
        description: description.trim()
      });
      
      await fetchTasks(); // Refresh task list
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
      
      // Update current user data
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
      
      // Update current user data
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
      
      // Update current user data
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

  const resetDatabase = async () => {
    if (window.confirm('Are you sure you want to reset the entire database? This will remove all users and data.')) {
      try {
        await axios.post(`${API}/admin/reset-database`);
        setCurrentUser(null);
        setUsers([]);
        setActiveUsers([]);
        setNotifications([]);
        alert('Database reset successfully!');
      } catch (error) {
        console.error('Failed to reset database:', error);
        alert('Failed to reset database');
      }
    }
  };

  if (!isInitialized) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-black text-xl">Initializing Focus Royale...</div>
      </div>
    );
  }

  if (!currentUser) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="bg-black text-white p-8 rounded-lg shadow-2xl max-w-md w-full mx-4">
          <h1 className="text-3xl font-bold text-center mb-2">Focus Royale</h1>
          <p className="text-gray-300 text-center mb-6">
            Turn focus into currency. Strategy decides who rises.
          </p>
          
          {/* Auth Mode Toggle */}
          <div className="flex bg-gray-800 rounded-lg p-1 mb-6">
            <button
              onClick={() => setAuthMode('login')}
              className={`flex-1 py-2 px-4 rounded-md transition-colors ${
                authMode === 'login' ? 'bg-white text-black' : 'text-gray-300 hover:text-white'
              }`}
            >
              Login
            </button>
            <button
              onClick={() => setAuthMode('register')}
              className={`flex-1 py-2 px-4 rounded-md transition-colors ${
                authMode === 'register' ? 'bg-white text-black' : 'text-gray-300 hover:text-white'
              }`}
            >
              Register
            </button>
          </div>
          
          <form onSubmit={handleAuth}>
            <input
              type="text"
              placeholder="Username"
              value={authForm.username}
              onChange={(e) => setAuthForm({...authForm, username: e.target.value})}
              className="w-full p-3 bg-gray-800 text-white rounded mb-4 focus:outline-none focus:ring-2 focus:ring-gray-600"
              required
            />
            <input
              type="password"
              placeholder="Password"
              value={authForm.password}
              onChange={(e) => setAuthForm({...authForm, password: e.target.value})}
              className="w-full p-3 bg-gray-800 text-white rounded mb-4 focus:outline-none focus:ring-2 focus:ring-gray-600"
              required
            />
            <button
              type="submit"
              className="w-full bg-white text-black p-3 rounded font-semibold hover:bg-gray-200 transition-colors"
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
    <div className="min-h-screen bg-white text-black">
      {/* Header */}
      <header className="bg-black text-white p-4">
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
              <div className="text-gray-300">{currentUser.credits} FC</div>
              <div className="text-sm text-gray-400">
                Rate: {currentUser.credit_rate_multiplier.toFixed(1)}x
              </div>
            </div>
            {unreadNotifications.length > 0 && (
              <div className="bg-red-500 text-white px-2 py-1 rounded-full text-xs">
                {unreadNotifications.length}
              </div>
            )}
            <button
              onClick={() => setCurrentUser(null)}
              className="bg-gray-800 hover:bg-gray-700 px-3 py-1 rounded transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-gray-100 border-b">
        <div className="max-w-6xl mx-auto">
          <div className="flex space-x-8">
            {['dashboard', 'shop', 'tasks', 'leaderboard', 'activity'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-3 px-4 border-b-2 transition-colors capitalize ${
                  activeTab === tab 
                    ? 'border-black text-black font-semibold' 
                    : 'border-transparent text-gray-600 hover:text-black'
                }`}
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
            <div className="bg-gray-50 p-6 rounded-lg border-2 border-gray-200">
              <h2 className="text-xl font-bold mb-4">Focus Session</h2>
              
              {!focusSession ? (
                <div className="text-center">
                  <p className="text-gray-600 mb-4">
                    Ready to earn some Focus Credits (FC)? <br />
                    <span className="text-sm text-gray-500">10 FC per hour • Rate: {currentUser.credit_rate_multiplier.toFixed(1)}x</span>
                  </p>
                  <button
                    onClick={startFocusSession}
                    className="bg-black text-white px-8 py-3 rounded-lg font-semibold hover:bg-gray-800 transition-colors"
                  >
                    Start Focus Session
                  </button>
                </div>
              ) : (
                <div className="text-center">
                  <div className="bg-green-100 border-2 border-green-300 p-4 rounded-lg mb-4">
                    <div className="text-2xl font-bold text-green-800 mb-2">FOCUSING</div>
                    <div className="text-green-700">
                      Started at {new Date(focusSession.start_time).toLocaleTimeString()}
                    </div>
                    <div className="text-sm text-green-600 mt-2">
                      Earning {(10 * currentUser.credit_rate_multiplier).toFixed(1)} FC per hour
                    </div>
                  </div>
                  <button
                    onClick={endFocusSession}
                    className="bg-red-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-red-700 transition-colors"
                  >
                    End Session
                  </button>
                </div>
              )}
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-black text-white p-4 rounded-lg text-center">
                <div className="text-2xl font-bold">{currentUser.credits}</div>
                <div className="text-gray-300">Focus Credits</div>
              </div>
              <div className="bg-black text-white p-4 rounded-lg text-center">
                <div className="text-2xl font-bold">{currentUser.total_focus_time}</div>
                <div className="text-gray-300">Focus Minutes</div>
              </div>
              <div className="bg-black text-white p-4 rounded-lg text-center">
                <div className="text-2xl font-bold">{currentUser.credit_rate_multiplier.toFixed(1)}x</div>
                <div className="text-gray-300">Credit Rate</div>
              </div>
              <div className="bg-black text-white p-4 rounded-lg text-center">
                <div className="text-2xl font-bold">{currentUser.completed_tasks}</div>
                <div className="text-gray-300">Tasks Done</div>
              </div>
            </div>

            {/* Active Users */}
            {activeUsers.length > 0 && (
              <div className="bg-gray-50 p-6 rounded-lg border">
                <h3 className="text-lg font-semibold mb-3">Currently Focusing</h3>
                <div className="space-y-2">
                  {activeUsers.map(user => (
                    <div key={user.id} className="flex justify-between items-center bg-white p-3 rounded border">
                      <span className="font-medium flex items-center">
                        {user.username}
                        {user.level > 1 && (
                          <span className="ml-2 bg-yellow-400 text-black px-1.5 py-0.5 rounded text-xs">
                            L{user.level}
                          </span>
                        )}
                      </span>
                      <div className="flex items-center space-x-3">
                        <span className="text-sm text-gray-600">{user.credits} FC</span>
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
              <p className="text-gray-600">Boost yourself or target others with passes</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {shopItems.map(item => (
                <div key={item.id} className={`border-2 rounded-lg p-6 transition-all hover:shadow-lg ${
                  item.item_type === 'sabotage' 
                    ? 'border-red-300 bg-red-50 hover:border-red-400' 
                    : item.item_type === 'special'
                    ? 'border-blue-300 bg-blue-50 hover:border-blue-400'
                    : 'border-green-300 bg-green-50 hover:border-green-400'
                }`}>
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="text-lg font-bold flex items-center">
                      <span className="text-2xl mr-2">{item.emoji}</span>
                      {item.name}
                    </h3>
                    <div className={`px-3 py-1 rounded text-sm font-semibold text-white ${
                      item.item_type === 'sabotage' ? 'bg-red-600' 
                      : item.item_type === 'special' ? 'bg-blue-600'
                      : 'bg-green-600'
                    }`}>
                      {item.price} FC
                    </div>
                  </div>
                  
                  <p className="text-gray-700 mb-4 text-sm">{item.description}</p>
                  
                  {item.requires_target ? (
                    <div>
                      <select 
                        id={`target-${item.id}`}
                        className="w-full p-2 border rounded mb-3 text-sm"
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
                        className={`w-full py-2 px-4 rounded font-semibold transition-colors text-white ${
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
                      className={`w-full py-2 px-4 rounded font-semibold transition-colors text-white ${
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
              <p className="text-gray-600">Create and complete your own tasks to earn 3 FC each</p>
            </div>
            
            {/* Task Creation Form */}
            <div className="bg-gray-50 border-2 border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-bold mb-4">Create New Task</h3>
              <form onSubmit={handleCreateTask} className="space-y-4">
                <div>
                  <input
                    type="text"
                    placeholder="Task title (e.g., Read for 30 minutes)"
                    value={newTask.title}
                    onChange={(e) => setNewTask({...newTask, title: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-400"
                    maxLength={100}
                  />
                </div>
                <div>
                  <textarea
                    placeholder="Task description (optional)"
                    value={newTask.description}
                    onChange={(e) => setNewTask({...newTask, description: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-400 resize-none"
                    rows="3"
                    maxLength={300}
                  />
                </div>
                <button
                  type="submit"
                  className="bg-black text-white px-6 py-2 rounded-lg font-semibold hover:bg-gray-800 transition-colors"
                >
                  Create Task
                </button>
              </form>
            </div>
            
            {/* Tasks List */}
            <div>
              <h3 className="text-lg font-semibold mb-4">Your Active Tasks</h3>
              {tasks.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p>No tasks yet. Create your first task above!</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {tasks.map(task => (
                    <div key={task.id} className="bg-gray-50 border-2 border-gray-200 rounded-lg p-6 hover:shadow-lg transition-all">
                      <h4 className="text-lg font-bold mb-2">{task.title}</h4>
                      {task.description && (
                        <p className="text-gray-600 mb-4 text-sm">{task.description}</p>
                      )}
                      
                      <div className="flex justify-between items-center">
                        <span className="text-green-600 font-semibold">+{task.credits_reward} FC</span>
                        <button
                          onClick={() => completeTask(task.id)}
                          className="bg-green-600 text-white px-4 py-2 rounded font-semibold hover:bg-green-700 transition-colors"
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
            
            <div className="bg-gray-50 rounded-lg border">
              {users
                .sort((a, b) => b.credits - a.credits)
                .slice(0, 10)
                .map((user, index) => (
                  <div key={user.id} className={`flex justify-between items-center p-4 border-b last:border-b-0 ${
                    user.id === currentUser.id ? 'bg-yellow-100' : ''
                  }`}>
                    <div className="flex items-center space-x-4">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                        index === 0 ? 'bg-yellow-500 text-white' :
                        index === 1 ? 'bg-gray-400 text-white' :
                        index === 2 ? 'bg-amber-600 text-white' :
                        'bg-gray-200 text-gray-700'
                      }`}>
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
                        <div className="text-sm text-gray-600">
                          {user.total_focus_time} min focused • {user.credit_rate_multiplier.toFixed(1)}x rate • {user.completed_tasks} tasks
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xl font-bold">{user.credits}</div>
                      <div className="text-sm text-gray-600">FC</div>
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
            
            <div className="bg-gray-50 rounded-lg border">
              {notifications.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  No recent activity. Start focusing or complete tasks to see updates!
                </div>
              ) : (
                notifications.map(notification => (
                  <div key={notification.id} className={`p-4 border-b last:border-b-0 ${
                    notification.user_id === currentUser.id && !notification.is_read ? 'bg-yellow-50' : ''
                  }`}>
                    <div className="flex justify-between items-start">
                      <div>
                        <div className={`font-medium ${
                          notification.notification_type === 'pass_used' ? 'text-red-600' :
                          notification.notification_type === 'task_completed' ? 'text-green-600' :
                          notification.notification_type === 'ally_formed' ? 'text-blue-600' :
                          'text-gray-800'
                        }`}>
                          {notification.message}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          {notification.notification_type.replace('_', ' ').toUpperCase()}
                        </div>
                      </div>
                      <div className="text-right text-sm text-gray-600">
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

export default App;