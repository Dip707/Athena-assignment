# Test Query Results

## Run provenance

- Semantic index: **BM25 FALLBACK**
- AI curation: **CONFIGURED BUT NO TAGS/FALLBACK** (key presence only; key value is never reported)

## "Gaming keyboard under ₹5000"

*Intended evaluation target:* Price-filtered keyword query. Tests: BM25 matching on 'gaming keyboard' + price range filtering. Should match ~30+ products including IDs like 2, 6, 10, 12, etc. with prices < 5000.

Applied filters: `{'price_max': 5000.0, 'category_hint': 'Gaming Keyboards'}`

Total matches: 50

| # | Title | Category | Price | BM25 rank | Semantic rank | Fused score | Tag |
|---|-------|----------|-------|-----------|----------------|-------------|-----|
| 1 | Gaming Keyboard Budget Under 3000 | Gaming Keyboards | ₹2299 | 5 | None | 0.0154 |  |
| 2 | Gaming Keyboard Compact Layout | Gaming Keyboards | ₹2999 | 7 | None | 0.0149 |  |
| 3 | Laptop Gaming Keyboard Portable | Gaming Keyboards | ₹3199 | 8 | None | 0.0147 |  |
| 4 | Gaming Keyboard Compact Wireless | Gaming Keyboards | ₹3699 | 10 | None | 0.0143 |  |
| 5 | Gaming Keyboard Cable Coiled | Gaming Keyboards | ₹3599 | 11 | None | 0.0141 |  |

## "Gift cards for PlayStation"

*Intended evaluation target:* Vocabulary variation test. Some products say 'PlayStation gift card' (ID 36), others say 'PSN Wallet' (ID 37) or 'PlayStation Store credit' (ID 38). Tests semantic matching for synonyms. Should match gift card products but exclude Xbox/Steam.

Applied filters: `{'category_hint': 'Gift Cards'}`

Total matches: 50

| # | Title | Category | Price | BM25 rank | Semantic rank | Fused score | Tag |
|---|-------|----------|-------|-----------|----------------|-------------|-----|
| 1 | PlayStation Gift Card 500 | Gift Cards | ₹500 | 1 | None | 0.0164 |  |
| 2 | PlayStation Store Credit 2000 | Gift Cards | ₹2000 | 2 | None | 0.0161 |  |
| 3 | PSN Balance Top-up 5000 | Gift Cards | ₹5000 | 3 | None | 0.0159 |  |
| 4 | PSN Wallet Top-up 1000 | Gift Cards | ₹1000 | 4 | None | 0.0156 |  |
| 5 | Xbox Live Credits 1000 | Gift Cards | ₹1000 | 5 | None | 0.0154 |  |

## "Budget mechanical keyboard"

*Intended evaluation target:* Budget adjective + mechanical keyword test. Should return products like IDs 2, 6, 10 using both terms, plus others using synonyms like 'inexpensive', 'affordable', 'low-cost' paired with 'mechanical'.

Applied filters: `{'category_hint': 'Gaming Keyboards'}`

Total matches: 50

| # | Title | Category | Price | BM25 rank | Semantic rank | Fused score | Tag |
|---|-------|----------|-------|-----------|----------------|-------------|-----|
| 1 | Clicky Switch Mechanical Board Budget | Gaming Keyboards | ₹3299 | 1 | None | 0.0164 |  |
| 2 | Affordable Clicky Mechanical Board | Gaming Keyboards | ₹2799 | 2 | None | 0.0161 |  |
| 3 | Budget Keyboard Low Price Gaming | Gaming Keyboards | ₹1299 | 3 | None | 0.0159 |  |
| 4 | Gaming Keyboard Wireless Mechanical | Gaming Keyboards | ₹6799 | 4 | None | 0.0156 |  |
| 5 | Gaming Keyboard Compact Mechanical | Gaming Keyboards | ₹3899 | 5 | None | 0.0154 |  |

## "Mechanical keyboard"

*Intended evaluation target:* Pure keyword query. Tests BM25 on exact term match. Should return ~60+ keyboard products, though some vary vocabulary (e.g., 'tactical', 'clicky', 'tactile', 'optical', 'wireless' without explicit 'mechanical').

Applied filters: `{'category_hint': 'Gaming Keyboards'}`

Total matches: 50

| # | Title | Category | Price | BM25 rank | Semantic rank | Fused score | Tag |
|---|-------|----------|-------|-----------|----------------|-------------|-----|
| 1 | Gaming Keyboard Wireless Mechanical | Gaming Keyboards | ₹6799 | 1 | None | 0.0164 |  |
| 2 | Gaming Keyboard Compact Mechanical | Gaming Keyboards | ₹3899 | 2 | None | 0.0161 |  |
| 3 | Refurbished Gaming Keyboard Mechanical | Gaming Keyboards | ₹2999 | 3 | None | 0.0159 |  |
| 4 | Keyboard Mechanical Compact 61 Key | Gaming Keyboards | ₹3999 | 5 | None | 0.0154 |  |
| 5 | Gaming Keyboard Silent Mechanical | Gaming Keyboards | ₹5699 | 6 | None | 0.0152 |  |

## "Clicky switches keyboard"

*Intended evaluation target:* Synonym variation test. Products using 'clicky switches' (IDs 2, 10, 83) should match alongside those saying 'mechanical keyboard' or 'blue switches'. Tests semantic understanding of switch types.

Applied filters: `{'category_hint': 'Gaming Keyboards'}`

Total matches: 50

| # | Title | Category | Price | BM25 rank | Semantic rank | Fused score | Tag |
|---|-------|----------|-------|-----------|----------------|-------------|-----|
| 1 | Clicky Switch Mechanical Board Budget | Gaming Keyboards | ₹3299 | 1 | None | 0.0164 |  |
| 2 | Budget Clicky Keyboard for Gaming | Gaming Keyboards | ₹3199 | 2 | None | 0.0161 |  |
| 3 | Affordable Clicky Mechanical Board | Gaming Keyboards | ₹2799 | 3 | None | 0.0159 |  |
| 4 | Gaming Keyboard Stainless Steel Switches | Gaming Keyboards | ₹8599 | 4 | None | 0.0156 |  |
| 5 | Gaming Keyboard Optical Switches | Gaming Keyboards | ₹7899 | 5 | None | 0.0154 |  |

## "PSN wallet top-up under 2000"

*Intended evaluation target:* Vocabulary + price filter. PSN/PlayStation nomenclature variant. Should match gift card products like ID 37 (₹1000) but exclude ID 38 (₹2000) and higher due to price constraint. Tests non-standard product naming.

Applied filters: `{'price_max': 2000.0}`

Total matches: 18

| # | Title | Category | Price | BM25 rank | Semantic rank | Fused score | Tag |
|---|-------|----------|-------|-----------|----------------|-------------|-----|
| 1 | PSN Wallet Top-up 1000 | Gift Cards | ₹1000 | 1 | None | 0.0164 |  |
| 2 | Gaming Mouse Under 2000 Budget | Gaming Mice | ₹1499 | 3 | None | 0.0159 |  |
| 3 | Steam Wallet Code 500 | Gift Cards | ₹500 | 4 | None | 0.0156 |  |
| 4 | PlayStation Store Credit 2000 | Gift Cards | ₹2000 | 7 | None | 0.0149 |  |
| 5 | Amazon Pay Digital Voucher 2000 | Gift Cards | ₹2000 | 8 | None | 0.0147 |  |

## "Gaming mouse under 2000"

*Intended evaluation target:* Different category with price filter. Should return budget gaming mice like IDs 20 (₹899), 24 (₹1599), 156 (₹899), 220 (₹1499). Tests cross-category search and price filtering on non-keyboard items.

Applied filters: `{'price_max': 2000.0}`

Total matches: 50

| # | Title | Category | Price | BM25 rank | Semantic rank | Fused score | Tag |
|---|-------|----------|-------|-----------|----------------|-------------|-----|
| 1 | Gaming Mouse Under 2000 Budget | Gaming Mice | ₹1499 | 1 | None | 0.0164 |  |
| 2 | Budget Gaming Mouse Under 1000 | Gaming Mice | ₹899 | 3 | None | 0.0159 |  |
| 3 | PlayStation Store Credit 2000 | Gift Cards | ₹2000 | 6 | None | 0.0152 |  |
| 4 | Amazon Pay Digital Voucher 2000 | Gift Cards | ₹2000 | 7 | None | 0.0149 |  |
| 5 | Steam Game Voucher 2000 | Gift Cards | ₹2000 | 8 | None | 0.0147 |  |

## "Headset surround sound"

*Intended evaluation target:* Feature-based query. Should match headsets with surround sound specifications like IDs 25 (7.1), 145 (5.1), 185 (virtual 7.1). Tests semantic matching on technical specifications.

Applied filters: `{'category_hint': 'Gaming Headsets'}`

Total matches: 23

| # | Title | Category | Price | BM25 rank | Semantic rank | Fused score | Tag |
|---|-------|----------|-------|-----------|----------------|-------------|-----|
| 1 | Gaming Headset Surround Sound | Gaming Headsets | ₹3899 | 1 | None | 0.0164 |  |
| 2 | Gaming Headset Virtual 7.1 Surround | Gaming Headsets | ₹2999 | 2 | None | 0.0161 |  |
| 3 | Gaming Headset Surround 5.1 | Gaming Headsets | ₹3499 | 3 | None | 0.0159 |  |
| 4 | Gaming Headset Virtual Surround 7.1 | Gaming Headsets | ₹3099 | 4 | None | 0.0156 |  |
| 5 | Gaming Headset for Mobile Gaming | Gaming Headsets | ₹1699 | 5 | None | 0.0154 |  |

## "Gaming chair ergonomic under 15000"

*Intended evaluation target:* Multi-feature query with price. Should match ergonomic gaming chairs like IDs 51 (₹12999), 123 (₹14999), 211 (₹12999). Tests field-specific filtering + vocabulary variation.

Applied filters: `{'price_max': 15000.0, 'category_hint': 'Gaming Chairs'}`

Total matches: 50

| # | Title | Category | Price | BM25 rank | Semantic rank | Fused score | Tag |
|---|-------|----------|-------|-----------|----------------|-------------|-----|
| 1 | Gaming Chair under Budget 10000 | Gaming Chairs | ₹8999 | 1 | None | 0.0164 |  |
| 2 | Compact Gaming Chair Small Space | Gaming Chairs | ₹7999 | 2 | None | 0.0161 |  |
| 3 | Gaming Chair Ergonomic | Gaming Chairs | ₹12999 | 3 | None | 0.0159 |  |
| 4 | Gaming Chair Mesh Back | Gaming Chairs | ₹10999 | 7 | None | 0.0149 |  |
| 5 | Gaming Chair with Armrest Padding | Gaming Chairs | ₹10999 | 8 | None | 0.0147 |  |

## "Dishwasher"

*Intended evaluation target:* No-match baseline test. Query outside gaming/electronics domain should return zero or near-zero relevant results, validating that search correctly filters for product catalog relevance.

Applied filters: `{}`

Total matches: 0

_No results._
