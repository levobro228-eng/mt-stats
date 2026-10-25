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

// Улучшенный SVG флаг СССР (красный с серпом и молотом)
const USSR_FLAG_SVG = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 90 60'><rect width='90' height='60' fill='%23CC0000'/><g fill='%23FFCC00' transform='translate(15,15) scale(0.4)'><polygon points='0,0 15,45 60,45 25,75 40,120 0,90 -40,120 -25,75 -60,45 -15,45'/><path d='M 30 150 Q 30 200 80 200 Q 130 200 130 150 L 110 150 Q 110 180 80 180 Q 50 180 50 150 Z'/><rect x='75' y='140' width='8' height='60'/><rect x='60' y='155' width='40' height='8' transform='rotate(25 80 155)'/></g></svg>";

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
    if (wr >= 50) return '#f9a
