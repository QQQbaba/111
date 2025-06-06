import asyncio
import docker
import redis
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ContainerManager:
    def __init__(self, database):
        self.db = database
        self.docker_client = docker.from_env()
        self.redis_client = redis.from_url("redis://redis:6379", decode_responses=True)
        self.running = False
        self.containers: Dict[str, str] = {}  # session_id -> container_id
        
        # Container configuration
        self.desktop_image = "kasmweb/ubuntu-focal-desktop:1.14.0"
        self.base_vnc_port = 5900
        self.max_containers = 50
        
    async def start(self):
        """Start the container manager"""
        self.running = True
        logger.info("Container Manager started")
        
        # Subscribe to Redis messages
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe('container:create', 'container:delete')
        
        try:
            while self.running:
                message = pubsub.get_message(timeout=1.0)
                if message and message['type'] == 'message':
                    await self._handle_redis_message(message)
                await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Error in container manager: {e}")
        finally:
            pubsub.close()
    
    async def stop(self):
        """Stop the container manager"""
        self.running = False
        logger.info("Container Manager stopped")
    
    async def _handle_redis_message(self, message):
        """Handle Redis pub/sub messages"""
        channel = message['channel']
        data = message['data']
        
        try:
            if channel == 'container:create':
                session_id, user_id = data.split(':', 1)
                await self._create_container(session_id, int(user_id))
            elif channel == 'container:delete':
                session_id = data
                await self._delete_container(session_id)
        except Exception as e:
            logger.error(f"Error handling Redis message {channel}: {e}")
    
    async def _create_container(self, session_id: str, user_id: int):
        """Create a new desktop container"""
        try:
            logger.info(f"Creating container for session {session_id}")
            
            # Find available VNC port
            vnc_port = await self._find_available_port()
            if not vnc_port:
                logger.error("No available VNC ports")
                await self._update_session_status(session_id, "failed")
                return
            
            # Container configuration
            container_name = f"desk-{session_id}"
            
            # Environment variables for the desktop container
            environment = {
                'VNC_PW': 'password',  # Default VNC password
                'KASM_SVC_SEND_CUT_TEXT': '0',
                'KASM_SVC_ACCEPT_CUT_TEXT': '0',
                'START_PULSEAUDIO': '0',
                'START_XFCE4': '1'
            }
            
            # Resource limits
            mem_limit = '1g'
            cpu_period = 100000
            cpu_quota = 50000  # 0.5 CPU
            pids_limit = 512
            
            # Security options
            security_opt = ['seccomp=unconfined']
            
            # Volumes for lxcfs (to hide host hardware info)
            volumes = {
                '/var/lib/lxcfs/proc': {'bind': '/proc', 'mode': 'ro'}
            }
            
            # Create and start container
            container = self.docker_client.containers.run(
                image=self.desktop_image,
                name=container_name,
                ports={5901: vnc_port},
                environment=environment,
                mem_limit=mem_limit,
                cpu_period=cpu_period,
                cpu_quota=cpu_quota,
                pids_limit=pids_limit,
                security_opt=security_opt,
                volumes=volumes,
                detach=True,
                remove=True,  # Auto-remove when stopped
                restart_policy={"Name": "no"}
            )
            
            # Store container info
            self.containers[session_id] = container.id
            
            # Update database
            await self._update_session_container(session_id, container.id, vnc_port)
            await self._update_session_status(session_id, "active")
            
            logger.info(f"Container {container_name} created successfully on port {vnc_port}")
            
        except docker.errors.ImageNotFound:
            logger.error(f"Desktop image {self.desktop_image} not found")
            await self._update_session_status(session_id, "failed")
        except docker.errors.APIError as e:
            logger.error(f"Docker API error creating container: {e}")
            await self._update_session_status(session_id, "failed")
        except Exception as e:
            logger.error(f"Unexpected error creating container: {e}")
            await self._update_session_status(session_id, "failed")
    
    async def _delete_container(self, session_id: str):
        """Delete a desktop container"""
        try:
            logger.info(f"Deleting container for session {session_id}")
            
            container_id = self.containers.get(session_id)
            if container_id:
                try:
                    container = self.docker_client.containers.get(container_id)
                    container.stop(timeout=10)
                    container.remove(force=True)
                    logger.info(f"Container {container_id} deleted successfully")
                except docker.errors.NotFound:
                    logger.warning(f"Container {container_id} not found")
                except Exception as e:
                    logger.error(f"Error deleting container {container_id}: {e}")
                
                # Remove from tracking
                del self.containers[session_id]
            
            # Clean up by container name as fallback
            container_name = f"desk-{session_id}"
            try:
                container = self.docker_client.containers.get(container_name)
                container.stop(timeout=10)
                container.remove(force=True)
                logger.info(f"Container {container_name} deleted successfully")
            except docker.errors.NotFound:
                pass  # Container already gone
            except Exception as e:
                logger.error(f"Error deleting container {container_name}: {e}")
                
        except Exception as e:
            logger.error(f"Unexpected error deleting container: {e}")
    
    async def _find_available_port(self) -> Optional[int]:
        """Find an available VNC port"""
        for port in range(self.base_vnc_port + 1, self.base_vnc_port + self.max_containers + 1):
            try:
                # Check if port is in use by checking existing containers
                containers = self.docker_client.containers.list()
                port_in_use = False
                
                for container in containers:
                    if container.name.startswith('desk-'):
                        ports = container.attrs.get('NetworkSettings', {}).get('Ports', {})
                        for container_port, host_bindings in ports.items():
                            if host_bindings:
                                for binding in host_bindings:
                                    if int(binding['HostPort']) == port:
                                        port_in_use = True
                                        break
                
                if not port_in_use:
                    return port
                    
            except Exception as e:
                logger.error(f"Error checking port {port}: {e}")
                continue
        
        return None
    
    async def _update_session_container(self, session_id: str, container_id: str, vnc_port: int):
        """Update session with container information"""
        try:
            await self.db.execute(
                "UPDATE sessions SET container_id = ?, vnc_port = ? WHERE id = ?",
                (container_id, vnc_port, session_id)
            )
        except Exception as e:
            logger.error(f"Error updating session container info: {e}")
    
    async def _update_session_status(self, session_id: str, status: str):
        """Update session status"""
        try:
            await self.db.execute(
                "UPDATE sessions SET status = ? WHERE id = ?",
                (status, session_id)
            )
        except Exception as e:
            logger.error(f"Error updating session status: {e}")
