# SignalDesk Product Usage Analytics Pipeline

A Python-based utility script designed to ingest, clean, and audit daily workflow performance logs for SignalDesk. The pipeline automatically flags hidden quality drops where internal model confidence metrics diverge sharply from human validation data.

## The Core Problem
In automated assistance systems like SignalDesk, a high system confidence score does not automatically guarantee high-quality human utility. Relying blindly on model logs creates operational blind spots. 

This tool functions as an automated internal audit layer for product teams. It actively surfaces the exact operational windows where quantitative model performance indicators conflict with real-world user metrics (such as user ratings and human acceptance rates).

## Artifact Features

### 1. Ingestion & Data Quality Repairs (`load_and_clean`)
Directly fixes structural irregularities found within real-world system data exports:
* **String Casing Alignment:** Normalizes inconsistent team identifiers (e.g., mixing `"Product"` and `"product"`) to prevent data fragmentation during `groupby` splittings.
* **Safe Numeric Coercion:** Coerces dirty text parameters (such as literal `"n/a"` strings) into standard numeric floats to prevent type errors across math calculations.
* **Export Artifact Deduplication:** Flags and isolates identical duplicate row instances across matching primary indices while keeping the initial record intact.

### 2. Operational Health Summary (`workflow_summary`)
Generates an explicit performance matrix sorted by total volume, providing clean operational visibility into:
* Volume metrics (`sessions`, `completed`, `accepted_output`, `flagged_for_review`)
* Operational rates (`completion_rate`, `acceptance_rate`, `flag_rate`)
* User satisfaction signals (`avg_minutes_saved`, `user_rating`)

### 3. Divergence Profiling (`flag_suspicious_days`)
Applies specialized conditional logic rules to expose hidden failure profiles:
* **The Confidence Trap:** Extracts dates where model confidence remains high ($\geq 0.85$) but human acceptance plunges ($\le 0.5$).
* **Relative Variance Spikes:** Tracks localized volatility by identifying days where a workflow's daily flag rate surges $1.5\times$ above its own historical running mean.

## Operational Spotlight: The August 7th Signal
When evaluated against the product logs, the pipeline isolates a critical behavioral shift on **2026-08-07** within the `Reply draft` workflow:
* **The Conflict:** Model `median_confidence` hit its maximum peak performance rating for the week (**0.91**).
* **The Reality:** Human acceptance collapsed, user ratings bottomed out at **2.1**, and system review flags spiked aggressively to **0.40**.
* **Root Cause Guidance:** Corresponding logs note a mid-day policy mutation. This confirms that tracking confidence scores in isolation risks masking immediate drops in customer experience during system changes.

## Engineering Foundations
* **Language:** Python 3.8+
* **Dependencies:** `pandas`
* **File Structure:**
  * `analyze_signaldesk.py`: Core ingestion, cleaning, and analytics execution pipeline.
  * `sample-data/product_usage_data.csv`: Target dataset source file.

## Quick Start

1. Ensure your source file is located in the target directory:
   `sample-data/product_usage_data.csv`

2. Trigger the pipeline directly from your terminal terminal:
   ```bash
   python analyze_signaldesk.py
   ```
