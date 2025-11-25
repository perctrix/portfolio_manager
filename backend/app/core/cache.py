import os
import json
import logging
import re
import pandas as pd
import portalocker
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Callable
from contextlib import contextmanager

logger = logging.getLogger(__name__)


def validate_symbol(symbol: str) -> str:
    """Validate and sanitize stock ticker symbol to prevent path traversal attacks

    Args:
        symbol: Stock ticker symbol

    Returns:
        Validated symbol

    Raises:
        ValueError: If symbol contains invalid characters
    """
    if not symbol or not isinstance(symbol, str):
        raise ValueError("Symbol must be a non-empty string")

    if not re.match(r'^[A-Z0-9\.\^\_\-]+$', symbol):
        raise ValueError(f"Invalid symbol: {symbol}. Only alphanumeric, '.', '^', '_', '-' allowed")

    if '..' in symbol or '/' in symbol or '\\' in symbol:
        raise ValueError(f"Invalid symbol: {symbol}. Path traversal characters not allowed")

    if len(symbol) > 20:
        raise ValueError(f"Invalid symbol: {symbol}. Symbol too long (max 20 characters)")

    return symbol


@dataclass
class CacheMetadata:
    """Metadata for a single cached ticker"""

    last_updated: datetime
    data_range_start: str
    data_range_end: str
    row_count: int

    def to_dict(self) -> Dict[str, any]:
        """Convert metadata to dictionary for JSON serialization"""
        return {
            "last_updated": self.last_updated.isoformat(),
            "data_range": {
                "start": self.data_range_start,
                "end": self.data_range_end
            },
            "row_count": self.row_count
        }

    @staticmethod
    def from_dict(data: Dict[str, any]) -> 'CacheMetadata':
        """Create metadata from dictionary"""
        last_updated_str = data["last_updated"]

        try:
            last_updated = datetime.fromisoformat(last_updated_str)
        except ValueError:
            last_updated = datetime.strptime(last_updated_str, "%Y-%m-%dT%H:%M:%S.%fZ")

        if last_updated.tzinfo is None:
            last_updated = last_updated.replace(tzinfo=timezone.utc)

        return CacheMetadata(
            last_updated=last_updated,
            data_range_start=data["data_range"]["start"],
            data_range_end=data["data_range"]["end"],
            row_count=data["row_count"]
        )


class PriceCacheManager:
    """Thread-safe price cache manager with metadata tracking"""

    def __init__(self, prices_dir: str, ttl_hours: float):
        self.prices_dir: str = os.path.abspath(prices_dir)
        self.ttl: timedelta = timedelta(hours=ttl_hours)
        self.metadata_file: str = os.path.join(self.prices_dir, "metadata.json")
        self.metadata_lock_file: str = self.metadata_file + ".lock"

        os.makedirs(self.prices_dir, exist_ok=True)

    def _get_safe_csv_path(self, symbol: str) -> str:
        """Get safe CSV path with validation to prevent path traversal

        Args:
            symbol: Stock ticker symbol (must be validated)

        Returns:
            Absolute path to CSV file

        Raises:
            ValueError: If path is outside prices directory
        """
        symbol = validate_symbol(symbol)
        csv_path = os.path.abspath(os.path.join(self.prices_dir, f"{symbol}.csv"))

        if not csv_path.startswith(self.prices_dir + os.sep):
            raise ValueError(f"Invalid path: {csv_path} is outside prices directory")

        return csv_path

    def is_cache_valid(self, symbol: str) -> bool:
        """Check if cache exists and not expired

        Args:
            symbol: Stock ticker symbol

        Returns:
            True if cache is valid, False otherwise
        """
        symbol = validate_symbol(symbol)
        metadata = self._load_metadata()

        if symbol not in metadata:
            migrated = self._migrate_existing_csv(symbol)
            if migrated is None:
                return False
            metadata[symbol] = migrated

        last_updated = metadata[symbol].last_updated
        if last_updated.tzinfo is None:
            last_updated = last_updated.replace(tzinfo=timezone.utc)

        age = datetime.now(timezone.utc) - last_updated
        return age <= self.ttl

    def get_or_refresh(self, symbol: str, fetch_func: Callable[[], pd.DataFrame]) -> pd.DataFrame:
        """Main entry point: get cached data or refresh if expired

        Args:
            symbol: Stock ticker symbol
            fetch_func: Function to fetch fresh data if cache is invalid

        Returns:
            Price data DataFrame
        """
        symbol = validate_symbol(symbol)
        if self.is_cache_valid(symbol):
            logger.info(f"Cache hit for {symbol}")
            return self._read_csv(symbol)

        with self._acquire_lock():
            if self.is_cache_valid(symbol):
                logger.info(f"Cache hit for {symbol} after lock acquisition")
                return self._read_csv(symbol)

            logger.info(f"Cache miss for {symbol}, fetching fresh data")
            data = fetch_func()
            self._update_cache(symbol, data)
            return data

    def _load_metadata(self) -> Dict[str, CacheMetadata]:
        """Load metadata from file with error recovery

        Returns:
            Dictionary mapping symbols to their metadata
        """
        if not os.path.exists(self.metadata_file):
            return {}

        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if "tickers" not in data:
                logger.warning("Metadata file missing 'tickers' key, returning empty dict")
                return {}

            return {k: CacheMetadata.from_dict(v) for k, v in data.get("tickers", {}).items()}

        except json.JSONDecodeError as e:
            logger.error(f"Metadata file corrupted: {e}, returning empty dict")
            return {}
        except FileNotFoundError:
            return {}
        except Exception as e:
            logger.error(f"Error loading metadata: {e}, returning empty dict")
            return {}

    def _save_metadata_locked(self, metadata: Dict[str, CacheMetadata]) -> None:
        """Save metadata to file (caller must hold lock)

        Args:
            metadata: Dictionary of metadata to save
        """
        data = {
            "version": "1.0",
            "last_modified": datetime.now(timezone.utc).isoformat(),
            "tickers": {k: v.to_dict() for k, v in metadata.items()}
        }

        temp_file = self.metadata_file + ".tmp"
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            os.replace(temp_file, self.metadata_file)
            logger.debug("Metadata saved successfully")
        finally:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass

    def _migrate_existing_csv(self, symbol: str) -> Optional[CacheMetadata]:
        """Generate metadata for existing CSV files without metadata

        Args:
            symbol: Stock ticker symbol

        Returns:
            CacheMetadata if CSV exists, None otherwise
        """
        csv_path = self._get_safe_csv_path(symbol)
        if not os.path.exists(csv_path):
            return None

        try:
            df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
            if df.empty:
                logger.warning(f"CSV file for {symbol} is empty")
                return None

            mtime = os.path.getmtime(csv_path)
            last_updated = datetime.fromtimestamp(mtime, tz=timezone.utc)

            metadata = CacheMetadata(
                last_updated=last_updated,
                data_range_start=df.index.min().strftime("%Y-%m-%d"),
                data_range_end=df.index.max().strftime("%Y-%m-%d"),
                row_count=len(df)
            )

            with self._acquire_lock():
                all_metadata = self._load_metadata()
                all_metadata[symbol] = metadata
                self._save_metadata_locked(all_metadata)

            logger.info(f"Migrated existing CSV for {symbol}")
            return metadata

        except Exception as e:
            logger.warning(f"Migration failed for {symbol}: {e}")
            return None

    def _update_cache(self, symbol: str, data: pd.DataFrame) -> None:
        """Update CSV file and metadata (caller must hold lock)

        Args:
            symbol: Stock ticker symbol
            data: Price data to cache
        """
        if data.empty:
            logger.warning(f"Attempted to cache empty data for {symbol}")
            return

        csv_path = self._get_safe_csv_path(symbol)
        data.to_csv(csv_path)
        logger.debug(f"Saved CSV for {symbol}")

        metadata = self._load_metadata()
        metadata[symbol] = CacheMetadata(
            last_updated=datetime.now(timezone.utc),
            data_range_start=data.index.min().strftime("%Y-%m-%d"),
            data_range_end=data.index.max().strftime("%Y-%m-%d"),
            row_count=len(data)
        )
        self._save_metadata_locked(metadata)
        logger.info(f"Updated cache for {symbol}: {len(data)} rows")

    def _read_csv(self, symbol: str) -> pd.DataFrame:
        """Read CSV file directly

        Args:
            symbol: Stock ticker symbol

        Returns:
            Price data DataFrame
        """
        csv_path = self._get_safe_csv_path(symbol)

        if not os.path.exists(csv_path):
            logger.warning(f"CSV file not found for {symbol}")
            return pd.DataFrame()

        df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
        if not df.empty and hasattr(df.index, 'normalize'):
            df.index = df.index.normalize()

        return df

    @contextmanager
    def _acquire_lock(self):
        """Context manager for acquiring metadata lock

        Yields:
            None
        """
        os.makedirs(os.path.dirname(self.metadata_lock_file), exist_ok=True)

        with open(self.metadata_lock_file, 'a') as lock_fd:
            try:
                portalocker.lock(lock_fd, portalocker.LOCK_EX)
                yield
            except portalocker.LockException as e:
                logger.error(f"Failed to acquire lock: {e}")
                raise
            finally:
                try:
                    portalocker.unlock(lock_fd)
                except Exception:
                    pass
