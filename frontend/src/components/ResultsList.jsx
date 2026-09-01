import ProductCard from "./ProductCard";
import "./ResultsList.css";

/**
 * Renders the list of product result cards, plus empty/idle states.
 * @param {{ results: Array<Object>, hasSearched: boolean }} props
 */
export default function ResultsList({ results, hasSearched }) {
  const count = results?.length ?? 0;
  if (!hasSearched) {
    return (
      <div className="results-list__state"><h2 id="results-title">Results</h2><p className="results-list__placeholder">Start by searching above.</p></div>
    );
  }

  if (!results || results.length === 0) {
    return <div className="results-list__state"><h2 id="results-title">Results</h2><p className="results-list__placeholder">No matching products yet. Try a broader search.</p></div>;
  }

  return (
    <div className="results-list__content"><div className="results-list__heading"><h2 id="results-title">Results</h2><span>{count} {count === 1 ? "match" : "matches"}</span></div><ul className="results-list">
      {results.map((result, index) => (
        <ProductCard key={result?.product?.id ?? index} result={result} />
      ))}
    </ul></div>
  );
}
