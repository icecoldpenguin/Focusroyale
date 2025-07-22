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
  const [recentPurchases, setRecentPurchases] = useState([]);
  const [focusSession, setFocusSession] = useState(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');

  // Initialize data on component mount
  useEffect(() => {
    initializeData();
    
    // Set up polling for real-time updates
    const interval = setInterval(() => {
      if (currentUser) {
        fetchActiveUsers();
        fetchUsers();
        fetchRecentPurchases();
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [currentUser]);

  const initializeData = async () => {
    try {
      // Initialize shop items
      await axios.post(`${API}/init`);
      await fetchShopItems();
      await fetchUsers();
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

  const fetchRecentPurchases = async () => {
    try {
      const response = await axios.get(`${API}/shop/purchases`);
      setRecentPurchases(response.data);
    } catch (error) {
      console.error('Failed to fetch recent purchases:', error);
    }
  };

  const createUser = async (username) => {
    try {
      const response = await axios.post(`${API}/users`, { username });
      setCurrentUser(response.data);
      await fetchUsers();
      return response.data;
    } catch (error) {
      console.error('Failed to create user:', error);
      alert(error.response?.data?.detail || 'Failed to create user');
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
      
      alert(`Session ended! You earned ${response.data.credits_earned} credits in ${response.data.duration_minutes} minutes.`);
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
      await fetchRecentPurchases();
      
      alert(`Successfully purchased ${response.data.item_name}!`);
    } catch (error) {
      console.error('Failed to purchase item:', error);
      alert(error.response?.data?.detail || 'Failed to purchase item');
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
          <h1 className="text-3xl font-bold text-center mb-6">Focus Royale</h1>
          <p className="text-gray-300 text-center mb-6">
            Turn focus into currency. Strategy decides who rises.
          </p>
          
          <form onSubmit={(e) => {
            e.preventDefault();
            const username = e.target.username.value.trim();
            if (username) {
              createUser(username);
            }
          }}>
            <input
              type="text"
              name="username"
              placeholder="Enter your username"
              className="w-full p-3 bg-gray-800 text-white rounded mb-4 focus:outline-none focus:ring-2 focus:ring-gray-600"
              required
            />
            <button
              type="submit"
              className="w-full bg-white text-black p-3 rounded font-semibold hover:bg-gray-200 transition-colors"
            >
              Enter the Arena
            </button>
          </form>
          
          {users.length > 0 && (
            <div className="mt-6">
              <p className="text-gray-300 text-sm mb-2">Or select existing user:</p>
              <div className="space-y-2">
                {users.map(user => (
                  <button
                    key={user.id}
                    onClick={() => setCurrentUser(user)}
                    className="block w-full text-left p-2 bg-gray-800 hover:bg-gray-700 rounded transition-colors"
                  >
                    {user.username} ({user.credits} credits)
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white text-black">
      {/* Header */}
      <header className="bg-black text-white p-4">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold">Focus Royale</h1>
          <div className="flex items-center space-x-6">
            <div className="text-right">
              <div className="text-lg font-semibold">{currentUser.username}</div>
              <div className="text-gray-300">{currentUser.credits} credits</div>
              <div className="text-sm text-gray-400">
                Rate: {currentUser.credit_rate_multiplier.toFixed(1)}x
              </div>
            </div>
            <button
              onClick={() => setCurrentUser(null)}
              className="bg-gray-800 hover:bg-gray-700 px-3 py-1 rounded transition-colors"
            >
              Switch User
            </button>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-gray-100 border-b">
        <div className="max-w-6xl mx-auto">
          <div className="flex space-x-8">
            {['dashboard', 'shop', 'leaderboard', 'activity'].map(tab => (
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
                  <p className="text-gray-600 mb-4">Ready to earn some credits?</p>
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
                      Earning {currentUser.credit_rate_multiplier.toFixed(1)} credits per minute
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
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-black text-white p-4 rounded-lg text-center">
                <div className="text-2xl font-bold">{currentUser.credits}</div>
                <div className="text-gray-300">Total Credits</div>
              </div>
              <div className="bg-black text-white p-4 rounded-lg text-center">
                <div className="text-2xl font-bold">{currentUser.total_focus_time}</div>
                <div className="text-gray-300">Focus Minutes</div>
              </div>
              <div className="bg-black text-white p-4 rounded-lg text-center">
                <div className="text-2xl font-bold">{currentUser.credit_rate_multiplier.toFixed(1)}x</div>
                <div className="text-gray-300">Credit Rate</div>
              </div>
            </div>

            {/* Active Users */}
            {activeUsers.length > 0 && (
              <div className="bg-gray-50 p-6 rounded-lg border">
                <h3 className="text-lg font-semibold mb-3">Currently Focusing</h3>
                <div className="space-y-2">
                  {activeUsers.map(user => (
                    <div key={user.id} className="flex justify-between items-center bg-white p-3 rounded border">
                      <span className="font-medium">{user.username}</span>
                      <div className="flex items-center space-x-3">
                        <span className="text-sm text-gray-600">{user.credits} credits</span>
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
              <p className="text-gray-600">Boost yourself or sabotage others</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
              {shopItems.map(item => (
                <div key={item.id} className={`border-2 rounded-lg p-6 transition-all hover:shadow-lg ${
                  item.item_type === 'sabotage' 
                    ? 'border-red-300 bg-red-50 hover:border-red-400' 
                    : 'border-green-300 bg-green-50 hover:border-green-400'
                }`}>
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="text-lg font-bold">{item.name}</h3>
                    <div className={`px-3 py-1 rounded text-sm font-semibold ${
                      item.item_type === 'sabotage' 
                        ? 'bg-red-600 text-white' 
                        : 'bg-green-600 text-white'
                    }`}>
                      {item.price} credits
                    </div>
                  </div>
                  
                  <p className="text-gray-700 mb-4">{item.description}</p>
                  
                  {item.item_type === 'sabotage' ? (
                    <div>
                      <select 
                        id={`target-${item.id}`}
                        className="w-full p-2 border rounded mb-3"
                        defaultValue=""
                      >
                        <option value="" disabled>Select target user</option>
                        {users.filter(user => user.id !== currentUser.id).map(user => (
                          <option key={user.id} value={user.id}>
                            {user.username} ({user.credits} credits)
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
                        className="w-full bg-red-600 text-white py-2 px-4 rounded font-semibold hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                      >
                        {currentUser.credits < item.price ? 'Insufficient Credits' : 'Deploy Sabotage'}
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => purchaseItem(item.id)}
                      disabled={currentUser.credits < item.price}
                      className="w-full bg-green-600 text-white py-2 px-4 rounded font-semibold hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                    >
                      {currentUser.credits < item.price ? 'Insufficient Credits' : 'Purchase Boost'}
                    </button>
                  )}
                </div>
              ))}
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
                        <div className="font-semibold">{user.username}</div>
                        <div className="text-sm text-gray-600">
                          {user.total_focus_time} min focused • {user.credit_rate_multiplier.toFixed(1)}x rate
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xl font-bold">{user.credits}</div>
                      <div className="text-sm text-gray-600">credits</div>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* Activity Tab */}
        {activeTab === 'activity' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-center">Recent Activity</h2>
            
            <div className="bg-gray-50 rounded-lg border">
              {recentPurchases.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  No recent activity. Be the first to make a move!
                </div>
              ) : (
                recentPurchases.map(purchase => {
                  const purchaser = users.find(u => u.id === purchase.user_id);
                  const target = users.find(u => u.id === purchase.target_user_id);
                  const item = shopItems.find(i => i.id === purchase.item_id);
                  
                  return (
                    <div key={purchase.id} className="p-4 border-b last:border-b-0">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="font-semibold">
                            {purchaser?.username || 'Unknown'} purchased "{item?.name || 'Unknown Item'}"
                          </div>
                          {target && (
                            <div className="text-sm text-red-600 mt-1">
                              → Targeted {target.username}
                            </div>
                          )}
                        </div>
                        <div className="text-right text-sm text-gray-600">
                          <div>{purchase.price} credits</div>
                          <div>{new Date(purchase.timestamp).toLocaleString()}</div>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;