"""
Scheduler for self-healing container cleanup
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

logger = logging.getLogger(__name__)


class SchedulerManager:
    """Manages background tasks for container cleanup"""
    
    def __init__(self, docker_manager):
        self.docker_manager = docker_manager
        self.scheduler = AsyncIOScheduler()
    
    def start(self):
        """Start scheduler with cleanup job"""
        # Run cleanup every 5 minutes
        self.scheduler.add_job(
            self.docker_manager.cleanup_expired_containers,
            trigger=CronTrigger(minute="*/5"),
            id="cleanup_expired_containers",
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Scheduler started: Cleanup job scheduled (every 5 minutes)")
    
    def shutdown(self):
        """Shutdown scheduler"""
        self.scheduler.shutdown()
        logger.info("Scheduler shut down")



