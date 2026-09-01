import { useEffect, useRef, useState } from "react";
import DatasetLoader from "./components/DatasetLoader";
import SearchBar from "./components/SearchBar";
import ResultsList from "./components/ResultsList";
import { getCatalogStatus, searchProducts } from "./api";
import "./App.css";

function App() {
  const [catalogStatus, setCatalogStatus] = useState(null);
  const [catalogStatusError, setCatalogStatusError] = useState(null);
  const [setupOpen, setSetupOpen] = useState(false);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [refining, setRefining] = useState(false);
  const searchGeneration = useRef(0);
  const catalogMutation = useRef(0);

  useEffect(() => {
    let active = true;
    const statusVersion = catalogMutation.current;
    getCatalogStatus()
      .then((status) => {
        if (!active || statusVersion !== catalogMutation.current) return;
        setCatalogStatus(status);
        setCatalogStatusError(null);
      })
      .catch((err) => {
        if (!active || statusVersion !== catalogMutation.current) return;
        setCatalogStatusError(err.message || "Catalog status is unavailable.");
      });

    return () => {
      active = false;
    };
  }, []);

  const catalogLoaded = catalogStatus?.loaded === true;
  const aiEnabled = catalogStatus?.ai_enabled === true;

  const handleSearch = async (query) => {
    const generation = ++searchGeneration.current;
    setLoading(true);
    setRefining(false);
    setError(null);
    setHasSearched(true);
    setResults([]);

    try {
      const initialData = await searchProducts(query, { curate: false });
      if (generation !== searchGeneration.current) return;

      setResults(Array.isArray(initialData?.results) ? initialData.results : []);
      setLoading(false);

      // Deterministic search is the complete flow when AI is unavailable.
      // In particular, do not issue a second curate=true request without a
      // backend status response confirming that a key is configured.
      if (!aiEnabled) return;

      setRefining(true);

      try {
        const refinedData = await searchProducts(query, { curate: true });
        if (generation !== searchGeneration.current) return;
        setResults(Array.isArray(refinedData?.results) ? refinedData.results : []);
      } catch {
        // AI refinement is best-effort; retain the deterministic results.
      } finally {
        if (generation === searchGeneration.current) setRefining(false);
      }
    } catch (err) {
      if (generation !== searchGeneration.current) return;
      setError(err.message || "Something went wrong while searching.");
      setResults([]);
      setLoading(false);
      setRefining(false);
    }
  };

  const handleDatasetLoaded = ({ indexed }) => {
    catalogMutation.current += 1;
    setCatalogStatus((current) => ({
      loaded: indexed > 0,
      product_count: indexed,
      ai_enabled: current?.ai_enabled === true,
    }));
    setCatalogStatusError(null);
    setSetupOpen(indexed > 0 ? false : true);
  };

  return (
    <div className="app">
      <header className="app__header">
        <p className="app__eyebrow">PRODUCT CATALOG / HYBRID INDEX</p>
        <h1>AI Product Search</h1>
        <p className="app__subtitle">
          Search products by keyword and meaning, ranked with hybrid search.
        </p>
      </header>

      <main className="app__main">
        <section className="app__workspace" aria-label="Product search workspace">
          <section className="app__section app__section--setup" aria-labelledby="catalog-setup-title">
            <h2 id="catalog-setup-title">Catalog setup</h2>
            {catalogStatusError && (
              <div className="app__catalog-message app__catalog-message--error" role="alert">
                <strong>Catalog readiness is unavailable.</strong> {catalogStatusError} You can still paste or upload a dataset below.
              </div>
            )}
            {catalogStatus && !catalogStatus.loaded && (
              <div className="app__catalog-message" role="status">
                <strong>No populated catalog is ready.</strong> We could not find products in <code>data/products.json</code>. Paste or upload a JSON product list below to start searching.
              </div>
            )}
            {catalogLoaded && !setupOpen ? (
              <button
                type="button"
                className="app__dataset-toggle"
                onClick={() => setSetupOpen(true)}
              >
                Use another dataset
              </button>
            ) : (
              <DatasetLoader onLoaded={handleDatasetLoaded} />
            )}
          </section>
          <section className="app__section app__section--search" aria-labelledby="search-title">
            <h2 id="search-title">Search the catalog</h2>
            <SearchBar onSearch={handleSearch} loading={loading} />
          </section>

        {error && (
          <div className="app__error" role="alert" aria-live="assertive">
            <span aria-hidden="true">!</span>
            {error}
          </div>
        )}

        {loading && <div className="app__loading" role="status" aria-live="polite"><span className="app__status-dot" aria-hidden="true" />Searching…</div>}

        {refining && (
          <div className="app__refining" role="status" aria-live="polite"><span className="app__status-dot" aria-hidden="true" />
            Refining results with AI…
          </div>
        )}

        {!loading && <section className="app__section app__section--results" aria-labelledby="results-title"><ResultsList results={results} hasSearched={hasSearched} /></section>}
        </section>
      </main>
    </div>
  );
}

export default App;
