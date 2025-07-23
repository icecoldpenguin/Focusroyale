// MongoDB initialization script for Docker
db = db.getSiblingDB('focus_royale');

// Create collections
db.createCollection('users');
db.createCollection('focus_sessions');
db.createCollection('tasks');
db.createCollection('weekly_tasks');
db.createCollection('shop_items');
db.createCollection('purchases');
db.createCollection('notifications');

// Create indexes for better performance
db.users.createIndex({ "username": 1 }, { unique: true });
db.users.createIndex({ "id": 1 }, { unique: true });
db.focus_sessions.createIndex({ "user_id": 1 });
db.focus_sessions.createIndex({ "is_active": 1 });
db.tasks.createIndex({ "user_id": 1 });
db.weekly_tasks.createIndex({ "user_id": 1, "week_start": 1 });
db.notifications.createIndex({ "user_id": 1, "timestamp": -1 });

print('Database initialized successfully!');