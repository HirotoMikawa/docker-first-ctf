"""
Docker container management with atomic operations
"""

import docker
from docker.errors import DockerException, APIError
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class DockerManager:
    """Manages Docker containers with atomic startup strategy"""
    
    def __init__(self):
        """Initialize Docker client"""
        try:
            self.client = docker.from_env()
            self.client.ping()
            logger.info("Docker client connected successfully")
        except DockerException as e:
            logger.error(f"Failed to connect to Docker: {e}")
            self.client = None
    
    async def ensure_network(self) -> bool:
        """
        Ensure ctf_net network exists (internal network)
        """
        if not self.client:
            return False
        
        try:
            networks = self.client.networks.list(names=["ctf_net"])
            if not networks:
                self.client.networks.create(
                    name="ctf_net",
                    driver="bridge",
                    internal=True  # No external internet access
                )
                logger.info("Created ctf_net network (internal)")
            else:
                logger.info("ctf_net network already exists")
            return True
        except APIError as e:
            logger.error(f"Failed to ensure network: {e}")
            return False
    
    async def startup_cleanup(self):
        """
        Cleanup orphaned containers on startup
        """
        if not self.client:
            return
        
        try:
            # Get all running containers
            running_containers = self.client.containers.list(all=True)
            running_ids = {c.id for c in running_containers}
            
            # TODO: Compare with DB and remove orphaned entries
            logger.info(f"Startup cleanup: {len(running_containers)} containers found")
        except Exception as e:
            logger.error(f"Startup cleanup failed: {e}")
    
    async def start_container(
        self,
        user_id: str,
        image: str,
        flag: str
    ) -> Dict:
        """
        Atomic container startup with port allocation
        
        Returns: {"status": "success", "container_id": "...", "port": 12345}
        or raises HTTPException on failure
        """
        if not self.client:
            raise Exception("Docker client not available")
        
        container = None
        
        try:
            # Atomic startup: Port 0 = Docker assigns available port
            container = self.client.containers.run(
                image=image,
                name=f"ctf_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                ports={'8000/tcp': ('0.0.0.0', 0)},  # Internal port 8000, host port auto
                network=settings.CONTAINER_NETWORK,
                detach=True,
                remove=False,
                mem_limit=settings.CONTAINER_MEMORY_LIMIT,
                cpu_quota=int(float(settings.CONTAINER_CPU_LIMIT) * 100000),
                cpu_period=100000,
                environment={
                    "CTF_FLAG": flag
                },
                # Security: No docker.sock mount
            )
            
            # Reload to get assigned port
            container.reload()
            assigned_port = container.ports['8000/tcp'][0]['HostPort']
            
            # TODO: Save to DB
            # await save_to_db(user_id, container.id, assigned_port)
            
            logger.info(f"Container started: {container.id[:12]} on port {assigned_port}")
            
            return {
                "status": "success",
                "container_id": container.id,
                "port": int(assigned_port)
            }
            
        except Exception as e:
            # Rollback: Remove container if created
            if container:
                try:
                    container.remove(force=True)
                    logger.warning(f"Rollback: Removed failed container {container.id[:12]}")
                except:
                    pass
            
            logger.error(f"Container startup failed: {e}")
            raise Exception(f"Mission Start Failed: {str(e)}")
    
    async def stop_container(self, container_id: str) -> bool:
        """Stop and remove container"""
        if not self.client:
            return False
        
        try:
            container = self.client.containers.get(container_id)
            container.stop()
            container.remove()
            logger.info(f"Container stopped and removed: {container_id[:12]}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop container: {e}")
            return False
    
    async def cleanup_expired_containers(self):
        """
        Cleanup containers older than TTL
        """
        if not self.client:
            return
        
        try:
            containers = self.client.containers.list(all=True, filters={"name": "ctf_"})
            ttl = timedelta(minutes=settings.CONTAINER_TTL_MINUTES)
            now = datetime.now()
            
            for container in containers:
                # Check creation time
                created = datetime.fromtimestamp(container.attrs['Created'])
                if now - created > ttl:
                    try:
                        container.stop()
                        container.remove()
                        logger.info(f"Cleaned up expired container: {container.id[:12]}")
                    except Exception as e:
                        logger.error(f"Failed to cleanup container: {e}")
        except Exception as e:
            logger.error(f"Cleanup expired containers failed: {e}")
    
    async def cleanup_all_containers(self):
        """Cleanup all ctf containers (shutdown)"""
        if not self.client:
            return
        
        try:
            containers = self.client.containers.list(all=True, filters={"name": "ctf_"})
            for container in containers:
                try:
                    container.stop()
                    container.remove()
                except:
                    pass
        except Exception as e:
            logger.error(f"Cleanup all containers failed: {e}")



