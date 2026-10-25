let allData = null;
let currentPeriod = '6m';
let currentFilters = {
    search: '',
    nations: new Set(),
    classType: 'all',
    level: 'all',
    category: 'all'
};
let currentSort = { field: 'win_rate', direction: 'desc' };

const DATA_URL = 'https://raw.githubusercontent.com/levobro228-eng/mt-stats/main/data/tanks.json';

const CATEGORY_LABELS = {
    regular: 'Прокачиваемые',
    premium: 'Премиум',
    collector: 'Коллекционные'
};

const NATION_TO_COUNTRY = {
    'ussr': 'ru',
    'russia': 'ru',
    'germany': 'de',
    'usa': 'us',
    'china': 'cn',
    'france': 'fr',
    'uk': 'gb',
    'britain': 'gb',
    'japan': 'jp',
    'czech': 'cz',
    'czechoslovakia': 'cz',
    'sweden': 'se',
    'poland': 'pl',
    'italy': 'it'
};

const NATION_NAMES = {
    'ussr': 'СССР',
    'russia': 'Россия',
    'germany': 'Германия',
    'usa': 'США',
    'china': 'Китай',
    'france': 'Франция',
    'uk': 'Великобритания',
    'britain': 'Великобритания',
    'japan': 'Япония',
    'czech': 'Чехия',
    'czechoslovakia': 'Чехословакия',
    'sweden': 'Швеция',
    'poland': 'Польша',
    'italy': 'Италия'
};

// Простой SVG флаг СССР (красный с жёлтой звездой)
const USSR_FLAG_SVG = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 90 60'><rect width='90' height='60' fill='%23CC0000'/><polygon points='15,10 18,20 28,20 20,26 23,36 15,30 7,36 10,26 2,20 12,20' fill='%23FFCC00'/></svg>";

// SVG флаг России (бело-сине-красный)
const RUSSIA_FLAG_SVG = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 90 60'><rect width='90' height='20' fill='white'/><rect y='20' width='90' height='20' fill='%230039A6'/><rect y='40' width='90' height='20' fill='%23D52B1E'/></svg>";

function getFlagUrl(nation) {
    if (nation === 'ussr') return USSR_FLAG_SVG;
    if (nation === 'russia') return RUSSIA_FLAG_SVG;
    const code = NATION_TO_COUNTRY[nation] || 'xx';
    return `https://flagcdn.com/w40/${code}.png`;
}

function getNationName(nation) {
    return NATION_NAMES[nation] || nation;
}

async function loadData() {
    try {
        const timestamp = new Date().getTime();
        const response = await fetch(`${DATA_URL}?t=${timestamp}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const text = await response.text();
        if (text.trim() === '{}') throw new Error('Файл данных пуст');
        
        allData = JSON.parse(text);
        document.getElementById('update-date').textContent = allData.updated || '...';
        
        initNationFilters();
        updateSearchHint();
        renderTable();
    } catch (error) {
        console.error('Ошибка:', error);
        document.getElementById('tanks-body').innerHTML = 
            `<tr><td colspan="7" class="loading">Ошибка: ${error.message}</td></tr>`;
    }
}

function initNationFilters() {
    if (!allData || !allData.periods) return;
    const nations = new Set();
    Object.values(allData.periods).forEach(period => {
        if (Array.isArray(period)) {
            period.forEach(tank => {
                if (tank.nation) nations.add(tank.nation);
            });
        }
    });
    
    const nationOrder = ['ussr', 'germany', 'usa', 'china', 'france', 'uk', 'japan', 'czech', 'sweden', 'poland', 'italy'];
    const sorted = [...nations].sort((a, b) => {
        const ia = nationOrder.indexOf(a), ib = nationOrder.indexOf(b);
        if (ia === -1 && ib === -1) return a.localeCompare(b);
        if (ia === -1) return 1;
        if (ib === -1) return -1;
        return ia - ib;
    });
    
    const container = document.getElementById('nation-filters');
    container.innerHTML = '';
    sorted.forEach(nation => {
        const btn = document.createElement('button');
        btn.className = 'nation-btn active';
        btn.dataset.nation = nation;
        btn.title = getNationName(nation);
        btn.innerHTML = `<img src="${getFlagUrl(nation)}" alt="${getNationName(nation)}">`;
        btn.addEventListener('click', () => toggleNation(nation, btn));
        container.appendChild(btn);
        currentFilters.nations.add(nation);
    });
}

function toggleNation(nation, btn) {
    if (currentFilters.nations.has(nation)) {
        currentFilters.nations.delete(nation);
        btn.classList.remove('active');
    } else {
        currentFilters.nations.add(nation);
        btn.classList.add('active');
    }
    renderTable();
}

function updateSearchHint() {
    if (!allData || !allData.periods) return;
    const tanks = allData.periods[currentPeriod] || [];
    document.getElementById('search-hint').textContent = `Поиск по ${tanks.length} танкам`;
}

function getFilteredTanks() {
    if (!allData || !allData.periods) return [];
    let tanks = [...(allData.periods[currentPeriod] || [])];
    
    if (currentFilters.search) {
        const s = currentFilters.search.toLowerCase();
        tanks = tanks.filter(t => t.name.toLowerCase().includes(s));
    }
    if (currentFilters.nations.size > 0) {
        tanks = tanks.filter(t => currentFilters.nations.has(t.nation));
    }
    if (currentFilters.classType !== 'all') {
        tanks = tanks.filter(t => t.type === currentFilters.classType);
    }
    if (currentFilters.level !== 'all') {
        tanks = tanks.filter(t => t.level === parseInt(currentFilters.level));
    }
    if (currentFilters.category !== 'all') {
        tanks = tanks.filter(t => t.category === currentFilters.category);
    }
    
    const { field, direction } = currentSort;
    tanks.sort((a, b) => {
        let va = a[field], vb = b[field];
        if (typeof va === 'string') {
            va = va.toLowerCase(); vb = vb.toLowerCase();
            return direction === 'asc' ? va.localeCompare(vb) : vb.localeCompare(va);
        }
        return direction === 'asc' ? va - vb : vb - va;
    });
    
    return tanks;
}

function getWinrateColor(wr) {
    if (wr >= 55) return '#d32f2f';
    if (wr >= 52) return '#f57c00';
    if (wr >= 50) return '#f9a825';
    if (wr >= 48) return '#1976d2';
    return '#388e3c';
}

function renderTable() {
    const tanks = getFilteredTanks();
    const tbody = document.getElementById('tanks-body');
    
    document.getElementById('stat-count').textContent = `${tanks.length} танков`;
    const avg = tanks.length ? (tanks.reduce((s, t) => s + t.win_rate, 0) / tanks.length).toFixed(2) : 0;
    document.getElementById('stat-avg').textContent = `Средний винрейт: ${avg}%`;
    const totalB = tanks.reduce((s, t) => s + t.battles, 0);
    document.getElementById('stat-battles').textContent = `Всего боёв: ${totalB.toLocaleString('ru-RU')}`;
    
    if (tanks.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="loading">Танки не найдены</td></tr>';
        return;
    }
    
    tbody.innerHTML = tanks.map(t => {
        const nameClass = t.category === 'premium' ? 'premium-name' : t.category === 'collector' ? 'collector-name' : '';
        const statusLabel = CATEGORY_LABELS[t.category] || t.category;
        const barWidth = Math.min(100, Math.max(0, (t.win_rate - 40) * 5));
        const color = getWinrateColor(t.win_rate);
        
        return `
        <tr>
            <td class="flag-cell"><img src="${getFlagUrl(t.nation)}" alt="${getNationName(t.nation)}" title="${getNationName(t.nation)}"></td>
            <td>${romanize(t.level)}</td>
            <td>
                <div class="tank-name-cell">
                    ${t.icon ? `<img class="tank-icon" src="${t.icon}" alt="" onerror="this.style.display='none'">` : ''}
                    <span class="tank-name ${nameClass}">${t.name}</span>
                </div>
            </td>
            <td><span class="status-badge status-${t.category}">${statusLabel}</span></td>
            <td>${t.battles.toLocaleString('ru-RU')}</td>
            <td>${t.wins.toLocaleString('ru-RU')}</td>
            <td>
                <div class="winrate-cell">
                    <span class="winrate-value" style="color:${color}">${t.win_rate}%</span>
                    <div class="winrate-bar-bg">
                        <div class="winrate-bar-fill" style="width:${barWidth}%;background:${color}"></div>
                    </div>
                </div>
            </td>
        </tr>`;
    }).join('');
}

function romanize(num) {
    const map = {1:'I',2:'II',3:'III',4:'IV',5:'V',6:'VI',7:'VII',8:'VIII',9:'IX',10:'X',11:'XI'};
    return map[num] || num;
}

document.getElementById('search-input').addEventListener('input', (e) => {
    currentFilters.search = e.target.value;
    renderTable();
});

document.getElementById('btn-reset').addEventListener('click', () => {
    currentFilters = { 
        search: '', 
        nations: new Set([...document.querySelectorAll('.nation-btn')].map(b => b.dataset.nation)), 
        classType: 'all', 
        level: 'all', 
        category: 'all' 
    };
    document.getElementById('search-input').value = '';
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.filter-btn[data-class="all"], .filter-btn[data-level="all"], .filter-btn[data-category="all"]').forEach(b => b.classList.add('active'));
    document.querySelectorAll('.nation-btn').forEach(b => b.classList.add('active'));
    renderTable();
});

document.querySelectorAll('.filter-btn[data-class]').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.filter-btn[data-class]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentFilters.classType = btn.dataset.class;
        renderTable();
    });
});

document.querySelectorAll('.filter-btn[data-level]').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.filter-btn[data-level]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentFilters.level = btn.dataset.level;
        renderTable();
    });
});

document.querySelectorAll('.filter-btn[data-category]').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.filter-btn[data-category]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentFilters.category = btn.dataset.category;
        renderTable();
    });
});

document.querySelectorAll('th.sortable').forEach(th => {
    th.addEventListener('click', () => {
        const field = th.dataset.sort;
        if (currentSort.field === field) {
            currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
        } else {
            currentSort.field = field;
            currentSort.direction = field === 'win_rate' || field === 'battles' || field === 'wins' || field === 'level' ? 'desc' : 'asc';
        }
        document.querySelectorAll('th.sortable').forEach(h => {
            h.classList.remove('active', 'asc', 'desc');
        });
        th.classList.add('active', currentSort.direction);
        renderTable();
    });
});

loadData();
