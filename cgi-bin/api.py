#!/usr/bin/env python3
"""
UAE Market Intelligence — Backend API
Serves signal data from SQLite database via CGI
Endpoint: /cgi-bin/api.py?action=...
"""

import cgi
import cgitb
import json
import sqlite3
import os
import sys
from datetime import datetime, timedelta
import random

cgitb.enable()

# ===================== DB SETUP =====================
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'market_intel.db')

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        arabic_title TEXT,
        summary TEXT,
        type TEXT CHECK(type IN ('trending','pain_point','opportunity','mention')),
        sector TEXT,
        platform TEXT,
        priority TEXT CHECK(priority IN ('High','Medium','Low')),
        score INTEGER,
        mentions INTEGER DEFAULT 0,
        keywords TEXT,
        raw_text TEXT,
        source_url TEXT,
        date_collected TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS platforms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        description TEXT,
        active BOOLEAN DEFAULT 1
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS sectors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        description TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS metadata (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    # Seed if empty
    cursor = conn.execute('SELECT COUNT(*) FROM signals')
    if cursor.fetchone()[0] == 0:
        seed_data(conn)
    conn.close()

# ===================== SEED DATA =====================
SEED_SIGNALS = [
  {"title":"Surge in demand for halal certified delivery platforms","arabic_title":"\u0632\u064a\u0627\u062f\u0629 \u0627\u0644\u0637\u0644\u0628 \u0639\u0644\u0649 \u0645\u0646\u0635\u0627\u062a \u0627\u0644\u062a\u0648\u0635\u064a\u0644 \u0627\u0644\u062d\u0644\u0627\u0644","summary":"Multiple users across UAE subreddits and Facebook Groups report difficulty finding reliable halal-certified food delivery options beyond major apps. Small restaurant owners highlight gaps in last-mile logistics for halal-only kitchens.","type":"trending","sector":"Food & Beverage","platform":"Reddit","priority":"High","score":91,"mentions":87,"keywords":"halal delivery,food logistics,UAE dining,last-mile","date_collected":"2026-02-20","source_url":"https://reddit.com/r/dubai","raw_text":"Honestly the halal delivery scene in Dubai is still super fragmented."},
  {"title":"SME owners frustrated with UAE bank onboarding delays","arabic_title":"\u0623\u0635\u062d\u0627\u0628 \u0627\u0644\u0634\u0631\u0643\u0627\u062a \u0627\u0644\u0635\u063a\u064a\u0631\u0629 \u064a\u0639\u0627\u0646\u0648\u0646 \u0645\u0646 \u062a\u0623\u062e\u064a\u0631\u0627\u062a \u0641\u062a\u062d \u0627\u0644\u062d\u0633\u0627\u0628\u0627\u062a \u0627\u0644\u0628\u0646\u0643\u064a\u0629","summary":"A recurring pain point: small business owners spending 4-8 weeks waiting for corporate bank account approvals.","type":"pain_point","sector":"Fintech","platform":"LinkedIn","priority":"High","score":88,"mentions":62,"keywords":"SME banking,account opening,fintech UAE,digital banking","date_collected":"2026-02-21","source_url":"https://linkedin.com","raw_text":"It took us 6 weeks to open a corporate account."},
  {"title":"Arabic-language mental health content severely underserved","arabic_title":"\u0645\u062d\u062a\u0648\u0649 \u0627\u0644\u0635\u062d\u0629 \u0627\u0644\u0646\u0641\u0633\u064a\u0629 \u0628\u0627\u0644\u0644\u063a\u0629 \u0627\u0644\u0639\u0631\u0628\u064a\u0629 \u0634\u062d\u064a\u062d","summary":"Growing conversation about lack of quality mental health resources in Arabic. Strong unmet demand.","type":"opportunity","sector":"Healthcare","platform":"X / Twitter","priority":"High","score":85,"mentions":74,"keywords":"mental health,Arabic content,wellbeing UAE,telehealth","date_collected":"2026-02-19","source_url":"https://x.com","raw_text":"\u0643\u0644 \u062a\u0637\u0628\u064a\u0642\u0627\u062a \u0627\u0644\u0635\u062d\u0629 \u0627\u0644\u0646\u0641\u0633\u064a\u0629 \u0628\u0627\u0644\u0625\u0646\u062c\u0644\u064a\u0632\u064a."},
  {"title":"Real estate investors seeking off-plan transparency tools","arabic_title":"\u0627\u0644\u0645\u0633\u062a\u062b\u0645\u0631\u0648\u0646 \u0627\u0644\u0639\u0642\u0627\u0631\u064a\u0648\u0646 \u064a\u0628\u062d\u062b\u0648\u0646 \u0639\u0646 \u0623\u062f\u0648\u0627\u062a \u0634\u0641\u0627\u0641\u064a\u0629 \u0644\u0644\u0645\u0634\u0627\u0631\u064a\u0639 \u0639\u0644\u0649 \u0627\u0644\u062e\u0631\u064a\u0637\u0629","summary":"Investors want dashboards tracking construction progress, escrow releases, and developer reputation.","type":"pain_point","sector":"Real Estate","platform":"Forums","priority":"High","score":83,"mentions":55,"keywords":"off-plan,real estate UAE,investor tools,transparency","date_collected":"2026-02-22","source_url":"https://propertyfinder.ae","raw_text":"Bought off-plan 2 years ago, zero communication from developer."},
  {"title":"Cross-border remittance fees still too high say expats","arabic_title":"\u0631\u0633\u0648\u0645 \u0627\u0644\u062a\u062d\u0648\u064a\u0644 \u0627\u0644\u0645\u0627\u0644\u064a \u0644\u0627 \u062a\u0632\u0627\u0644 \u0645\u0631\u062a\u0641\u0639\u0629 \u0628\u062d\u0633\u0628 \u0627\u0644\u0645\u063a\u062a\u0631\u0628\u064a\u0646","summary":"Expat communities express ongoing frustration with remittance fees averaging 2-4%.","type":"pain_point","sector":"Fintech","platform":"Facebook Groups","priority":"Medium","score":77,"mentions":91,"keywords":"remittance,expat UAE,money transfer,fees","date_collected":"2026-02-18","source_url":"https://facebook.com/groups","raw_text":"Still paying 3.5% to send money home."},
  {"title":"D2C grocery brands growing in Abu Dhabi market","arabic_title":"\u0646\u0645\u0648 \u0627\u0644\u0639\u0644\u0627\u0645\u0627\u062a \u0627\u0644\u062a\u062c\u0627\u0631\u064a\u0629 \u0627\u0644\u0645\u0628\u0627\u0634\u0631\u0629 \u0644\u0644\u0645\u0633\u062a\u0647\u0644\u0643 \u0641\u064a \u0633\u0648\u0642 \u0623\u0628\u0648\u0638\u0628\u064a","summary":"UAE-based D2C grocery startups gaining traction. Consumers cite freshness guarantees and subscription models.","type":"trending","sector":"Food & Beverage","platform":"LinkedIn","priority":"Medium","score":74,"mentions":38,"keywords":"D2C grocery,Abu Dhabi,subscription,fresh food","date_collected":"2026-02-23","source_url":"https://linkedin.com","raw_text":"Our D2C organic vegetable box just hit 2,000 subscribers in Abu Dhabi."},
  {"title":"EdTech platforms lacking Arabic STEM content for K-12","arabic_title":"\u0645\u0646\u0635\u0627\u062a \u0627\u0644\u062a\u0639\u0644\u064a\u0645 \u0627\u0644\u0625\u0644\u0643\u062a\u0631\u0648\u0646\u064a \u062a\u0641\u062a\u0642\u0631 \u0625\u0644\u0649 \u0645\u062d\u062a\u0648\u0649 STEM \u0628\u0627\u0644\u0639\u0631\u0628\u064a\u0629 \u0644\u0644\u0645\u0631\u0627\u062d\u0644 \u0627\u0644\u062f\u0631\u0627\u0633\u064a\u0629","summary":"Clear market gap for Arabic-first ed-tech serving K-12 students.","type":"opportunity","sector":"Education","platform":"Forums","priority":"High","score":82,"mentions":49,"keywords":"edtech,Arabic STEM,K-12,gamified learning","date_collected":"2026-02-20","source_url":"https://forums.ae","raw_text":"I want something engaging, Arabic, and curriculum-aligned for UAE schools."},
  {"title":"Healthcare appointment booking fragmented across Emirates","arabic_title":"\u062d\u062c\u0632 \u0627\u0644\u0645\u0648\u0627\u0639\u064a\u062f \u0627\u0644\u0635\u062d\u064a\u0629 \u0645\u062c\u0632\u0623 \u0639\u0628\u0631 \u0627\u0644\u0625\u0645\u0627\u0631\u0627\u062a","summary":"Users want a single unified platform aggregating availability across public and private providers.","type":"pain_point","sector":"Healthcare","platform":"Google Reviews","priority":"Medium","score":71,"mentions":43,"keywords":"healthcare booking,UAE hospitals,unified platform,appointment","date_collected":"2026-02-21","source_url":"https://maps.google.com","raw_text":"Had to call 4 different numbers to book a specialist."},
  {"title":"Sustainable packaging demand rising among UAE retailers","arabic_title":"\u0627\u0631\u062a\u0641\u0627\u0639 \u0627\u0644\u0637\u0644\u0628 \u0639\u0644\u0649 \u0627\u0644\u062a\u063a\u0644\u064a\u0641 \u0627\u0644\u0645\u0633\u062a\u062f\u0627\u0645 \u0628\u064a\u0646 \u062a\u062c\u0627\u0631 \u0627\u0644\u062a\u062c\u0632\u0626\u0629 \u0641\u064a \u0627\u0644\u0625\u0645\u0627\u0631\u0627\u062a","summary":"UAE brands increasingly committing to sustainable packaging amid regulatory pressure and consumer demand.","type":"trending","sector":"Retail","platform":"News","priority":"Medium","score":68,"mentions":29,"keywords":"sustainable packaging,retail UAE,eco,regulation","date_collected":"2026-02-22","source_url":"https://thenationalnews.com","raw_text":"UAE retailers are fast-tracking sustainable packaging transitions."},
  {"title":"Tourism operators want AI-powered multilingual tour guides","arabic_title":"\u0645\u0634\u063a\u0644\u0648 \u0627\u0644\u0633\u064a\u0627\u062d\u0629 \u064a\u0631\u064a\u062f\u0648\u0646 \u0645\u0631\u0634\u062f\u064a\u0646 \u0633\u064a\u0627\u062d\u064a\u064a\u0646 \u0645\u062a\u0639\u062f\u062f\u064a \u0627\u0644\u0644\u063a\u0627\u062a \u0628\u0627\u0644\u0630\u0643\u0627\u0621 \u0627\u0644\u0627\u0635\u0637\u0646\u0627\u0639\u064a","summary":"UAE tour operators want AI audio guide technology supporting Arabic, English, Chinese, and Russian.","type":"opportunity","sector":"Tourism","platform":"LinkedIn","priority":"Medium","score":72,"mentions":22,"keywords":"AI tour guide,multilingual,tourism UAE,MICE","date_collected":"2026-02-19","source_url":"https://linkedin.com","raw_text":"We need AI audio guides that switch between Arabic and Mandarin."},
  {"title":"Last-mile logistics for e-commerce still unreliable in outer Abu Dhabi","arabic_title":"\u0627\u0644\u062e\u062f\u0645\u0627\u062a \u0627\u0644\u0644\u0648\u062c\u0633\u062a\u064a\u0629 \u0644\u0644\u062a\u062c\u0627\u0631\u0629 \u0627\u0644\u0625\u0644\u0643\u062a\u0631\u0648\u0646\u064a\u0629 \u063a\u064a\u0631 \u0645\u0648\u062b\u0648\u0642\u0629 \u0641\u064a \u0645\u0646\u0627\u0637\u0642 \u0623\u0628\u0648\u0638\u0628\u064a \u0627\u0644\u062e\u0627\u0631\u062c\u064a\u0629","summary":"Market opportunity for hyperlocal logistics player serving Al Ain, Madinat Zayed, and outer Emirates.","type":"pain_point","sector":"Logistics","platform":"X / Twitter","priority":"High","score":80,"mentions":58,"keywords":"last-mile,Abu Dhabi delivery,Al Ain,logistics gap","date_collected":"2026-02-23","source_url":"https://x.com","raw_text":"Al Ain delivery is a disaster compared to Dubai."},
  {"title":"Co-working space demand spiking in Sharjah and Northern Emirates","arabic_title":"\u0627\u0631\u062a\u0641\u0627\u0639 \u0627\u0644\u0637\u0644\u0628 \u0639\u0644\u0649 \u0645\u0633\u0627\u062d\u0627\u062a \u0627\u0644\u0639\u0645\u0644 \u0627\u0644\u0645\u0634\u062a\u0631\u0643 \u0641\u064a \u0627\u0644\u0634\u0627\u0631\u0642\u0629 \u0648\u0627\u0644\u0625\u0645\u0627\u0631\u0627\u062a \u0627\u0644\u0634\u0645\u0627\u0644\u064a\u0629","summary":"Sharjah and Ras Al Khaimah showing strong unmet demand for co-working spaces.","type":"opportunity","sector":"Real Estate","platform":"LinkedIn","priority":"Medium","score":70,"mentions":31,"keywords":"co-working,Sharjah,RAK,startup space","date_collected":"2026-02-20","source_url":"https://linkedin.com","raw_text":"Sharjah freelancers are forced to commute to Dubai for decent workspace."},
  {"title":"Digital wills and estate planning for expats an untapped niche","arabic_title":"\u0627\u0644\u0648\u0635\u0627\u064a\u0627 \u0627\u0644\u0631\u0642\u0645\u064a\u0629 \u0648\u062a\u062e\u0637\u064a\u0637 \u0627\u0644\u062a\u0631\u0643\u0627\u062a \u0644\u0644\u0645\u063a\u062a\u0631\u0628\u064a\u0646 \u0641\u0631\u0635\u0629 \u063a\u064a\u0631 \u0645\u0633\u062a\u063a\u0644\u0629","summary":"Very few tech products serve the UAE digital estate planning need for expats.","type":"opportunity","sector":"Fintech","platform":"Reddit","priority":"Medium","score":75,"mentions":37,"keywords":"digital will,estate planning,expat UAE,legaltech","date_collected":"2026-02-18","source_url":"https://reddit.com/r/expats","raw_text":"No idea how my assets would be handled if something happened to me."},
  {"title":"Restaurant owners demand better POS integrations with delivery apps","arabic_title":"\u0623\u0635\u062d\u0627\u0628 \u0627\u0644\u0645\u0637\u0627\u0639\u0645 \u064a\u0637\u0627\u0644\u0628\u0648\u0646 \u0628\u062a\u0643\u0627\u0645\u0644 \u0623\u0641\u0636\u0644 \u0628\u064a\u0646 \u0646\u0642\u0627\u0637 \u0627\u0644\u0628\u064a\u0639 \u0648\u062a\u0637\u0628\u064a\u0642\u0627\u062a \u0627\u0644\u062a\u0648\u0635\u064a\u0644","summary":"F&B operators cite double-entry headaches managing Talabat, Careem Food, and in-house POS separately.","type":"pain_point","sector":"Food & Beverage","platform":"Facebook Groups","priority":"Medium","score":69,"mentions":45,"keywords":"POS integration,Talabat,restaurant tech,UAE F&B","date_collected":"2026-02-22","source_url":"https://facebook.com/groups","raw_text":"Managing 3 delivery platforms + our POS is a nightmare."},
  {"title":"Corporate wellness programs underutilized in UAE SMEs","arabic_title":"\u0628\u0631\u0627\u0645\u062c \u0631\u0641\u0627\u0647\u064a\u0629 \u0627\u0644\u0645\u0648\u0638\u0641\u064a\u0646 \u063a\u064a\u0631 \u0645\u0633\u062a\u063a\u0644\u0629 \u0641\u064a \u0627\u0644\u0634\u0631\u0643\u0627\u062a \u0627\u0644\u0635\u063a\u064a\u0631\u0629 \u0648\u0627\u0644\u0645\u062a\u0648\u0633\u0637\u0629 \u0628\u0627\u0644\u0625\u0645\u0627\u0631\u0627\u062a","summary":"SMEs lack affordable, scalable wellness benefit platforms tailored to their employee demographics.","type":"opportunity","sector":"Healthcare","platform":"LinkedIn","priority":"Low","score":61,"mentions":18,"keywords":"corporate wellness,SME UAE,employee benefits,HR tech","date_collected":"2026-02-21","source_url":"https://linkedin.com","raw_text":"Big wellness platforms want AED 200K+ contracts. We're 30 people."},
  {"title":"Rising interest in UAE-based cloud kitchen concepts","arabic_title":"\u0627\u0647\u062a\u0645\u0627\u0645 \u0645\u062a\u0632\u0627\u064a\u062f \u0628\u0645\u0641\u0647\u0648\u0645 \u0627\u0644\u0645\u0637\u0627\u0628\u062e \u0627\u0644\u0633\u062d\u0627\u0628\u064a\u0629 \u0641\u064a \u0627\u0644\u0625\u0645\u0627\u0631\u0627\u062a","summary":"Demand emerging for plug-and-play cloud kitchen infrastructure with built-in delivery partnerships.","type":"trending","sector":"Food & Beverage","platform":"Reddit","priority":"Medium","score":66,"mentions":27,"keywords":"cloud kitchen,ghost kitchen,UAE F&B,food startup","date_collected":"2026-02-19","source_url":"https://reddit.com/r/dubai","raw_text":"Cloud kitchens in Dubai are filling up fast."},
  {"title":"Arabic language interfaces still lacking in SaaS tools","arabic_title":"\u0648\u0627\u062c\u0647\u0627\u062a \u0627\u0644\u0644\u063a\u0629 \u0627\u0644\u0639\u0631\u0628\u064a\u0629 \u0644\u0627 \u062a\u0632\u0627\u0644 \u062a\u0641\u062a\u0642\u0631 \u0625\u0644\u064a\u0647\u0627 \u0623\u062f\u0648\u0627\u062a SaaS","summary":"RTL support remains inconsistent even in major platforms. A large, underserved market.","type":"pain_point","sector":"Technology","platform":"X / Twitter","priority":"High","score":79,"mentions":53,"keywords":"Arabic UI,RTL,SaaS localization,Arabic tech","date_collected":"2026-02-20","source_url":"https://x.com","raw_text":"Why in 2026 do enterprise SaaS products still ship broken Arabic RTL support?"},
  {"title":"Demand for Islamic finance investment apps among millennials","arabic_title":"\u0627\u0644\u0637\u0644\u0628 \u0639\u0644\u0649 \u062a\u0637\u0628\u064a\u0642\u0627\u062a \u0627\u0644\u0627\u0633\u062a\u062b\u0645\u0627\u0631 \u0627\u0644\u0625\u0633\u0644\u0627\u0645\u064a\u0629 \u0628\u064a\u0646 \u062c\u064a\u0644 \u0627\u0644\u0623\u0644\u0641\u064a\u0629","summary":"UAE millennials want a Robinhood-style app that is fully Shariah-compliant and transparent.","type":"opportunity","sector":"Fintech","platform":"Reddit","priority":"High","score":84,"mentions":61,"keywords":"Islamic finance,halal investing,millennial UAE,Shariah","date_collected":"2026-02-23","source_url":"https://reddit.com/r/IslamicFinance","raw_text":"I want a simple, clean investing app that's halal."},
  {"title":"Tourism recovery driving demand for Arabic-first travel content creators","arabic_title":"\u062a\u0639\u0627\u0641\u064a \u0627\u0644\u0633\u064a\u0627\u062d\u0629 \u064a\u062f\u0641\u0639 \u0627\u0644\u0637\u0644\u0628 \u0646\u062d\u0648 \u0645\u0646\u0634\u0626\u064a \u0627\u0644\u0645\u062d\u062a\u0648\u0649 \u0627\u0644\u0633\u064a\u0627\u062d\u064a \u0628\u0627\u0644\u0644\u063a\u0629 \u0627\u0644\u0639\u0631\u0628\u064a\u0629","summary":"GCC domestic traveller is underserved in Arabic-language travel content on TikTok and YouTube.","type":"opportunity","sector":"Tourism","platform":"LinkedIn","priority":"Medium","score":67,"mentions":24,"keywords":"Arabic travel content,UAE tourism,influencer,GCC","date_collected":"2026-02-22","source_url":"https://linkedin.com","raw_text":"Investing in Arabic content creators for UAE tourism campaigns."},
  {"title":"Warehouse automation interest spiking among UAE 3PLs","arabic_title":"\u0627\u0631\u062a\u0641\u0627\u0639 \u0627\u0644\u0627\u0647\u062a\u0645\u0627\u0645 \u0628\u0623\u062a\u0645\u062a\u0629 \u0627\u0644\u0645\u0633\u062a\u0648\u062f\u0639\u0627\u062a \u0628\u064a\u0646 \u0634\u0631\u0643\u0627\u062a \u0627\u0644\u062e\u062f\u0645\u0627\u062a \u0627\u0644\u0644\u0648\u062c\u0633\u062a\u064a\u0629 \u0641\u064a \u0627\u0644\u0625\u0645\u0627\u0631\u0627\u062a","summary":"UAE 3PLs exploring robotics and WMS upgrades driven by labor cost pressures and e-commerce growth.","type":"trending","sector":"Logistics","platform":"News","priority":"Medium","score":65,"mentions":19,"keywords":"warehouse automation,robotics,3PL UAE,WMS","date_collected":"2026-02-21","source_url":"https://arabianbusiness.com","raw_text":"UAE logistics firms are fast-tracking warehouse automation investments."},
  {"title":"Mention: Careem expanding into new service verticals","arabic_title":"\u0643\u0631\u064a\u0645 \u062a\u062a\u0648\u0633\u0639 \u0641\u064a \u0642\u0637\u0627\u0639\u0627\u062a \u062e\u062f\u0645\u064a\u0629 \u062c\u062f\u064a\u062f\u0629","summary":"Careem's continued expansion into home services, grocery, and payments signals increasing super-app competition.","type":"mention","sector":"Technology","platform":"News","priority":"Medium","score":63,"mentions":44,"keywords":"Careem,super app,UAE tech,expansion","date_collected":"2026-02-23","source_url":"https://thenationalnews.com","raw_text":"Careem is quietly building out its super-app ambitions."},
  {"title":"Mention: ADGM accelerator cohort signals B2B fintech focus","arabic_title":"\u0645\u0633\u0631\u0651\u0639 ADGM \u064a\u0631\u0643\u0632 \u0639\u0644\u0649 \u062a\u0645\u0648\u064a\u0644 \u0627\u0644\u0634\u0631\u0643\u0627\u062a","summary":"ADGM accelerator heavily weighted toward B2B fintech, regtech, and embedded finance.","type":"mention","sector":"Fintech","platform":"LinkedIn","priority":"Low","score":58,"mentions":16,"keywords":"ADGM,accelerator,B2B fintech,Abu Dhabi","date_collected":"2026-02-20","source_url":"https://linkedin.com","raw_text":"8 startups, all B2B focused."},
  {"title":"Pet care services market growing rapidly in Dubai","arabic_title":"\u0633\u0648\u0642 \u062e\u062f\u0645\u0627\u062a \u0631\u0639\u0627\u064a\u0629 \u0627\u0644\u062d\u064a\u0648\u0627\u0646\u0627\u062a \u0627\u0644\u0623\u0644\u064a\u0641\u0629 \u064a\u0646\u0645\u0648 \u0628\u0633\u0631\u0639\u0629 \u0641\u064a \u062f\u0628\u064a","summary":"Strong UAE pet owner demand for premium grooming, vet telehealth, and pet sitting. Ownership rising post-pandemic.","type":"trending","sector":"Retail","platform":"Reddit","priority":"Medium","score":64,"mentions":33,"keywords":"pet care,Dubai pets,vet UAE,grooming","date_collected":"2026-02-19","source_url":"https://reddit.com/r/dubai","raw_text":"Dubai pet parents are spending crazy money on grooming."},
  {"title":"School transport safety concerns raised by parents","arabic_title":"\u0645\u062e\u0627\u0648\u0641 \u0623\u0648\u0644\u064a\u0627\u0621 \u0627\u0644\u0623\u0645\u0648\u0631 \u0628\u0634\u0623\u0646 \u0633\u0644\u0627\u0645\u0629 \u0627\u0644\u0645\u0648\u0627\u0635\u0644\u0627\u062a \u0627\u0644\u0645\u062f\u0631\u0633\u064a\u0629","summary":"Strong demand signal for a school transport management platform with GPS tracking and driver vetting.","type":"pain_point","sector":"Education","platform":"Facebook Groups","priority":"High","score":81,"mentions":67,"keywords":"school bus,transport safety,parent app,UAE schools","date_collected":"2026-02-22","source_url":"https://facebook.com/groups","raw_text":"I have no idea where my kid's school bus is. There's no tracking app."},
  {"title":"EV charging infrastructure gaps frustrate UAE early adopters","arabic_title":"\u062b\u063a\u0631\u0627\u062a \u0627\u0644\u0628\u0646\u064a\u0629 \u0627\u0644\u062a\u062d\u062a\u064a\u0629 \u0644\u0634\u062d\u0646 \u0627\u0644\u0633\u064a\u0627\u0631\u0627\u062a \u0627\u0644\u0643\u0647\u0631\u0628\u0627\u0626\u064a\u0629 \u062a\u064f\u062d\u0628\u0637 \u0645\u0628\u0643\u0631\u064a \u0627\u0644\u062a\u0628\u0646\u064a \u0641\u064a \u0627\u0644\u0625\u0645\u0627\u0631\u0627\u062a","summary":"Insufficient fast chargers outside major malls and unclear DEWA billing for EV charging. Clear infrastructure opportunity.","type":"pain_point","sector":"Technology","platform":"Reddit","priority":"Medium","score":73,"mentions":41,"keywords":"EV charging,electric vehicle UAE,DEWA,infrastructure","date_collected":"2026-02-21","source_url":"https://reddit.com/r/dubai","raw_text":"The EV charging infrastructure here is embarrassingly underdeveloped."}
]

def seed_data(conn):
    c = conn.cursor()
    platforms = list(set(s['platform'] for s in SEED_SIGNALS))
    for p in platforms:
        c.execute('INSERT OR IGNORE INTO platforms (name) VALUES (?)', (p,))
    sectors = list(set(s['sector'] for s in SEED_SIGNALS))
    for s in sectors:
        c.execute('INSERT OR IGNORE INTO sectors (name) VALUES (?)', (s,))
    for s in SEED_SIGNALS:
        c.execute('''INSERT INTO signals 
            (title, arabic_title, summary, type, sector, platform, priority, score, mentions, keywords, raw_text, source_url, date_collected)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (s['title'], s.get('arabic_title'), s['summary'], s['type'], s['sector'],
             s['platform'], s['priority'], s['score'], s.get('mentions',0),
             s.get('keywords',''), s.get('raw_text',''), s.get('source_url',''), s.get('date_collected','')))
    conn.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('last_seeded', ?)",(datetime.now().isoformat(),))
    conn.commit()

# ===================== HANDLERS =====================
def get_all_signals(conn, limit=200):
    c = conn.cursor()
    rows = c.execute('SELECT * FROM signals ORDER BY score DESC, id ASC LIMIT ?', (limit,)).fetchall()
    signals = []
    for row in rows:
        d = dict(row)
        d['keywords'] = [k.strip() for k in d['keywords'].split(',') if k.strip()] if d.get('keywords') else []
        signals.append(d)
    return signals

def get_by_sector(conn, sector):
    c = conn.cursor()
    rows = c.execute('SELECT * FROM signals WHERE sector=? ORDER BY score DESC', (sector,)).fetchall()
    signals = []
    for row in rows:
        d = dict(row)
        d['keywords'] = [k.strip() for k in d['keywords'].split(',') if k.strip()] if d.get('keywords') else []
        signals.append(d)
    return signals

def get_by_platform(conn, platform):
    c = conn.cursor()
    rows = c.execute('SELECT * FROM signals WHERE platform=? ORDER BY score DESC', (platform,)).fetchall()
    signals = []
    for row in rows:
        d = dict(row)
        d['keywords'] = [k.strip() for k in d['keywords'].split(',') if k.strip()] if d.get('keywords') else []
        signals.append(d)
    return signals

def search_signals(conn, query):
    c = conn.cursor()
    q = f'%{query}%'
    rows = c.execute('''SELECT * FROM signals WHERE 
        title LIKE ? OR summary LIKE ? OR keywords LIKE ? OR arabic_title LIKE ?
        ORDER BY score DESC''', (q, q, q, q)).fetchall()
    signals = []
    for row in rows:
        d = dict(row)
        d['keywords'] = [k.strip() for k in d['keywords'].split(',') if k.strip()] if d.get('keywords') else []
        signals.append(d)
    return signals

def get_stats(conn):
    c = conn.cursor()
    total = c.execute('SELECT COUNT(*) FROM signals').fetchone()[0]
    high = c.execute("SELECT COUNT(*) FROM signals WHERE priority='High'").fetchone()[0]
    sectors = c.execute('SELECT COUNT(DISTINCT sector) FROM signals').fetchone()[0]
    platforms = c.execute('SELECT COUNT(DISTINCT platform) FROM signals').fetchone()[0]
    by_type = {}
    for row in c.execute("SELECT type, COUNT(*) as cnt FROM signals GROUP BY type").fetchall():
        by_type[row['type']] = row['cnt']
    return {"total": total, "high_priority": high, "sectors": sectors, "platforms": platforms, "by_type": by_type}

# ===================== MAIN =====================
def main():
    print("Content-Type: application/json")
    print("Access-Control-Allow-Origin: *")
    print()
    
    try:
        init_db()
        form = cgi.FieldStorage()
        action = form.getvalue('action', 'all')
        conn = get_db()
        
        if action == 'all':
            signals = get_all_signals(conn)
            result = {"signals": signals, "count": len(signals), "timestamp": datetime.now().isoformat()}
        elif action == 'stats':
            result = get_stats(conn)
        elif action == 'sector':
            sector = form.getvalue('sector', '')
            signals = get_by_sector(conn, sector)
            result = {"signals": signals, "sector": sector, "count": len(signals)}
        elif action == 'platform':
            platform = form.getvalue('platform', '')
            signals = get_by_platform(conn, platform)
            result = {"signals": signals, "platform": platform, "count": len(signals)}
        elif action == 'search':
            query = form.getvalue('q', '')
            signals = search_signals(conn, query)
            result = {"signals": signals, "query": query, "count": len(signals)}
        else:
            result = {"error": "Unknown action", "valid_actions": ["all","stats","sector","platform","search"]}
        
        conn.close()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    except Exception as e:
        print(json.dumps({"error": str(e), "type": type(e).__name__}))

if __name__ == '__main__':
    main()
