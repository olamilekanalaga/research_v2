from __future__ import annotations

import asyncio
import ctypes
import logging
import os
from pathlib import Path

from .collector import run_collector
from .logging_config import configure_logging
from .outcome_tracker import run_outcome_tracker

logger = logging.getLogger(__name__)

ERROR_ALREADY_EXISTS = 183


async def run_services() -> None:
    configure_logging()
    lock_path = Path(".service_runner.lock")
    try:
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
    except FileExistsError:
        logger.error("Combined service lock file exists; exiting duplicate process")
        return
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Global\\VlakAladdinService")
    if ctypes.windll.kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        logger.error("Combined service is already running; exiting duplicate process")
        os.close(lock_fd)
        lock_path.unlink(missing_ok=True)
        return
    logger.info("Starting combined collector and outcome tracker service")
    try:
        await asyncio.gather(run_collector(), run_outcome_tracker())
    finally:
        ctypes.windll.kernel32.CloseHandle(mutex)
        os.close(lock_fd)
        lock_path.unlink(missing_ok=True)


if __name__ == "__main__":
    asyncio.run(run_services())
