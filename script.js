let allData = null;
let currentPeriod = '6m';

async function loadData() {
    try {
        const response = await fetch('data/tanks.json');
        allData = await response.json();
        document.getElementById('update-date').textContent = allData.updated;
        initLevelFilters();
        renderTable();
    } catch (error) {
        document.getElementById('tanks-body').innerHTML = 
            '<tr><td colspan="6" class="loading">Ошибка загрузки данных. Попробуйте позже.</td></tr>';
        console.error(error);
    }
}

function initLevelFilters() {
    const levels = new Set();
    Object.values(allData.periods).forEach(period => {
        period.forEach(tank => levels.add(tank.level));
    });
    
    const container = document.getElementById('level-filters');
    container.innerHTML = '';
    [...levels].sort((a, b) => a - b).forEach(level => {
        const label = document.createElement('label');
        label.innerHTML = `<input type="checkbox" class="filter-level" value="${level}" checked> ${level}`;
        container.appendChild(label);
    });
}

function getFilteredTanks() {
    if (!allData) return [];
    
    const tanks = allData.periods[currentPeriod] || [];
    const search = document.getElementById('search-input').value.toLowerCase();
    
    const activeTypes = [...document.querySelectorAll('.filter-type:checked')].map(cb => cb.value);
    const activeClasses = [...document.querySelectorAll('.filter-class:checked')].map(cb => cb.value);
    const activeLevels = [...document.querySelectorAll('.filter-level:checked')].map(cb => parseInt(cb.value));
    
    return tanks.filter(tank => {
        if (search && !tank.name.toLowerCase().includes(search)) return false;
        if (!activeTypes.includes(tank.category)) return false;
        if (!activeClasses.includes(tank.type)) return false;
        if (!activeLevels.includes(tank.level)) return false;
        return true;
    });
}

function getWinrateColor(winrate) {
    if (winrate >= 55) return '#ff4444';
    if (winrate >= 52) return '#ff8c00';
    if (winrate >= 50) return '#ffd700';
    if (winrate >= 48) return '#87ceeb';
    return '#4caf50';
}

function getCategoryLabel(cat) {
    const labels = { regular: 'Обычный', premium: 'Премиум', collector: 'Коллекц.' };
    return labels[cat] || cat;
}

function renderTable() {
    const tanks = getFilteredTanks();
    const tbody = document.getElementById('tanks-body');
    
    // Статистика
    document.getElementById('stat-total').textContent = tanks.length;
    const avgWinrate = tanks.length ? (tanks.reduce((s, t) => s + t.win_rate, 0) / tanks.length).toFixed(2) : 0;
    document.getElementById('stat-avg-winrate').textContent = avgWinrate + '%';
    const totalBattles = tanks.reduce((s, t) => s + t.battles, 0);
    document.getElementById('stat-battles').textContent = totalBattles.toLocaleString('ru-RU');
    
    if (tanks.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">Танки не найдены</td></tr>';
        return;
    }
    
    tbody.innerHTML = tanks.map(tank => `
        <tr>
            <td>
                <div>${tank.name}</div>
                <span class="category-badge category-${tank.category}">${getCategoryLabel(tank.category)}</span>
            </td>
            <td>${tank.type}</td>
            <td>${tank.level}</td>
            <td>${tank.type}</td>
            <td>${tank.battles.toLocaleString('ru-RU')}</td>
            <td>
                <div class="winrate-bar">
                    <span class="winrate-value" style="color: ${getWinrateColor(tank.win_rate)}">${tank.win_rate}%</span>
                    <div class="winrate-bar-bg">
                        <div class="winrate-bar-fill" style="width: ${Math.min(100, (tank.win_rate - 40) * 5)}%; background: ${getWinrateColor(tank.win_rate)}"></div>
                    </div>
                </div>
            </td>
        </tr>
    `).join('');
}

// Обработчики событий
document.getElementById('period-select').addEventListener('change', (e) => {
    currentPeriod = e.target.value;
    renderTable();
});

document.getElementById('search-input').addEventListener('input', renderTable);
document.querySelectorAll('.filter-type, .filter-class, .filter-level').forEach(cb => {
    cb.addEventListener('change', renderTable);
});

// Запуск
loadData();
