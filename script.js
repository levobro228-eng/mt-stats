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
    'ussr': 'su',
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

// URL флага СССР с Wikimedia Commons
const USSR_FLAG_URL = 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Flag_of_the_Soviet_Union.svg/40px-Flag_of_the_Soviet_Union.svg.png';

function getFlagUrl(nation) {
    if (nation === 'ussr') {
        return USSR_FLAG_URL;
    }
    var code = NATION_TO_COUNTRY[nation];
    if (!code) {
        code = 'xx';
    }
    return 'https://flagcdn.com/w40/' + code + '.png';
}

function getNationName(nation) {
    var name = NATION_NAMES[nation];
    if (!name) {
        name = nation;
    }
    return name;
}

function loadData() {
    var timestamp = new Date().getTime();
    var url = DATA_URL + '?t=' + timestamp;
    
    fetch(url)
        .then(function(response) {
            if (!response.ok) {
                throw new Error('HTTP ' + response.status);
            }
            return response.text();
        })
        .then(function(text) {
            if (text.trim() === '{}') {
                throw new Error('Файл данных пуст');
            }
            allData = JSON.parse(text);
            
            var updateEl = document.getElementById('update-date');
            if (updateEl) {
                updateEl.textContent = allData.updated || '...';
            }
            
            initNationFilters();
            updateSearchHint();
            renderTable();
        })
        .catch(function(error) {
            console.error('Ошибка:', error);
            var tbody = document.getElementById('tanks-body');
            if (tbody) {
                tbody.innerHTML = '<tr><td colspan="7" class="loading">Ошибка: ' + error.message + '</td></tr>';
            }
        });
}

function initNationFilters() {
    if (!allData || !allData.periods) {
        return;
    }
    
    var nations = new Set();
    var periods = allData.periods;
    var keys = Object.keys(periods);
    
    for (var i = 0; i < keys.length; i++) {
        var period = periods[keys[i]];
        if (Array.isArray(period)) {
            for (var j = 0; j < period.length; j++) {
                var tank = period[j];
                if (tank.nation) {
                    nations.add(tank.nation);
                }
            }
        }
    }
    
    var nationOrder = ['ussr', 'germany', 'usa', 'china', 'france', 'uk', 'japan', 'czech', 'sweden', 'poland', 'italy'];
    var sorted = Array.from(nations).sort(function(a, b) {
        var ia = nationOrder.indexOf(a);
        var ib = nationOrder.indexOf(b);
        if (ia === -1 && ib === -1) return a.localeCompare(b);
        if (ia === -1) return 1;
        if (ib === -1) return -1;
        return ia - ib;
    });
    
    var container = document.getElementById('nation-filters');
    if (!container) return;
    container.innerHTML = '';
    
    for (var i = 0; i < sorted.length; i++) {
        var nation = sorted[i];
        var btn = document.createElement('button');
        btn.className = 'nation-btn active';
        btn.dataset.nation = nation;
        btn.title = getNationName(nation);
        
        var img = document.createElement('img');
        img.src = getFlagUrl(nation);
        img.alt = getNationName(nation);
        btn.appendChild(img);
        
        btn.addEventListener('click', (function(n, b) {
            return function() {
                toggleNation(n, b);
            };
        })(nation, btn));
        
        container.appendChild(btn);
        currentFilters.nations.add(nation);
    }
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
    var tanks = allData.periods[currentPeriod] || [];
    var hint = document.getElementById('search-hint');
    if (hint) {
        hint.textContent = 'Поиск по ' + tanks.length + ' танкам';
    }
}

function getFilteredTanks() {
    if (!allData || !allData.periods) return [];
    var tanks = (allData.periods[currentPeriod] || []).slice();
    
    if (currentFilters.search) {
        var s = currentFilters.search.toLowerCase();
        tanks = tanks.filter(function(t) {
            return t.name.toLowerCase().indexOf(s) !== -1;
        });
    }
    
    if (currentFilters.nations.size > 0) {
        tanks = tanks.filter(function(t) {
            return currentFilters.nations.has(t.nation);
        });
    }
    
    if (currentFilters.classType !== 'all') {
        tanks = tanks.filter(function(t) {
            return t.type === currentFilters.classType;
        });
    }
    
    if (currentFilters.level !== 'all') {
        var lvl = parseInt(currentFilters.level);
        tanks = tanks.filter(function(t) {
            return t.level === lvl;
        });
    }
    
    if (currentFilters.category !== 'all') {
        tanks = tanks.filter(function(t) {
            return t.category === currentFilters.category;
        });
    }
    
