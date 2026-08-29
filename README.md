# Vitamin Shoppe $1 Dollar Deals Tracker

A simple, mobile-friendly web page and automated scraping pipeline to track The Vitamin Shoppe's Thursday–Sunday **$1 Energy Drink of the Week** deals.

---

## ⚡ Features

* **Outrun Synthwave Mobile UI (`index.html`)**: Clean, responsive 80s neon aesthetic that dynamically displays the active $1 deal, date range, purchase limits, and companion offers.
* **Firecrawl Scraper Pipeline (`scraper.py`)**: Uses Firecrawl Cloud API with structured schema extraction to bypass DataDome anti-bot protections and output clean, typed `deals.json`.
* **Zero Overhead**: Can be run locally, via GitHub Actions cron, or on any static hosting platform (Vercel, Netlify, Cloudflare Pages, GitHub Pages).

---

## 🚀 Quick Start

### 1. View the Web Page Locally
Open `index.html` directly in your browser or run:
```bash
python3 -m http.server 3000
```
Visit `http://localhost:3000`.

### 2. Update Deals with Firecrawl
Set your free Firecrawl API key (free tier includes 500 requests/month):
```bash
export FIRECRAWL_API_KEY="fc-your-key-here"
python3 scraper.py
```
This queries `https://www.vitaminshoppe.com/c/deals/promotions`, extracts the structured JSON, and writes it directly to `deals.json`.

---

## 📅 Promotion Details
* **Deal Schedule:** Every Thursday through Sunday.
* **Standard Offer:** $1 per single can for featured energy drinks (Limit 6 per customer/day).
* **This Week:** **Jocko GO Energy Drinks ($1.00)** + Jocko Molk RTD Protein Shakes ($2.00).
