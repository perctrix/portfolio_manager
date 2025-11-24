'use client';

import { useState, useEffect, useRef } from 'react';

interface Ticker {
  symbol: string;
  name: string;
  exchange: string;
  type: string;
}

interface TickerData {
  metadata: {
    last_updated: string;
    count: number;
    sources: string[];
  };
  tickers: Ticker[];
}

let cachedTickers: Ticker[] | null = null;
let loadingPromise: Promise<void> | null = null;

async function loadTickers(): Promise<void> {
  if (cachedTickers) return;

  if (loadingPromise) {
    await loadingPromise;
    return;
  }

  loadingPromise = (async () => {
    try {
      const response = await fetch('/data/tickers.json');
      const data: TickerData = await response.json();
      cachedTickers = data.tickers;
      console.log(`Loaded ${cachedTickers.length} tickers for autocomplete`);
    } catch (error) {
      console.error('Failed to load tickers:', error);
      cachedTickers = [];
    } finally {
      loadingPromise = null;
    }
  })();

  await loadingPromise;
}

interface TickerAutocompleteProps {
  value: string;
  onChange: (value: string) => void;
  onSelect?: (ticker: Ticker) => void;
  placeholder?: string;
  className?: string;
  required?: boolean;
}

export function TickerAutocomplete({
  value,
  onChange,
  onSelect,
  placeholder = "AAPL",
  className = "",
  required = false
}: TickerAutocompleteProps) {
  const [suggestions, setSuggestions] = useState<Ticker[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadTickers();
  }, []);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(event.target as Node)
      ) {
        setShowDropdown(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  function searchTickers(query: string): Ticker[] {
    if (!cachedTickers || !query) return [];

    const q = query.toUpperCase().trim();

    const symbolStartsWith = cachedTickers.filter(t => t.symbol.startsWith(q));
    const symbolContains = cachedTickers.filter(t =>
      !t.symbol.startsWith(q) && t.symbol.includes(q)
    );
    const nameContains = cachedTickers.filter(t =>
      !t.symbol.includes(q) && t.name.toUpperCase().includes(q)
    );

    return [...symbolStartsWith, ...symbolContains, ...nameContains].slice(0, 20);
  }

  async function handleInputChange(input: string) {
    const upperInput = input.toUpperCase();
    onChange(upperInput);

    if (!upperInput.trim()) {
      setSuggestions([]);
      setShowDropdown(false);
      return;
    }

    if (!cachedTickers) {
      setIsLoading(true);
      await loadTickers();
      setIsLoading(false);
    }

    const results = searchTickers(upperInput);
    setSuggestions(results);
    setShowDropdown(results.length > 0);
    setSelectedIndex(-1);
  }

  function selectTicker(ticker: Ticker) {
    onChange(ticker.symbol);
    setShowDropdown(false);
    setSuggestions([]);
    setSelectedIndex(-1);
    onSelect?.(ticker);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (!showDropdown) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(i => Math.min(i + 1, suggestions.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(i => Math.max(i - 1, -1));
    } else if (e.key === 'Enter' && selectedIndex >= 0) {
      e.preventDefault();
      selectTicker(suggestions[selectedIndex]);
    } else if (e.key === 'Escape') {
      e.preventDefault();
      setShowDropdown(false);
    }
  }

  useEffect(() => {
    if (selectedIndex >= 0 && dropdownRef.current) {
      const selectedElement = dropdownRef.current.children[selectedIndex] as HTMLElement;
      if (selectedElement) {
        selectedElement.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      }
    }
  }, [selectedIndex]);

  return (
    <div className="relative">
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => handleInputChange(e.target.value)}
        onKeyDown={handleKeyDown}
        onFocus={() => {
          if (value && cachedTickers) {
            const results = searchTickers(value);
            if (results.length > 0) {
              setSuggestions(results);
              setShowDropdown(true);
            }
          }
        }}
        className={`w-full px-3 py-2 border rounded-lg uppercase ${className}`}
        placeholder={placeholder}
        autoComplete="off"
        required={required}
        disabled={isLoading}
      />

      {isLoading && (
        <div className="absolute right-3 top-1/2 -translate-y-1/2">
          <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
        </div>
      )}

      {showDropdown && suggestions.length > 0 && (
        <div
          ref={dropdownRef}
          className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-80 overflow-y-auto"
        >
          {suggestions.map((ticker, index) => (
            <div
              key={ticker.symbol}
              onClick={() => selectTicker(ticker)}
              onMouseEnter={() => setSelectedIndex(index)}
              className={`px-4 py-2.5 cursor-pointer border-b border-gray-100 last:border-b-0 ${
                index === selectedIndex ? 'bg-blue-50' : 'hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-gray-900">{ticker.symbol}</div>
                  <div className="text-xs text-gray-600 truncate">{ticker.name}</div>
                </div>
                <div className="flex items-center gap-2 ml-3 flex-shrink-0">
                  <span className="text-xs text-gray-500">{ticker.exchange}</span>
                  <span className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded">
                    {ticker.type}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
