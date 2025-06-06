const express = require('express');
const { createServer } = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const helmet = require('helmet');
const { RateLimiterMemory } = require('rate-limiter-flexible');
const Database = require('./database');
const RedisClient = require('./redis');

const app = express();
const server = createServer(app);

// Security middleware
app.use(helmet());
app.use(cors({
    origin: process.env.NODE_ENV === 'production' ? false : true,
    credentials: true
}));

// Rate limiting
const rateLimiter = new RateLimiterMemory({
    keyGenerator: (req, res, next) => req.ip,
    points: 10, // Number of requests
    duration: 60, // Per 60 seconds
});

// Socket.IO setup
const io = new Server(server, {
    cors: {
        origin: process.env.NODE_ENV === 'production' ? false : true,
        methods: ["GET", "POST"]
    },
    transports: ['websocket', 'polling']
});

// Message rate limiting for Socket.IO
const messageRateLimiter = new RateLimiterMemory({
    points: 5, // Number of messages
    duration: 60, // Per 60 seconds
});

// Initialize database and Redis
const db = new Database();
const redis = new RedisClient();

// Health check endpoint
app.get('/health', (req, res) => {
    res.status(200).json({ status: 'healthy', timestamp: Date.now() });
});

// Socket.IO connection handling
io.on('connection', async (socket) => {
    console.log(`User connected: ${socket.id}`);
    
    // Send chat history to new user
    try {
        const history = await db.getRecentMessages(100);
        socket.emit('chat:history', history);
    } catch (error) {
        console.error('Error fetching chat history:', error);
    }
    
    // Handle chat messages
    socket.on('chat:send', async (data) => {
        try {
            // Rate limiting
            await messageRateLimiter.consume(socket.handshake.address);
            
            const { text, user } = data;
            
            // Validate message
            if (!text || !user || text.trim().length === 0) {
                socket.emit('chat:error', { message: 'Invalid message' });
                return;
            }
            
            if (text.length > 500) {
                socket.emit('chat:error', { message: 'Message too long' });
                return;
            }
            
            // Clean and sanitize message
            const cleanText = text.trim().substring(0, 500);
            const cleanUser = user.trim().substring(0, 50);
            
            // Save message to database
            const message = await db.saveMessage(cleanUser, cleanText);
            
            // Broadcast message to all connected clients
            io.emit('chat:new', {
                id: message.id,
                user: message.user,
                text: message.text,
                time: message.sent_at
            });
            
            // Publish to Redis for potential cross-instance communication
            await redis.publish('chat:message', JSON.stringify({
                user: message.user,
                text: message.text,
                time: message.sent_at
            }));
            
        } catch (rateLimiterRes) {
            if (rateLimiterRes.remainingPoints !== undefined) {
                socket.emit('chat:error', { 
                    message: 'Rate limit exceeded. Please slow down.' 
                });
            } else {
                console.error('Error handling chat message:', rateLimiterRes);
                socket.emit('chat:error', { 
                    message: 'Failed to send message' 
                });
            }
        }
    });
    
    // Handle user typing indicator
    socket.on('chat:typing', (data) => {
        socket.broadcast.emit('chat:typing', {
            user: data.user,
            isTyping: data.isTyping
        });
    });
    
    // Handle disconnection
    socket.on('disconnect', () => {
        console.log(`User disconnected: ${socket.id}`);
    });
});

// Subscribe to Redis messages for cross-instance communication
redis.subscribe('chat:message', (message) => {
    try {
        const data = JSON.parse(message);
        io.emit('chat:new', data);
    } catch (error) {
        console.error('Error processing Redis message:', error);
    }
});

// Graceful shutdown
process.on('SIGTERM', async () => {
    console.log('SIGTERM received, shutting down gracefully');
    server.close(() => {
        db.close();
        redis.disconnect();
        process.exit(0);
    });
});

process.on('SIGINT', async () => {
    console.log('SIGINT received, shutting down gracefully');
    server.close(() => {
        db.close();
        redis.disconnect();
        process.exit(0);
    });
});

// Start server
const PORT = process.env.PORT || 7000;
server.listen(PORT, () => {
    console.log(`Chat server running on port ${PORT}`);
});
