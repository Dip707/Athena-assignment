import { useState } from "react";
import "./ProductCard.css";

function formatPrice(price) {
  if (price === null || price === undefined || Number.isNaN(Number(price))) {
    return "Price unavailable";
  }
  return `₹${Number(price).toLocaleString("en-IN", {
    maximumFractionDigits: 0,
  })}`;
}

// Renders a value, or a placeholder dash if it's missing/null — the
// backend's fusion logic (bm25_rank / semantic_rank / fused_score) isn't
// implemented yet, so these fields may legitimately be absent.
function formatField(value, digits) {
  if (value === null || value === undefined) return "n/a";
  return typeof digits === "number" ? Number(value).toFixed(digits) : value;
}

/**
 * A single product result card with an expandable "why this ranked here"
 * section showing BM25 rank, semantic rank, and fused score.
 * @param {{ result: Object }} props
 */
export default function ProductCard({ result }) {
  const [expanded, setExpanded] = useState(false);
  const product = result?.product ?? {};
  const { bm25_rank, semantic_rank, fused_score, tag } = result ?? {};

  return (
    <li className="product-card">
      {tag && <span className="product-card__tag">{tag}</span>}
      <div className="product-card__header">
        <h3 className="product-card__title">
          {product.title || "Untitled product"}
        </h3>
        <span className="product-card__price">{formatPrice(product.price)}</span>
      </div>

      {product.category && (
        <span className="product-card__category">{product.category}</span>
      )}

      <p className="product-card__description">{product.description || ""}</p>

      <button
        type="button"
        className="product-card__toggle"
        onClick={() => setExpanded((prev) => !prev)}
        aria-expanded={expanded}
      >
        {expanded ? "▲ Hide" : "▼ Show"} why this ranked here
      </button>

      {expanded && (
        <div className="product-card__explanation">
          <span><small>Keyword rank</small><strong>{formatField(bm25_rank)}</strong></span>
          <span><small>Semantic rank</small><strong>{formatField(semantic_rank)}</strong></span>
          <span><small>Combined score</small><strong>{formatField(fused_score, 3)}</strong></span>
        </div>
      )}
    </li>
  );
}
