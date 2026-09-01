import { useState } from "react";
import { uploadDataset } from "../api";
import "./DatasetLoader.css";

function DatasetLoader({ onLoaded }) {
  const [text, setText] = useState("");
  const [status, setStatus] = useState(null);
  const [busy, setBusy] = useState(false);

  const handleFile = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    setText(await file.text());
  };

  const handleLoad = async () => {
    setBusy(true);
    setStatus(null);
    try {
      const products = JSON.parse(text);
      const result = await uploadDataset(products);
      setStatus(`Indexed ${result.indexed} products.`);
      onLoaded?.(result);
    } catch (err) {
      setStatus(`Error: ${err.message}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="dataset-loader">
      <p className="dataset-loader__intro">
        Load a product dataset (JSON array of {"{"}id, title, description,
        category, price{"}"}). The bundled file is <code>data/products.json</code>;
        you can also paste or upload another catalog:
      </p>
      <label className="dataset-loader__label" htmlFor="dataset-file">Choose a JSON file</label>
      <input id="dataset-file" className="dataset-loader__file" type="file" accept="application/json" onChange={handleFile} />
      <label className="dataset-loader__label" htmlFor="dataset-json">Or paste JSON</label>
      <textarea
        id="dataset-json"
        className="dataset-loader__textarea"
        rows={6}
        cols={60}
        value={text}
        onChange={(event) => setText(event.target.value)}
        placeholder="Paste JSON array here, or choose a file above"
      />
      <p className="dataset-loader__hint">Your catalog is indexed locally for this session.</p>
      <button className="dataset-loader__button" onClick={handleLoad} disabled={busy || !text.trim()}>
        {busy ? "Loading..." : "Load dataset"}
      </button>
      {status && <p className="dataset-loader__status" role={status.startsWith("Error:") ? "alert" : "status"} aria-live="polite">{status}</p>}
    </div>
  );
}

export default DatasetLoader;
