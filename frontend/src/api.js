// API client for the AI Product Search backend.
//
// Contract (see backend/app/models.py):
//   GET /search?q=<query>  ->  SearchResponse {
//     query: string,
//     results: [{
//       product: { id, title, description, category, price },
//       bm25_rank, semantic_rank, bm25_score, semantic_score, fused_score,
//       explanation
//     }],
//     applied_filters, total_results, page, page_size
//   }
//
// The fusion/ranking fields are still optional/nullable on the backend
// (fusion.py isn't implemented yet), so callers should tolerate null/missing
// values on any of them.

const API_BASE_URL = "http://localhost:8000";

/**
 * Read whether the backend has a catalog ready for searching.
 * @returns {Promise<{loaded: boolean, product_count: number, ai_enabled: boolean}>}
 */
export async function getCatalogStatus() {
  const url = `${API_BASE_URL}/catalog/status`;

  let response;
  try {
    response = await fetch(url);
  } catch {
    throw new Error(
      `Could not reach the search server at ${API_BASE_URL}. Is the backend running?`
    );
  }

  if (!response.ok) {
    throw new Error(
      `Catalog status failed (${response.status} ${response.statusText})`
    );
  }

  try {
    return await response.json();
  } catch {
    throw new Error("The search server returned an invalid catalog status.");
  }
}

/**
 * Run a product search against the backend.
 *
 * `curate` is only sent when explicitly provided so existing callers that do
 * not pass options retain the backend's default behavior.
 * @param {string} query
 * @param {{curate?: boolean}} [options]
 * @returns {Promise<{query: string, results: Array<Object>, applied_filters?: Object, total_results?: number, page?: number, page_size?: number}>}
 */
export async function searchProducts(query, options = {}) {
  const curate =
    typeof options === "boolean" ? options : options?.curate;
  const curateParam = typeof curate === "boolean" ? `&curate=${curate}` : "";
  const url = `${API_BASE_URL}/search?q=${encodeURIComponent(query)}${curateParam}`;

  let response;
  try {
    response = await fetch(url);
  } catch {
    // Network-level failure: server down, CORS blocked, DNS, etc.
    throw new Error(
      `Could not reach the search server at ${API_BASE_URL}. Is the backend running?`
    );
  }

  if (!response.ok) {
    let detail = "";
    try {
      const body = await response.json();
      if (body?.detail) {
        detail = `: ${
          typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail)
        }`;
      }
    } catch {
      // response body wasn't JSON (or was empty) — ignore, use status text only
    }
    throw new Error(
      `Search failed (${response.status} ${response.statusText})${detail}`
    );
  }

  try {
    return await response.json();
  } catch {
    throw new Error("The search server returned an invalid response.");
  }
}

// Keep the original API name available to callers while exposing the more
// descriptive name used by the search flow.
export const search = searchProducts;

/**
 * Replace the backend's product catalog and rebuild its search indices.
 * @param {Array<Object>} products - array of {id, title, description, category, price}
 * @returns {Promise<{indexed: number}>}
 */
export async function uploadDataset(products) {
  const url = `${API_BASE_URL}/index`;

  let response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(products),
    });
  } catch {
    throw new Error(
      `Could not reach the search server at ${API_BASE_URL}. Is the backend running?`
    );
  }

  if (!response.ok) {
    let detail = "";
    try {
      const body = await response.json();
      if (body?.detail) {
        detail = `: ${
          typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail)
        }`;
      }
    } catch {
      // ignore non-JSON error body
    }
    throw new Error(
      `Dataset upload failed (${response.status} ${response.statusText})${detail}`
    );
  }

  return await response.json();
}
