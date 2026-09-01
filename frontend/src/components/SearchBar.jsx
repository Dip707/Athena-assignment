import { useState } from "react";
import "./SearchBar.css";

/**
 * Text input + submit button for running a product search.
 * @param {{ onSearch: (query: string) => void, loading: boolean }} props
 */
export default function SearchBar({ onSearch, loading }) {
  const [query, setQuery] = useState("");

  const handleSubmit = (event) => {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;
    onSearch(trimmed);
  };

  return (
    <form className="search-bar" onSubmit={handleSubmit}>
      <label className="search-bar__label" htmlFor="catalog-search">Search by keyword, product, or meaning</label>
      <input
        id="catalog-search"
        type="text"
        className="search-bar__input"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Search for products... e.g. 'Gaming keyboard under ₹5000'"
        aria-describedby="catalog-search-hint"
      />
      <p className="search-bar__hint" id="catalog-search-hint">Try “gaming keyboard under ₹5000” or “quiet desk lamp”.</p>
      <button
        type="submit"
        className="search-bar__button"
        disabled={loading || !query.trim()}
      >
        {loading ? "Searching…" : "Search"}
      </button>
    </form>
  );
}
