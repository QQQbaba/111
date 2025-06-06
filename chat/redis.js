const redis = require('redis');

class RedisClient {
    constructor() {
        const redisUrl = process.env.REDIS_URL || 'redis://redis:6379';
        
        this.client = redis.createClient({
            url: redisUrl,
            retry_strategy: (options) => {
                if (options.error && options.error.code === 'ECONNREFUSED') {
                    console.error('Redis connection refused');
                    return new Error('Redis connection refused');
                }
                if (options.total_retry_time > 1000 * 60 * 60) {
                    console.error('Redis retry time exhausted');
                    return new Error('Retry time exhausted');
                }
                if (options.attempt > 10) {
                    console.error('Redis max attempts reached');
                    return undefined;
                }
                return Math.min(options.attempt * 100, 3000);
            }
        });
        
        this.subscriber = this.client.duplicate();
        
        this.client.on('error', (err) => {
            console.error('Redis client error:', err);
        });
        
        this.client.on('connect', () => {
            console.log('Connected to Redis');
        });
        
        this.subscriber.on('error', (err) => {
            console.error('Redis subscriber error:', err);
        });
        
        this.connect();
    }
    
    async connect() {
        try {
            await this.client.connect();
            await this.subscriber.connect();
        } catch (error) {
            console.error('Failed to connect to Redis:', error);
        }
    }
    
    async publish(channel, message) {
        try {
            await this.client.publish(channel, message);
        } catch (error) {
            console.error('Failed to publish to Redis:', error);
        }
    }
    
    async subscribe(channel, callback) {
        try {
            await this.subscriber.subscribe(channel, callback);
        } catch (error) {
            console.error('Failed to subscribe to Redis channel:', error);
        }
    }
    
    async set(key, value, expireSeconds = null) {
        try {
            if (expireSeconds) {
                await this.client.setEx(key, expireSeconds, value);
            } else {
                await this.client.set(key, value);
            }
        } catch (error) {
            console.error('Failed to set Redis key:', error);
        }
    }
    
    async get(key) {
        try {
            return await this.client.get(key);
        } catch (error) {
            console.error('Failed to get Redis key:', error);
            return null;
        }
    }
    
    async del(key) {
        try {
            await this.client.del(key);
        } catch (error) {
            console.error('Failed to delete Redis key:', error);
        }
    }
    
    async disconnect() {
        try {
            await this.client.disconnect();
            await this.subscriber.disconnect();
            console.log('Disconnected from Redis');
        } catch (error) {
            console.error('Error disconnecting from Redis:', error);
        }
    }
}

module.exports = RedisClient;
