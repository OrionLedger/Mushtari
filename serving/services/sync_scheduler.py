"""
serving/services/sync_scheduler.py

Background service that orchestrates parallel syncing of data sources.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List
from datetime import datetime, timedelta

from infrastructure.logging.logger import get_logger
from serving.services.source_registry import SourceRegistry

logger = get_logger("SyncScheduler")

class SyncScheduler:
    _instance = None
    _lock = threading.Lock()
    _running = False
    _thread = None

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.stop_event = threading.Event()

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def start(self):
        """Starts the background scheduler loop."""
        if self._running:
            return
        
        self._running = True
        self.stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Sync scheduler started.")

    def stop(self):
        """Signals the background loop and executor to shut down."""
        self._running = False
        self.stop_event.set()
        self.executor.shutdown(wait=True)
        if self._thread:
            self._thread.join()
        logger.info("Sync scheduler stopped.")

    def _run_loop(self):
        """Main scheduler loop (checks every 5 minutes)."""
        while not self.stop_event.is_set():
            try:
                self.sync_all_due()
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
            
            # Sleep for 5 minutes or until stopped
            self.stop_event.wait(300)

    def sync_all_due(self):
        """Identifies and syncs sources that are due for a refresh."""
        sources = SourceRegistry.list_sources()
        now = datetime.now()
        
        due_sources = []
        for s in sources:
            source_id = s["id"]
            # Get sync interval from source (default 6h)
            # In absence of per-source config, we check watermark
            interval_hours = s.get("sync_interval_hours", 6)
            if interval_hours == 0: # Manual mode
                continue
                
            watermark = SourceRegistry.get_watermark(source_id)
            
            if not watermark or (now - watermark) > timedelta(hours=interval_hours):
                due_sources.append(source_id)
        
        if due_sources:
            logger.info(f"Triggering parallel sync for {len(due_sources)} due sources: {due_sources}")
            for sid in due_sources:
                self.executor.submit(self._safe_sync, sid)

    def sync_all_now(self):
        """Manually trigger parallel sync for ALL active sources."""
        sources = SourceRegistry.list_sources()
        source_ids = [s["id"] for s in sources]
        
        logger.info(f"Manual parallel sync triggered for {len(source_ids)} sources.")
        for sid in source_ids:
            self.executor.submit(self._safe_sync, sid)
        return {"ok": True, "count": len(source_ids)}

    def _safe_sync(self, source_id: int):
        """Internal wrapper to catch errors in worker threads."""
        try:
            logger.info(f"Background sync starting for source {source_id}")
            res = SourceRegistry.sync_source(source_id)
            if res.get("ok"):
                logger.info(f"Background sync success for source {source_id}: {res.get('rows')} rows.")
            else:
                logger.warning(f"Background sync failed for source {source_id}: {res.get('message')}")
        except Exception as e:
            logger.error(f"Fatal error in background sync for source {source_id}: {e}")
