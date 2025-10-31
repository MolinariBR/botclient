import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from models.user import User

logger = logging.getLogger(__name__)


class MuteService:
    """Service for handling automatic unmute functionality"""

    def __init__(self, db: Session, check_interval: int = 60):
        """
        Initialize mute service

        Args:
            db: Database session
            check_interval: Interval in seconds to check for expired mutes (default: 60 seconds)
        """
        self.db = db
        self.check_interval = check_interval
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the mute checking task"""
        if self._task is None:
            self._task = asyncio.create_task(self._check_expired_mutes_loop())
            logger.info("Mute service started - checking for expired mutes every %d seconds", self.check_interval)

    async def stop(self):
        """Stop the mute checking task"""
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
            logger.info("Mute service stopped")

    async def _check_expired_mutes_loop(self):
        """Main loop that periodically checks for expired mutes"""
        while True:
            try:
                await self._check_expired_mutes()
            except Exception as e:
                logger.error("Error checking expired mutes: %s", e)

            await asyncio.sleep(self.check_interval)

    async def _check_expired_mutes(self):
        """Check and unmute users whose mute duration has expired"""
        now = datetime.now(timezone.utc)

        # Find all muted users whose mute_until time has passed
        expired_mutes = self.db.query(User).filter(
            User.is_muted == True,
            User.mute_until.isnot(None),
            User.mute_until <= now
        ).all()

        if expired_mutes:
            logger.info("Found %d expired mutes to process", len(expired_mutes))

            for user in expired_mutes:
                logger.info("Unmuting user @%s (ID: %s) - mute expired at %s",
                          user.username, user.id, user.mute_until)

                # Unmute the user
                user.is_muted = False
                user.mute_until = None

            # Commit all changes
            self.db.commit()
            logger.info("Successfully unmuted %d users", len(expired_mutes))
        else:
            logger.debug("No expired mutes found")