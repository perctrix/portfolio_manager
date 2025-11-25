import logging
import threading
from datetime import datetime
from typing import List
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.benchmarks import BenchmarkLoader
from app.core import prices

logger = logging.getLogger(__name__)


class BenchmarkScheduler:
    """Scheduler for automatic benchmark data updates"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.benchmark_loader = BenchmarkLoader()
        # Update times in hours (server local time) for weekday updates
        self.update_times = [6, 10, 12, 14, 16, 18]

    def update_all_benchmarks(self) -> None:
        """Update all configured benchmark indices"""
        benchmarks = self.benchmark_loader.get_available_benchmarks()

        logger.info(f"Starting benchmark update for {len(benchmarks)} indices")

        success_count = 0
        fail_count = 0

        for benchmark in benchmarks:
            symbol = benchmark['symbol']
            try:
                logger.info(f"Updating benchmark: {symbol} ({benchmark['name']})")
                success = prices.update_price_cache(symbol)

                if success:
                    success_count += 1
                    logger.info(f"Successfully updated {symbol}")
                else:
                    fail_count += 1
                    logger.warning(f"Failed to update {symbol}")

            except Exception as e:
                fail_count += 1
                logger.error(f"Error updating benchmark {symbol}: {e}")

        logger.info(f"Benchmark update completed: {success_count} success, {fail_count} failed")

    def check_and_download_missing_benchmarks(self) -> None:
        """Check for missing benchmark data and download if needed"""
        benchmarks = self.benchmark_loader.get_available_benchmarks()

        logger.info("Checking for missing benchmark data")

        missing_count = 0
        downloaded_count = 0

        for benchmark in benchmarks:
            symbol = benchmark['symbol']
            try:
                df = prices.get_price_history(symbol)

                if df.empty:
                    missing_count += 1
                    logger.info(f"Benchmark {symbol} ({benchmark['name']}) is missing, downloading...")

                    success = prices.update_price_cache(symbol)
                    if success:
                        downloaded_count += 1
                        logger.info(f"Successfully downloaded {symbol}")
                    else:
                        logger.warning(f"Failed to download {symbol}")
                else:
                    logger.debug(f"Benchmark {symbol} data exists ({len(df)} rows)")

            except Exception as e:
                logger.error(f"Error checking benchmark {symbol}: {e}")

        if missing_count > 0:
            logger.info(f"Downloaded {downloaded_count}/{missing_count} missing benchmarks")
        else:
            logger.info("All benchmark data is available")

    def start(self) -> None:
        """Start the scheduler and perform initial check"""
        logger.info("Starting benchmark scheduler")

        for hour in self.update_times:
            self.scheduler.add_job(
                self.update_all_benchmarks,
                CronTrigger(day_of_week='mon-fri', hour=hour, minute=0),
                id=f'benchmark_update_{hour}h',
                name=f'Update benchmarks at {hour}:00',
                replace_existing=True
            )
            logger.info(f"Scheduled benchmark update for weekdays at {hour}:00")

        self.scheduler.start()

        self.scheduler.add_job(
            self.check_and_download_missing_benchmarks,
            'date',
            run_date=datetime.now(),
            id='initial_benchmark_check'
        )

        logger.info("Benchmark scheduler started successfully")

    def stop(self) -> None:
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Benchmark scheduler stopped")

    def get_next_run_times(self) -> List[str]:
        """Get next scheduled run times for monitoring"""
        jobs = self.scheduler.get_jobs()
        return [
            f"{job.name}: {job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')}"
            if job.next_run_time else f"{job.name}: Not scheduled"
            for job in jobs
        ]


scheduler_instance = None
_scheduler_lock = threading.Lock()


def get_scheduler() -> BenchmarkScheduler:
    """Get or create the global scheduler instance (thread-safe)"""
    global scheduler_instance
    with _scheduler_lock:
        if scheduler_instance is None:
            scheduler_instance = BenchmarkScheduler()
    return scheduler_instance


def start_scheduler() -> BenchmarkScheduler:
    """Start the benchmark scheduler (thread-safe)"""
    global scheduler_instance
    with _scheduler_lock:
        if scheduler_instance is None:
            scheduler_instance = BenchmarkScheduler()
        if not scheduler_instance.scheduler.running:
            scheduler_instance.start()
    return scheduler_instance


def stop_scheduler() -> None:
    """Stop the benchmark scheduler"""
    global scheduler_instance
    with _scheduler_lock:
        if scheduler_instance is not None:
            scheduler_instance.stop()
