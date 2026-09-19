# Tokenization Digest

I created an automated monthly newsletter to track research and developments in LLM tokenization.
The pipeline collects relevant papers from various sources, such as arXiv, LessWrong, Google Scholar etc.
I write a short editorial review for one selected article for each issue. The rest of the papers are automatically reviewed by Claude Sonnet.
The newsletter can be found on Substack: https://solidgoldmagikarp.substack.com

## Pipeline

```
Collectors (arxiv, Semantic Scholar, HF blog, Google Scholar)
    ↓
Filter & Deduplicate (keyword matching, relevance scoring)
    ↓
Summarize (Claude API generates per-paper summaries)
    ↓
Editorial (Claude API generates connecting narrative)
    ↓
Format (Markdown + HTML ready for Substack)
```

## How to use

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/tokenization-newsletter.git
cd tokenization-newsletter
pip install -r requirements.txt
```

### 2. Set the API key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 3. Run the pipeline

```bash
# Dry run — collect and filter only
python -m src.pipeline --dry-run --issue 1

# Collect only
python -m src.pipeline --collect-only

# Full run — generates complete newsletter
python -m src.pipeline --issue 1
```

### 4. Output

Placed to the `output/` directory:
- `issue_1_YYYYMM.md` — Markdown version
- `issue_1_YYYYMM.html` — HTML version
- `issue_1_YYYYMM_data.json` — Raw data

## Configuration

`config.yaml` can be used to customize:
- **Keywords**: search terms
- **Sources**: arxiv categories, RSS feeds etc.
- **Claude settings**: model, token limits
- **Newsletter settings**: max items, lookback period

### Google Scholar Alerts

1. Go to [scholar.google.com](https://scholar.google.com)
2. Search for your topic (e.g., "tokenization language model")
3. Click the envelope icon → Create Alert
4. Get the RSS feed URL
5. Add it to `config.yaml` under `google_scholar.alert_feeds`

## Cost

Approximately $0.10-0.30 per issue using Claude Sonnet (depends on number of papers found). The collectors use free APIs only.
