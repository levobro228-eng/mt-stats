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
    
    var field = currentSort.field;
    var direction = currentSort.direction;
    
    tanks.sort(function(a, b) {
        var va = a[field];
        var vb = b[field];
        if (typeof va === 'string') {
            va = va.toLowerCase();
            vb = vb.toLowerCase();
            if (direction === 'asc') {
                return va.localeCompare(vb);
            } else {
                return vb.localeCompare(va);
            }
        }
        if (direction === 'asc') {
            return va - vb;
        } else {
            return vb - va;
        }
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

function romanize(num) {
    var map = {1:'I',2:'II',3:'III',4:'IV',5:'V',6:'VI',7:'VII',8:'VIII',9:'IX',10:'X',11:'XI'};
    return map[num] || num;
}

function renderTable() {
    var tanks = getFilteredTanks();
    var tbody = document.getElementById('tanks-body');
    if (!tbody) return;
    
    var countEl = document.getElementById('stat-count');
    var avgEl = document.getElementById('stat-avg');
    var battlesEl = document.getElementById('stat-battles');
    
    if (countEl) countEl.textContent = tanks.length + ' танков';
    
    if (avgEl) {
        var avg = 0;
        if (tanks.length > 0) {
            var sum = 0;
            for (var i = 0; i < tanks.length; i++) {
                sum += tanks[i].win_rate;
            }
            avg = (sum / tanks.length).toFixed(2);
        }
        avgEl.textContent = 'Средний винрейт: ' + avg + '%';
    }
    
    if (battlesEl) {
        var totalB = 0;
        for (var i = 0; i < tanks.length; i++) {
            totalB += tanks[i].battles;
        }
        battlesEl.textContent = 'Всего боёв: ' + totalB.toLocaleString('ru-RU');
    }
    
    if (tanks.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="loading">Танки не найдены</td></tr>';
        return;
    }
    
    var html = '';
    for (var i = 0; i < tanks.length; i++) {
        var t = tanks[i];
        var nameClass = '';
        if (t.category === 'premium') {
            nameClass = 'premium-name';
        } else if (t.category === 'collector') {
            nameClass = 'collector-name';
        }
        var statusLabel = CATEGORY_LABELS[t.category] || t.category;
        var barWidth = Math.min(100, Math.max(0, (t.win_rate - 40) * 5));
        var color = getWinrateColor(t.win_rate);
        var iconHtml = '';
        if (t.icon) {
            iconHtml = '<img class="tank-icon" src="' + t.icon + '" alt="" onerror="this.style.display=\'none\'">';
        }
        
        html += '<tr>';
        html += '<td class="flag-cell"><img src="' + getFlagUrl(t.nation) + '" alt="' + getNationName(t.nation) + '" title="' + getNationName(t.nation) + '"></td>';
        html += '<td>' + romanize(t.level) + '</td>';
        html += '<td><div class="tank-name-cell">' + iconHtml + '<span class="tank-name ' + nameClass + '">' + t.name + '</span></div></td>';
        html += '<td><span class="status-badge status-' + t.category + '">' + statusLabel + '</span></td>';
        html += '<td>' + t.battles.toLocaleString('ru-RU') + '</td>';
        html += '<td>' + t.wins.toLocaleString('ru-RU') + '</td>';
        html += '<td><div class="winrate-cell"><span class="winrate-value" style="color:' + color + '">' + t.win_rate + '%</span><div class="winrate-bar-bg"><div class="winrate-bar-fill" style="width:' + barWidth + '%;background:' + color + '"></div></div></div></td>';
        html += '</tr>';
    }
    
    tbody.innerHTML = html;
}

// Обработчик для выбора периода
var periodSelect = document.getElementById('period-select');
if (periodSelect) {
    periodSelect.addEventListener('change', function(e) {
        currentPeriod = e.target.value;
        updateSearchHint();
        renderTable();
    });
}

// Обработчик поиска
var searchInput = document.getElementById('search-input');
if (searchInput) {
    searchInput.addEventListener('input', function(e) {
        currentFilters.search = e.target.value;
        renderTable();
    });
}

// Кнопка сброса
var resetBtn = document.getElementById('btn-reset');
if (resetBtn) {
    resetBtn.addEventListener('click', function() {
        currentFilters = {
            search: '',
            nations: new Set(),
            classType: 'all',
            level: 'all',
            category: 'all'
        };
        
        var searchInput = document.getElementById('search-input');
        if (searchInput) searchInput.value = '';
        
        var nationBtns = document.querySelectorAll('.nation-btn');
        for (var i = 0; i < nationBtns.length; i++) {
            nationBtns[i].classList.add('active');
            currentFilters.nations.add(nationBtns[i].dataset.nation);
        }
        
        var filterBtns = document.querySelectorAll('.filter-btn');
        for (var i = 0; i < filterBtns.length; i++) {
            filterBtns[i].classList.remove('active');
        }
        
        var allBtns = document.querySelectorAll('.filter-btn[data-class="all"], .filter-btn[data-level="all"], .filter-btn[data-category="all"]');
        for (var i = 0; i < allBtns.length; i++) {
            allBtns[i].classList.add('active');
        }
        
        renderTable();
    });
}

// Обработчики фильтров по классу
var classBtns = document.querySelectorAll('.filter-btn[data-class]');
for (var i = 0; i < classBtns.length; i++) {
    (function(btn) {
        btn.addEventListener('click', function() {
            var allBtns = document.querySelectorAll('.filter-btn[data-class]');
            for (var j = 0; j < allBtns.length; j++) {
                allBtns[j].classList.remove('active');
            }
            btn.classList.add('active');
            currentFilters.classType = btn.dataset.class;
            renderTable();
        });
    })(classBtns[i]);
}

// Обработчики фильтров по уровню
var levelBtns = document.querySelectorAll('.filter-btn[data-level]');
for (var i = 0; i < levelBtns.length; i++) {
    (function(btn) {
        btn.addEventListener('click', function() {
            var allBtns = document.querySelectorAll('.filter-btn[data-level]');
            for (var j = 0; j < allBtns.length; j++) {
                allBtns[j].classList.remove('active');
            }
            btn.classList.add('active');
            currentFilters.level = btn.dataset.level;
            renderTable();
        });
    })(levelBtns[i]);
}

// Обработчики фильтров по категории
var categoryBtns = document.querySelectorAll('.filter-btn[data-category]');
for (var i = 0; i < categoryBtns.length; i++) {
    (function(btn) {
        btn.addEventListener('click', function() {
            var allBtns = document.querySelectorAll('.filter-btn[data-category]');
            for (var j = 0; j < allBtns.length; j++) {
                allBtns[j].classList.remove('active');
            }
            btn.classList.add('active');
            currentFilters.category = btn.dataset.category;
            renderTable();
        });
    })(categoryBtns[i]);
}

// Сортировка по клику на заголовки
var sortableHeaders = document.querySelectorAll('th.sortable');
for (var i = 0; i < sortableHeaders.length; i++) {
    (function(th) {
        th.addEventListener('click', function() {
            var field = th.dataset.sort;
            if (currentSort.field === field) {
                currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
            } else {
                currentSort.field = field;
                if (field === 'win_rate' || field === 'battles' || field === 'wins' || field === 'level') {
                    currentSort.direction = 'desc';
                } else {
                    currentSort.direction = 'asc';
                }
            }
            
            var allHeaders = document.querySelectorAll('th.sortable');
            for (var j = 0; j < allHeaders.length; j++) {
                allHeaders[j].classList.remove('active', 'asc', 'desc');
            }
            th.classList.add('active', currentSort.direction);
            renderTable();
        });
    })(sortableHeaders[i]);
}

// Запуск
loadData();
