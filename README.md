# UAE Market Intelligence System

A premium dashboard for monitoring market opportunities across the UAE — tracking social media, forums, news, and review platforms to surface emerging pain points, unmet needs, and trending topics that signal business opportunities.

## Features

- **Multi-platform monitoring** — Reddit, X/Twitter, LinkedIn, Facebook Groups, Arabic Forums, Google Reviews, News
- **AI-powered analysis** — Extracts pain points, unmet needs, trending topics, and sentiment from raw content
- **Bilingual support** — Processes and displays both Arabic and English content
- **Sector categorization** — Food & Beverage, Fintech, Healthcare, Real Estate, Retail, Education, Logistics, Tourism
- **Opportunity scoring** — Signals rated High/Medium/Low based on frequency and cross-platform validation
- **Interactive filtering** — Filter by sector, search across all content

## Tech Stack

| Layer | Tool |
|-------|------|
| Orchestration | n8n (cloud) |
| Data Collection | Apify |
| AI Analysis | OpenAI GPT-4o |
| Web/News Search | Tavily API |
| Data Storage | Google Sheets / SQLite |
| Email Delivery | Gmail via n8n |
| Frontend | Vanilla HTML/CSS/JS |
| Backend API | Python (CGI) |

## Architecture

The system runs as two n8n workflows:

1. **Data Collection** (nightly) — Collects posts from Reddit, X, LinkedIn, Facebook Groups, Arabic forums, and Google Reviews
2. **Analysis & Digest** (morning) — AI analyzes raw data, ranks insights, and sends a daily email digest

## Project Structure

```
├── index.html          # Main dashboard UI
├── style.css           # Premium dark theme styles
├── app.js              # Frontend logic, filtering, rendering
├── cgi-bin/
│   └── api.py          # Backend API with SQLite storage
└── README.md
```

## Build Plan

| Phase | Goal | Timeline |
|-------|------|----------|
| Phase 1 — Foundation | Data collection pipeline & storage | Week 1–2 |
| Phase 2 — AI Analysis | NLP, sentiment analysis & clustering | Week 3 |
| Phase 3 — Daily Digest | Automated reporting & email alerts | Week 4 |
| Phase 4 — Expand | Additional sources & markets | Week 5+ |

---

Built for Rashed Al Dhaheri · Abu Dhabi, UAE
