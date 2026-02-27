// UAE Market Intelligence — Frontend
// Fetches data from API and renders the dashboard

const API_BASE = './cgi-bin/api.py';

let allSignals = [];
let activeFilters = { sector: 'all', type: 'all' };
let currentSearch = '';

// ===================== INIT =====================
document.addEventListener('DOMContentLoaded', async () => {
    await loadData();
    renderSectorFilters();
    applyFilters();
    renderSectorsTab();
    renderPlatformsTab();
    updateStats();
    startAutoRefresh();
});

// ===================== DATA =====================
async function loadData() {
    try {
        const res = await fetch(`${API_BASE}?action=all`);
        if (!res.ok) throw new Error('API error');
        const data = await res.json();
        allSignals = data.signals || [];
        document.getElementById('lastUpdated').textContent = `Updated ${formatRelative(new Date())}`;
    } catch (e) {
        // Fallback: use embedded seed data
        allSignals = SEED_DATA;
        document.getElementById('lastUpdated').textContent = 'Demo mode — seed data';
    }
}

async function refreshData() {
    const btn = document.querySelector('.refresh-btn');
    btn.style.opacity = '0.5';
    btn.style.pointerEvents = 'none';
    await loadData();
    applyFilters();
    renderSectorsTab();
    renderPlatformsTab();
    updateStats();
    setTimeout(() => {
        btn.style.opacity = '1';
        btn.style.pointerEvents = 'auto';
    }, 800);
}

function startAutoRefresh() {
    setInterval(refreshData, 5 * 60 * 1000); // every 5 minutes
}

// ===================== FILTERS =====================
function setFilter(dimension, value, el) {
    activeFilters[dimension] = value;
    const group = dimension === 'sector' ? document.getElementById('sectorFilters') : document.getElementById('typeFilters');
    group.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
    el.classList.add('active');
    applyFilters();
}

function applyFilters() {
    currentSearch = document.getElementById('searchInput').value.toLowerCase();
    let filtered = allSignals;
    if (activeFilters.sector !== 'all') {
        filtered = filtered.filter(s => s.sector === activeFilters.sector);
    }
    if (activeFilters.type !== 'all') {
        filtered = filtered.filter(s => s.type === activeFilters.type);
    }
    if (currentSearch) {
        filtered = filtered.filter(s =>
            s.title.toLowerCase().includes(currentSearch) ||
            s.summary.toLowerCase().includes(currentSearch) ||
            (s.keywords || []).some(k => k.toLowerCase().includes(currentSearch))
        );
    }
    renderFeed(filtered);
}

// ===================== RENDER: SECTOR FILTERS =====================
function renderSectorFilters() {
    const sectors = [...new Set(allSignals.map(s => s.sector))].sort();
    const container = document.getElementById('sectorFilters');
    container.innerHTML = `<button class="filter-chip active" data-filter="all" onclick="setFilter('sector', 'all', this)">All Sectors</button>`;
    sectors.forEach(sector => {
        const btn = document.createElement('button');
        btn.className = 'filter-chip';
        btn.dataset.filter = sector;
        btn.textContent = sector;
        btn.onclick = function() { setFilter('sector', sector, this); };
        container.appendChild(btn);
    });
}

// ===================== RENDER: FEED =====================
function renderFeed(signals) {
    const grid = document.getElementById('feedGrid');
    if (!signals.length) {
        grid.innerHTML = `<div style="color:var(--text-muted);font-size:14px;padding:40px 0;">No signals match the current filters.</div>`;
        return;
    }
    grid.innerHTML = signals.map(s => cardHTML(s)).join('');
}

function cardHTML(s) {
    return `
    <div class="signal-card priority-${s.priority?.toLowerCase()}" onclick="openModal(${s.id})">
        <div class="card-header">
            <div class="card-meta">
                <span class="card-type ${s.type}">${formatType(s.type)}</span>
                <span class="card-sector">${s.sector}</span>
            </div>
            <span class="priority-badge ${s.priority?.toLowerCase()}">${s.priority}</span>
        </div>
        <div class="card-title">${escHtml(s.title)}</div>
        <div class="card-summary">${escHtml(s.summary)}</div>
        <div class="card-footer">
            <div class="card-platform">
                <div class="platform-dot"></div>
                ${escHtml(s.platform)}
            </div>
            <div class="card-stats">
                ${s.mentions ? `<span class="card-stat">${s.mentions} mentions</span>` : ''}
            </div>
            <span class="card-score">Score: ${s.score ?? '—'}</span>
        </div>
        ${s.arabic_title ? `<div class="card-arabic">${escHtml(s.arabic_title)}</div>` : ''}
    </div>`;
}

// ===================== RENDER: SECTORS TAB =====================
function renderSectorsTab() {
    const sectors = {};
    allSignals.forEach(s => {
        if (!sectors[s.sector]) sectors[s.sector] = [];
        sectors[s.sector].push(s);
    });
    const grid = document.getElementById('sectorsGrid');
    grid.innerHTML = Object.entries(sectors).sort((a,b) => b[1].length - a[1].length).map(([name, signals]) => `
        <div class="sector-block">
            <div class="sector-block-header">
                <div class="sector-block-name">${name}</div>
                <div class="sector-block-count">${signals.length} signals</div>
            </div>
            <div class="sector-signal-list">
                ${signals.slice(0,5).map(s => `
                    <div class="sector-signal-item" onclick="openModal(${s.id})">
                        <div class="sector-signal-title">${escHtml(s.title)}</div>
                        <div class="sector-signal-meta">
                            <span class="card-type ${s.type}" style="font-size:10px;">${formatType(s.type)}</span>
                            <span class="priority-badge ${s.priority?.toLowerCase()}" style="font-size:10px;">${s.priority}</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `).join('');
}

// ===================== RENDER: PLATFORMS TAB =====================
function renderPlatformsTab() {
    const platforms = {};
    allSignals.forEach(s => {
        if (!platforms[s.platform]) platforms[s.platform] = [];
        platforms[s.platform].push(s);
    });
    const max = Math.max(...Object.values(platforms).map(v => v.length));
    const grid = document.getElementById('platformsGrid');
    grid.innerHTML = Object.entries(platforms).sort((a,b) => b[1].length - a[1].length).map(([name, signals]) => {
        const types = [...new Set(signals.map(s => s.type))];
        const pct = Math.round((signals.length / max) * 100);
        return `
        <div class="platform-block">
            <div class="platform-block-header">
                <div class="platform-block-name">${name}</div>
            </div>
            <div class="platform-block-count">${signals.length}</div>
            <div class="platform-block-label">signals tracked</div>
            <div class="platform-bar"><div class="platform-bar-fill" style="width:${pct}%"></div></div>
            <div class="platform-types">${types.map(t => `<span class="platform-type-tag">${formatType(t)}</span>`).join('')}</div>
        </div>`;
    }).join('');
}

// ===================== STATS =====================
function updateStats() {
    animateCount('statTotal', allSignals.length);
    animateCount('statHigh', allSignals.filter(s => s.priority === 'High').length);
    animateCount('statSectors', new Set(allSignals.map(s => s.sector)).size);
    animateCount('statPlatforms', new Set(allSignals.map(s => s.platform)).size);
}

function animateCount(id, target) {
    const el = document.getElementById(id);
    let current = 0;
    const step = Math.ceil(target / 30);
    const interval = setInterval(() => {
        current = Math.min(current + step, target);
        el.textContent = current;
        if (current >= target) clearInterval(interval);
    }, 40);
}

// ===================== MODAL =====================
function openModal(id) {
    const s = allSignals.find(x => x.id === id);
    if (!s) return;
    const typeColors = { trending: 'var(--gold)', pain_point: 'var(--red)', opportunity: 'var(--green)', mention: 'var(--blue)' };
    const typeBg = { trending: 'var(--gold-dim)', pain_point: 'var(--red-dim)', opportunity: 'var(--green-dim)', mention: 'var(--blue-dim)' };
    document.getElementById('modalBody').innerHTML = `
        <div class="modal-type-badge" style="background:${typeBg[s.type]};color:${typeColors[s.type]};">${formatType(s.type)}</div>
        <div class="modal-title">${escHtml(s.title)}</div>
        <div class="modal-summary">${escHtml(s.summary)}</div>
        <div class="modal-detail-grid">
            <div class="modal-detail-item">
                <div class="modal-detail-label">Sector</div>
                <div class="modal-detail-value">${escHtml(s.sector)}</div>
            </div>
            <div class="modal-detail-item">
                <div class="modal-detail-label">Platform</div>
                <div class="modal-detail-value">${escHtml(s.platform)}</div>
            </div>
            <div class="modal-detail-item">
                <div class="modal-detail-label">Priority</div>
                <div class="modal-detail-value">${escHtml(s.priority)}</div>
            </div>
            <div class="modal-detail-item">
                <div class="modal-detail-label">Score</div>
                <div class="modal-detail-value">${s.score ?? '—'}</div>
            </div>
            ${s.mentions ? `
            <div class="modal-detail-item">
                <div class="modal-detail-label">Mentions</div>
                <div class="modal-detail-value">${s.mentions}</div>
            </div>` : ''}
            <div class="modal-detail-item">
                <div class="modal-detail-label">Date Collected</div>
                <div class="modal-detail-value">${s.date_collected ?? '—'}</div>
            </div>
        </div>
        ${s.keywords?.length ? `
        <div class="modal-section-title">Keywords</div>
        <div class="modal-keywords">${s.keywords.map(k => `<span class="modal-keyword">${escHtml(k)}</span>`).join('')}</div>
        ` : ''}
        ${s.raw_text ? `
        <div class="modal-section-title">Original Content</div>
        <div class="modal-raw-text">${escHtml(s.raw_text)}</div>
        ` : ''}
        ${s.arabic_title ? `
        <div class="modal-section-title">Arabic</div>
        <div class="modal-arabic-text">${escHtml(s.arabic_title)}</div>
        ` : ''}
        ${s.source_url ? `<a href="${s.source_url}" target="_blank" rel="noopener" class="modal-source-link">View Original Source ↗</a>` : ''}
    `;
    document.getElementById('modalOverlay').classList.add('open');
}

function closeModal() {
    document.getElementById('modalOverlay').classList.remove('open');
}

document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeModal();
});

// ===================== UTILS =====================
function escHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function formatType(t) {
    return { trending: 'Trending', pain_point: 'Pain Point', opportunity: 'Opportunity', mention: 'Mention' }[t] || t;
}

function formatRelative(date) {
    return 'just now';
}

// ===================== SEED DATA (fallback) =====================
const SEED_DATA = [
  {"id":1,"title":"Surge in demand for halal certified delivery platforms","arabic_title":"زيادة الطلب على منصات التوصيل الحلال","summary":"Multiple users across UAE subreddits and Facebook Groups report difficulty finding reliable halal-certified food delivery options beyond major apps. Small restaurant owners highlight gaps in last-mile logistics for halal-only kitchens.","type":"trending","sector":"Food & Beverage","platform":"Reddit","priority":"High","score":91,"mentions":87,"keywords":["halal delivery","food logistics","UAE dining","last-mile"],"date_collected":"2026-02-20","source_url":"https://reddit.com/r/dubai","raw_text":"Honestly the halal delivery scene in Dubai is still super fragmented. I've been trying to find a dedicated platform for months..."},
  {"id":2,"title":"SME owners frustrated with UAE bank onboarding delays","arabic_title":"أصحاب الشركات الصغيرة يعانون من تأخيرات فتح الحسابات البنكية","summary":"A recurring pain point in multiple LinkedIn posts and Reddit threads: small business owners spending 4-8 weeks waiting for corporate bank account approvals. Several fintech founders suggest a digital-first SME banking alternative is overdue.","type":"pain_point","sector":"Fintech","platform":"LinkedIn","priority":"High","score":88,"mentions":62,"keywords":["SME banking","account opening","fintech UAE","digital banking"],"date_collected":"2026-02-21","source_url":"https://linkedin.com","raw_text":"It took us 6 weeks to open a corporate account. In 2026. For a registered UAE company. Unacceptable."},
  {"id":3,"title":"Arabic-language mental health content severely underserved","arabic_title":"محتوى الصحة النفسية باللغة العربية شحيح","summary":"Growing conversation on X and Arabic forums about the lack of quality mental health resources in Arabic. Users report turning to English-language apps due to absence of culturally relevant content, despite strong demand.","type":"opportunity","sector":"Healthcare","platform":"X / Twitter","priority":"High","score":85,"mentions":74,"keywords":["mental health","Arabic content","wellbeing UAE","telehealth"],"date_collected":"2026-02-19","source_url":"https://x.com","raw_text":"كل تطبيقات الصحة النفسية بالإنجليزي. محتاجين شي بالعربي يفهم ثقافتنا"},
  {"id":4,"title":"Real estate investors seeking off-plan transparency tools","arabic_title":"المستثمرون العقاريون يبحثون عن أدوات شفافية للمشاريع على الخريطة","summary":"Frequent complaints on Property Finder forums and Reddit about lack of real-time updates on off-plan project milestones. Investors want dashboards tracking construction progress, escrow releases, and developer reputation.","type":"pain_point","sector":"Real Estate","platform":"Forums","priority":"High","score":83,"mentions":55,"keywords":["off-plan","real estate UAE","investor tools","transparency"],"date_collected":"2026-02-22","source_url":"https://propertyfinder.ae","raw_text":"Bought off-plan 2 years ago, zero communication from developer on construction updates. Need a platform that tracks this."},
  {"id":5,"title":"Cross-border remittance fees still too high say expats","arabic_title":"رسوم التحويل المالي لا تزال مرتفعة بحسب المغتربين","summary":"UAE expat communities on Reddit and Filipino/Indian diaspora Facebook Groups express ongoing frustration with remittance fees averaging 2-4%. Despite competition, last-mile delivery fees and exchange rate opacity remain issues.","type":"pain_point","sector":"Fintech","platform":"Facebook Groups","priority":"Medium","score":77,"mentions":91,"keywords":["remittance","expat UAE","money transfer","fees"],"date_collected":"2026-02-18","source_url":"https://facebook.com/groups","raw_text":"Still paying 3.5% to send money home. When will UAE remittance get truly competitive?"},
  {"id":6,"title":"D2C grocery brands growing in Abu Dhabi market","arabic_title":"نمو العلامات التجارية المباشرة للمستهلك في سوق أبوظبي","summary":"Multiple mentions on LinkedIn and local news of UAE-based D2C grocery startups gaining traction. Consumers cite freshness guarantees and subscription models as key differentiators over hypermarkets.","type":"trending","sector":"Food & Beverage","platform":"LinkedIn","priority":"Medium","score":74,"mentions":38,"keywords":["D2C grocery","Abu Dhabi","subscription","fresh food"],"date_collected":"2026-02-23","source_url":"https://linkedin.com","raw_text":"Our D2C organic vegetable box just hit 2,000 subscribers in Abu Dhabi. The appetite for premium fresh food is real."},
  {"id":7,"title":"EdTech platforms lacking Arabic STEM content for K-12","arabic_title":"منصات التعليم الإلكتروني تفتقر إلى محتوى STEM بالعربية للمراحل الدراسية","summary":"Parents in UAE parenting forums and WhatsApp groups highlight the lack of gamified Arabic STEM content for school-age children. Most quality platforms are English-only, leaving a clear market gap for Arabic-first ed-tech.","type":"opportunity","sector":"Education","platform":"Forums","priority":"High","score":82,"mentions":49,"keywords":["edtech","Arabic STEM","K-12","gamified learning"],"date_collected":"2026-02-20","source_url":"https://forums.ae","raw_text":"My kids are stuck using Khan Academy in English. I want something engaging, Arabic, and curriculum-aligned for UAE schools."},
  {"id":8,"title":"Healthcare appointment booking fragmented across Emirates","arabic_title":"حجز المواعيد الصحية مجزأ عبر الإمارات","summary":"Google Reviews and Reddit threads highlight inconsistent digital booking experiences across Abu Dhabi and Dubai hospitals. Users want a single unified platform that aggregates availability across public and private providers.","type":"pain_point","sector":"Healthcare","platform":"Google Reviews","priority":"Medium","score":71,"mentions":43,"keywords":["healthcare booking","UAE hospitals","unified platform","appointment"],"date_collected":"2026-02-21","source_url":"https://maps.google.com","raw_text":"Had to call 4 different numbers to book a specialist. In 2026 this should be one app."},
  {"id":9,"title":"Sustainable packaging demand rising among UAE retailers","arabic_title":"ارتفاع الطلب على التغليف المستدام بين تجار التجزئة في الإمارات","summary":"Retail industry LinkedIn posts and news coverage show UAE brands increasingly committing to sustainable packaging amid regulatory pressure and consumer demand. Suppliers able to offer cost-competitive eco alternatives are in demand.","type":"trending","sector":"Retail","platform":"News","priority":"Medium","score":68,"mentions":29,"keywords":["sustainable packaging","retail UAE","eco","regulation"],"date_collected":"2026-02-22","source_url":"https://thenationalnews.com","raw_text":"UAE retailers are fast-tracking sustainable packaging transitions ahead of new plastic reduction targets."},
  {"id":10,"title":"Tourism operators want AI-powered multilingual tour guides","arabic_title":"مشغلو السياحة يريدون مرشدين سياحيين متعددي اللغات بالذكاء الاصطناعي","summary":"Travel forums and LinkedIn show UAE tour operators expressing interest in AI audio guide technology that supports Arabic, English, Chinese, and Russian. High demand from MICE and luxury tourism segments.","type":"opportunity","sector":"Tourism","platform":"LinkedIn","priority":"Medium","score":72,"mentions":22,"keywords":["AI tour guide","multilingual","tourism UAE","MICE"],"date_collected":"2026-02-19","source_url":"https://linkedin.com","raw_text":"We need AI audio guides that switch seamlessly between Arabic and Mandarin for our Chinese visitor groups. Nothing good exists yet."},
  {"id":11,"title":"Last-mile logistics for e-commerce still unreliable in outer Abu Dhabi","arabic_title":"الخدمات اللوجستية للتجارة الإلكترونية غير موثوقة في مناطق أبوظبي الخارجية","summary":"Shoppers in Al Ain, Madinat Zayed, and Liwa express frustration on social media about inconsistent delivery times and high fees. Market opportunity for hyperlocal logistics player serving outer Emirates.","type":"pain_point","sector":"Logistics","platform":"X / Twitter","priority":"High","score":80,"mentions":58,"keywords":["last-mile","Abu Dhabi delivery","Al Ain","logistics gap"],"date_collected":"2026-02-23","source_url":"https://x.com","raw_text":"Ordered from Noon 8 days ago. Still waiting. Al Ain delivery is a disaster compared to Dubai."},
  {"id":12,"title":"Co-working space demand spiking in Sharjah and Northern Emirates","arabic_title":"ارتفاع الطلب على مساحات العمل المشترك في الشارقة والإمارات الشمالية","summary":"LinkedIn posts from freelancers and startup founders highlight a shortage of quality co-working spaces outside Dubai and Abu Dhabi. Sharjah and Ras Al Khaimah showing strong unmet demand signals.","type":"opportunity","sector":"Real Estate","platform":"LinkedIn","priority":"Medium","score":70,"mentions":31,"keywords":["co-working","Sharjah","RAK","startup space"],"date_collected":"2026-02-20","source_url":"https://linkedin.com","raw_text":"Sharjah freelancers are forced to commute to Dubai for decent workspace. Someone needs to build WeWork for the Northern Emirates."},
  {"id":13,"title":"Digital wills and estate planning for expats an untapped niche","arabic_title":"الوصايا الرقمية وتخطيط التركات للمغتربين فرصة غير مستغلة","summary":"Legal advice threads on Reddit and expat forums frequently surface questions about UAE will registration, inheritance law for non-Muslims, and digital estate planning. Very few tech products serve this need.","type":"opportunity","sector":"Fintech","platform":"Reddit","priority":"Medium","score":75,"mentions":37,"keywords":["digital will","estate planning","expat UAE","legaltech"],"date_collected":"2026-02-18","source_url":"https://reddit.com/r/expats","raw_text":"Just realised I have no registered will in the UAE and no idea how my assets would be handled if something happened to me."},
  {"id":14,"title":"Restaurant owners demand better POS integrations with delivery apps","arabic_title":"أصحاب المطاعم يطالبون بتكامل أفضل بين نقاط البيع وتطبيقات التوصيل","summary":"F&B operators across UAE restaurant Facebook groups cite double-entry bookkeeping headaches from managing Talabat, Careem Food, and in-house POS separately. Demand for unified middleware is high.","type":"pain_point","sector":"Food & Beverage","platform":"Facebook Groups","priority":"Medium","score":69,"mentions":45,"keywords":["POS integration","Talabat","restaurant tech","UAE F&B"],"date_collected":"2026-02-22","source_url":"https://facebook.com/groups","raw_text":"Managing 3 delivery platforms + our POS is a nightmare. We need one system that syncs everything."},
  {"id":15,"title":"Corporate wellness programs underutilized in UAE SMEs","arabic_title":"برامج رفاهية الموظفين غير مستغلة في الشركات الصغيرة والمتوسطة بالإمارات","summary":"HR professionals on LinkedIn highlight that most UAE corporate wellness solutions are designed for large enterprises. SMEs lack affordable, scalable wellness benefit platforms tailored to their employee demographics.","type":"opportunity","sector":"Healthcare","platform":"LinkedIn","priority":"Low","score":61,"mentions":18,"keywords":["corporate wellness","SME UAE","employee benefits","HR tech"],"date_collected":"2026-02-21","source_url":"https://linkedin.com","raw_text":"Big wellness platforms want annual contracts worth AED 200K+. We're a 30-person company. Where's our option?"},
  {"id":16,"title":"Rising interest in UAE-based cloud kitchen concepts","arabic_title":"اهتمام متزايد بمفهوم المطابخ السحابية في الإمارات","summary":"Entrepreneur communities on Reddit and Twitter increasingly discussing cloud kitchen models as lower-risk F&B entry points. Demand for plug-and-play cloud kitchen infrastructure with built-in delivery partnerships is emerging.","type":"trending","sector":"Food & Beverage","platform":"Reddit","priority":"Medium","score":66,"mentions":27,"keywords":["cloud kitchen","ghost kitchen","UAE F&B","food startup"],"date_collected":"2026-02-19","source_url":"https://reddit.com/r/dubai","raw_text":"Cloud kitchens in Dubai are filling up fast. Infrastructure providers are killing it right now."},
  {"id":17,"title":"Arabic language interfaces still lacking in SaaS tools","arabic_title":"واجهات اللغة العربية لا تزال تفتقر إليها أدوات SaaS","summary":"Tech professionals in Arab countries, including UAE, cite frustration on LinkedIn and X at the poor quality of Arabic UI/UX in most business SaaS products. RTL support remains inconsistent even in major platforms.","type":"pain_point","sector":"Technology","platform":"X / Twitter","priority":"High","score":79,"mentions":53,"keywords":["Arabic UI","RTL","SaaS localization","Arabic tech"],"date_collected":"2026-02-20","source_url":"https://x.com","raw_text":"Why in 2026 do enterprise SaaS products still ship broken Arabic RTL support? It's not a small market."},
  {"id":18,"title":"Demand for Islamic finance investment apps among millennials","arabic_title":"الطلب على تطبيقات الاستثمار الإسلامية بين جيل الألفية","summary":"UAE millennials on Reddit and Islamic finance forums express desire for a Robinhood-style investment app that is fully Shariah-compliant and transparent about screening methodology. Existing options seen as opaque or complex.","type":"opportunity","sector":"Fintech","platform":"Reddit","priority":"High","score":84,"mentions":61,"keywords":["Islamic finance","halal investing","millennial UAE","Shariah"],"date_collected":"2026-02-23","source_url":"https://reddit.com/r/IslamicFinance","raw_text":"I want a simple, clean investing app that's halal. Every existing option is either complicated or not transparent about what they screen."},
  {"id":19,"title":"Tourism recovery driving demand for Arabic-first travel content creators","arabic_title":"تعافي السياحة يدفع الطلب نحو منشئي المحتوى السياحي باللغة العربية","summary":"UAE tourism boards and hospitality brands flagging a gap in Arabic-language travel influencer content on TikTok and YouTube. Most major UAE travel content is English-first, missing GCC domestic tourism audience.","type":"opportunity","sector":"Tourism","platform":"LinkedIn","priority":"Medium","score":67,"mentions":24,"keywords":["Arabic travel content","UAE tourism","influencer","GCC"],"date_collected":"2026-02-22","source_url":"https://linkedin.com","raw_text":"We're investing in Arabic content creators for UAE tourism campaigns. The GCC domestic traveller is underserved in their own language."},
  {"id":20,"title":"Warehouse automation interest spiking among UAE 3PLs","arabic_title":"ارتفاع الاهتمام بأتمتة المستودعات بين شركات الخدمات اللوجستية في الإمارات","summary":"Logistics sector LinkedIn posts and trade news show UAE third-party logistics providers exploring robotics and WMS upgrades. Driver for interest: labor cost pressures and e-commerce volume growth.","type":"trending","sector":"Logistics","platform":"News","priority":"Medium","score":65,"mentions":19,"keywords":["warehouse automation","robotics","3PL UAE","WMS"],"date_collected":"2026-02-21","source_url":"https://arabianbusiness.com","raw_text":"UAE logistics firms are fast-tracking warehouse automation investments as e-commerce volumes continue to surge."},
  {"id":21,"title":"Mention: Careem expanding into new service verticals","arabic_title":"كريم تتوسع في قطاعات خدمية جديدة","summary":"Multiple news sources and X posts note Careem's continued expansion into home services, grocery, and payments. Signals increasing super-app competition for vertical-specific startups in UAE.","type":"mention","sector":"Technology","platform":"News","priority":"Medium","score":63,"mentions":44,"keywords":["Careem","super app","UAE tech","expansion"],"date_collected":"2026-02-23","source_url":"https://thenationalnews.com","raw_text":"Careem is quietly building out its super-app ambitions with new verticals targeting UAE households."},
  {"id":22,"title":"Mention: ADGM accelerator cohort signals B2B fintech focus","arabic_title":"مسرّع ADGM يركز على تمويل الشركات","summary":"ADGM's latest accelerator cohort heavily weighted toward B2B fintech, regtech, and embedded finance. Signals Abu Dhabi institutional appetite for infrastructure-layer financial services startups.","type":"mention","sector":"Fintech","platform":"LinkedIn","priority":"Low","score":58,"mentions":16,"keywords":["ADGM","accelerator","B2B fintech","Abu Dhabi"],"date_collected":"2026-02-20","source_url":"https://linkedin.com","raw_text":"Excited to announce the new ADGM FinTech accelerator cohort — 8 startups, all B2B focused."},
  {"id":23,"title":"Pet care services market growing rapidly in Dubai","arabic_title":"سوق خدمات رعاية الحيوانات الأليفة ينمو بسرعة في دبي","summary":"Reddit and Instagram comments show strong UAE pet owner demand for premium grooming, vet telehealth, and pet sitting services. Pet ownership rising post-pandemic among expats and nationals alike.","type":"trending","sector":"Retail","platform":"Reddit","priority":"Medium","score":64,"mentions":33,"keywords":["pet care","Dubai pets","vet UAE","grooming"],"date_collected":"2026-02-19","source_url":"https://reddit.com/r/dubai","raw_text":"Dubai pet parents are spending crazy money on grooming. The market for premium pet services is exploding."},
  {"id":24,"title":"School transport safety concerns raised by parents","arabic_title":"مخاوف أولياء الأمور بشأن سلامة المواصلات المدرسية","summary":"Parenting Facebook Groups and WhatsApp communities flag concerns about UAE school bus tracking, driver vetting, and real-time GPS visibility. Strong demand signal for a school transport management platform.","type":"pain_point","sector":"Education","platform":"Facebook Groups","priority":"High","score":81,"mentions":67,"keywords":["school bus","transport safety","parent app","UAE schools"],"date_collected":"2026-02-22","source_url":"https://facebook.com/groups","raw_text":"I have no idea where my kid's school bus is. There's no tracking app. This is 2026 — why?"},
  {"id":25,"title":"EV charging infrastructure gaps frustrate UAE early adopters","arabic_title":"ثغرات البنية التحتية لشحن السيارات الكهربائية تُحبط مبكري التبني في الإمارات","summary":"EV owners on Reddit and X complain about insufficient fast chargers outside major malls, lack of home charging support in apartments, and unclear DEWA billing for EV charging. Clear infrastructure opportunity.","type":"pain_point","sector":"Technology","platform":"Reddit","priority":"Medium","score":73,"mentions":41,"keywords":["EV charging","electric vehicle UAE","DEWA","infrastructure"],"date_collected":"2026-02-21","source_url":"https://reddit.com/r/dubai","raw_text":"Been waiting 45 minutes for a charger at Dubai Mall. The EV charging infrastructure here is embarrassingly underdeveloped."}];
