# 📰 Tokenization Digest

A monthly automated newsletter tracking research and developments in LLM tokenization.

## How It Works

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

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/tokenization-newsletter.git
cd tokenization-newsletter
pip install -r requirements.txt
```

### 2. Set your API key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 3. Run the pipeline

```bash
# Dry run — collect and filter only, no API costs
python -m src.pipeline --dry-run --issue 1

# Collect only — save raw data for inspection
python -m src.pipeline --collect-only

# Full run — generates complete newsletter
python -m src.pipeline --issue 1
```

### 4. Find your output

After a full run, check the `output/` directory:
- `issue_1_YYYYMM.md` — Markdown version
- `issue_1_YYYYMM.html` — HTML version (paste into Substack)
- `issue_1_YYYYMM_data.json` — Raw data for reference

## GitHub Actions (Automated Monthly)

1. Push this repo to GitHub
2. Go to **Settings → Secrets → Actions**
3. Add `ANTHROPIC_API_KEY` as a repository secret
4. The workflow runs automatically on the 1st of each month
5. You can also trigger it manually from the **Actions** tab

## Configuration

Edit `config.yaml` to customize:
- **Keywords**: What terms to search for
- **Sources**: Which arxiv categories, RSS feeds, etc.
- **Claude settings**: Model, token limits
- **Newsletter settings**: Max items, lookback period

### Adding Google Scholar Alerts

1. Go to [scholar.google.com](https://scholar.google.com)
2. Search for your topic (e.g., "tokenization language model")
3. Click the envelope icon → Create Alert
4. Get the RSS feed URL
5. Add it to `config.yaml` under `google_scholar.alert_feeds`

## Publishing to Substack

1. Run the pipeline to generate the newsletter
2. Open the HTML file in a browser, or copy the Markdown
3. In Substack, create a new post
4. Paste the content (Substack handles Markdown well)
5. Review, edit your editorial voice into it, and publish!

## Tips

- **Always review before publishing.** The AI-generated summaries and editorial are drafts — add your own voice and expertise.
- **Start with `--dry-run`** to see what papers would be included before spending API credits.
- **Tune relevance** by adjusting keywords in `config.yaml` if you're getting too many false positives.

## Cost

Approximately $0.10-0.30 per issue using Claude Sonnet (depends on number of papers found). The collectors use free APIs only.
