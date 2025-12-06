"""
Symbol resolution service for mapping bare symbols to Yahoo Finance format.
Uses currency hints to determine likely exchange suffixes.
Validates symbols through the unified price data pipeline.
"""
import json
import logging
import os
from dataclasses import dataclass

from app.core import prices
from data.fetch_data import get_stealth_headers
import requests

logger: logging.Logger = logging.getLogger(__name__)


@dataclass
class ResolvedSymbol:
    """Result of successful symbol resolution."""
    original: str
    resolved: str
    currency: str
    exchange: str
    confidence: float
    source: str


@dataclass
class UnresolvedSymbol:
    """Symbol that could not be resolved automatically."""
    original: str
    currency: str
    attempted: list[str]
    suggestions: list[dict]


class SymbolResolver:
    """Resolves bare stock symbols to Yahoo Finance format using currency hints."""

    def __init__(self) -> None:
        self._suffix_config: dict = self._load_suffix_config()
        self._resolution_cache: dict[tuple[str, str], ResolvedSymbol | None] = {}

    def _load_suffix_config(self) -> dict:
        """Load exchange suffix configuration."""
        config_path = os.path.join(
            os.path.dirname(__file__),
            '..', '..', 'data', 'exchange_suffixes.json'
        )
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed to load exchange_suffixes.json: %s", e)
            return {"mappings": {}, "no_suffix": ["USD"]}

    def _validate_symbol(self, symbol: str) -> bool:
        """
        Validate symbol by attempting to get price data through the unified pipeline.
        Uses prices.get_price_history() which handles caching internally.
        """
        try:
            df = prices.get_price_history(symbol)
            return df is not None and not df.empty
        except Exception as e:
            logger.debug("Symbol validation failed for %s: %s", symbol, e)
            return False

    def resolve(
        self,
        symbol: str,
        currency: str,
        use_cache: bool = True
    ) -> tuple[ResolvedSymbol | None, UnresolvedSymbol | None]:
        """
        Resolve a symbol to Yahoo Finance format.

        Args:
            symbol: The bare stock symbol (e.g., "RHM")
            currency: The trading currency (e.g., "EUR")
            use_cache: Whether to use cached results

        Returns:
            Tuple of (ResolvedSymbol if successful, UnresolvedSymbol if failed)
        """
        symbol = symbol.upper().strip()
        currency = currency.upper().strip()

        cache_key = (symbol, currency)
        if use_cache and cache_key in self._resolution_cache:
            cached = self._resolution_cache[cache_key]
            if cached:
                return cached, None

        # Step 1: Check if symbol already has an exchange suffix
        if self._has_exchange_suffix(symbol):
            if self._validate_symbol(symbol):
                result = ResolvedSymbol(
                    original=symbol,
                    resolved=symbol,
                    currency=currency,
                    exchange=self._extract_exchange_from_suffix(symbol),
                    confidence=1.0,
                    source='exact'
                )
                self._resolution_cache[cache_key] = result
                return result, None

        # Step 2: For USD, try without suffix first
        no_suffix_currencies = self._suffix_config.get('no_suffix', ['USD'])
        if currency in no_suffix_currencies:
            if self._validate_symbol(symbol):
                result = ResolvedSymbol(
                    original=symbol,
                    resolved=symbol,
                    currency=currency,
                    exchange='US',
                    confidence=1.0,
                    source='exact'
                )
                self._resolution_cache[cache_key] = result
                return result, None

        # Step 3: Try currency-based suffixes
        mappings = self._suffix_config.get('mappings', {})
        currency_config = mappings.get(currency, {})

        attempted: list[str] = []

        # Try primary suffix first
        primary = currency_config.get('primary')
        if primary:
            candidate = f"{symbol}{primary}"
            attempted.append(candidate)
            if self._validate_symbol(candidate):
                result = ResolvedSymbol(
                    original=symbol,
                    resolved=candidate,
                    currency=currency,
                    exchange=primary.lstrip('.'),
                    confidence=0.9,
                    source='suffix_match'
                )
                self._resolution_cache[cache_key] = result
                return result, None

        # Try alternative suffixes
        alternatives = currency_config.get('alternatives', [])
        for suffix in alternatives:
            candidate = f"{symbol}{suffix}"
            attempted.append(candidate)
            if self._validate_symbol(candidate):
                result = ResolvedSymbol(
                    original=symbol,
                    resolved=candidate,
                    currency=currency,
                    exchange=suffix.lstrip('.'),
                    confidence=0.7,
                    source='suffix_match'
                )
                self._resolution_cache[cache_key] = result
                return result, None

        # Step 4: Try original symbol as fallback (maybe it works)
        if currency not in no_suffix_currencies:
            if self._validate_symbol(symbol):
                result = ResolvedSymbol(
                    original=symbol,
                    resolved=symbol,
                    currency=currency,
                    exchange='UNKNOWN',
                    confidence=0.5,
                    source='fallback'
                )
                self._resolution_cache[cache_key] = result
                return result, None

        # Step 5: Use Yahoo Search API to find suggestions
        suggestions = self._search_suggestions(symbol)

        # Mark as unresolved
        unresolved = UnresolvedSymbol(
            original=symbol,
            currency=currency,
            attempted=attempted,
            suggestions=suggestions
        )

        self._resolution_cache[cache_key] = None
        return None, unresolved

    def _has_exchange_suffix(self, symbol: str) -> bool:
        """Check if symbol already has an exchange suffix."""
        known_suffixes = [
            '.DE', '.PA', '.L', '.HK', '.TW', '.TO', '.T', '.SS', '.SZ',
            '.AX', '.SW', '.SI', '.ST', '.OL', '.CO', '.KS', '.KQ',
            '.MI', '.AS', '.BR', '.MC', '.VI', '.V', '.CN', '.NE',
            '.NS', '.BO', '.NZ', '.MX', '.SA', '.JO', '.IL', '.OS',
            '.NG', '.F', '.TWO', '.VX'
        ]
        return any(symbol.endswith(suffix) for suffix in known_suffixes)

    def _extract_exchange_from_suffix(self, symbol: str) -> str:
        """Extract exchange code from symbol suffix."""
        for suffix in ['.DE', '.PA', '.L', '.HK', '.TW', '.TO', '.T', '.SS', '.SZ',
                       '.AX', '.SW', '.SI', '.ST', '.OL', '.CO', '.KS', '.KQ',
                       '.MI', '.AS', '.BR', '.MC', '.VI', '.V', '.CN', '.NE',
                       '.NS', '.BO', '.NZ', '.MX', '.SA', '.JO', '.IL', '.OS',
                       '.NG', '.F', '.TWO', '.VX']:
            if symbol.endswith(suffix):
                return suffix.lstrip('.')
        return 'UNKNOWN'

    def _search_suggestions(self, symbol: str, limit: int = 5) -> list[dict]:
        """Use Yahoo Finance search API to find symbol suggestions."""
        try:
            url = "https://query2.finance.yahoo.com/v1/finance/search"
            params = {'q': symbol, 'quotes_count': limit, 'news_count': 0}
            response = requests.get(
                url,
                params=params,
                headers=get_stealth_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return [
                    {
                        'symbol': q.get('symbol', ''),
                        'name': q.get('longname') or q.get('shortname', ''),
                        'exchange': q.get('exchange', '')
                    }
                    for q in data.get('quotes', [])[:limit]
                ]
        except Exception as e:
            logger.warning("Yahoo search failed for %s: %s", symbol, e)

        return []

    def resolve_manual(
        self,
        original: str,
        resolved: str,
        currency: str
    ) -> ResolvedSymbol | None:
        """Register a manual resolution (user-provided)."""
        resolved = resolved.upper().strip()
        original = original.upper().strip()
        currency = currency.upper().strip()

        if self._validate_symbol(resolved):
            result = ResolvedSymbol(
                original=original,
                resolved=resolved,
                currency=currency,
                exchange=self._extract_exchange_from_suffix(resolved) if self._has_exchange_suffix(resolved) else 'UNKNOWN',
                confidence=1.0,
                source='manual'
            )
            cache_key = (original, currency)
            self._resolution_cache[cache_key] = result
            return result
        return None

    def clear_cache(self) -> None:
        """Clear the resolution cache."""
        self._resolution_cache.clear()


# Module-level instance
_resolver: SymbolResolver | None = None


def get_resolver() -> SymbolResolver:
    """Get the module-level SymbolResolver instance."""
    global _resolver
    if _resolver is None:
        _resolver = SymbolResolver()
    return _resolver
