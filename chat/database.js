const sqlite3 = require('sqlite3').verbose();
const path = require('path');

class Database {
    constructor() {
        const dbPath = process.env.DB_PATH || '/data/chat.db';
        
        // Ensure directory exists
        const fs = require('fs');
        const dir = path.dirname(dbPath);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
        
        this.db = new sqlite3.Database(dbPath, (err) => {
            if (err) {
                console.error('Error opening database:', err);
            } else {
                console.log('Connected to SQLite database');
                this.initTables();
            }
        });
    }
    
    initTables() {
        const createMessagesTable = `
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT NOT NULL,
                sent_at INTEGER NOT NULL,
                text TEXT NOT NULL
            )
        `;
        
        const createIndex = `
            CREATE INDEX IF NOT EXISTS idx_messages_time ON messages(sent_at)
        `;
        
        this.db.serialize(() => {
            this.db.run(createMessagesTable);
            this.db.run(createIndex);
        });
    }
    
    async saveMessage(user, text) {
        return new Promise((resolve, reject) => {
            const sentAt = Date.now();
            const query = 'INSERT INTO messages (user, sent_at, text) VALUES (?, ?, ?)';
            
            this.db.run(query, [user, sentAt, text], function(err) {
                if (err) {
                    reject(err);
                } else {
                    // Clean up old messages (keep only last 100)
                    const cleanupQuery = `
                        DELETE FROM messages 
                        WHERE id < (
                            SELECT id FROM messages 
                            ORDER BY id DESC 
                            LIMIT 1 OFFSET 100
                        )
                    `;
                    
                    this.db.run(cleanupQuery);
                    
                    resolve({
                        id: this.lastID,
                        user: user,
                        sent_at: sentAt,
                        text: text
                    });
                }
            });
        });
    }
    
    async getRecentMessages(limit = 100) {
        return new Promise((resolve, reject) => {
            const query = `
                SELECT id, user, sent_at, text 
                FROM messages 
                ORDER BY sent_at DESC 
                LIMIT ?
            `;
            
            this.db.all(query, [limit], (err, rows) => {
                if (err) {
                    reject(err);
                } else {
                    // Reverse to get chronological order
                    resolve(rows.reverse());
                }
            });
        });
    }
    
    async getMessageCount() {
        return new Promise((resolve, reject) => {
            const query = 'SELECT COUNT(*) as count FROM messages';
            
            this.db.get(query, (err, row) => {
                if (err) {
                    reject(err);
                } else {
                    resolve(row.count);
                }
            });
        });
    }
    
    close() {
        this.db.close((err) => {
            if (err) {
                console.error('Error closing database:', err);
            } else {
                console.log('Database connection closed');
            }
        });
    }
}

module.exports = Database;
