import asyncio
import os
import time
import logging
from container_manager import ContainerManager
from heartbeat_monitor import HeartbeatMonitor
from database import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main application entry point"""
    logger.info("Starting Container Manager Service")
    
    # Initialize components
    db = Database()
    container_manager = ContainerManager(db)
    heartbeat_monitor = HeartbeatMonitor(db, container_manager)
    
    try:
        # Start all services concurrently
        await asyncio.gather(
            container_manager.start(),
            heartbeat_monitor.start(),
            return_exceptions=True
        )
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Shutting down services")
        await container_manager.stop()
        await heartbeat_monitor.stop()


if __name__ == "__main__":
    asyncio.run(main())
