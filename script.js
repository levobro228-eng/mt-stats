var D='https://raw.githubusercontent.com/levobro228-eng/mt-stats/main/data/tanks.json';
var A=null,P='6m';
var F={s:'',n:new Set,c:'all',l:'all',k:'all'};
var S={f:'win_rate',d:'desc'};
var L={regular:'Прокачиваемые',premium:'Премиум',collector:'Коллекционные'};
var R={1:'I',2:'II',3:'III',4:'IV',5:'V',6:'VI',7:'VII',8:'VIII',9:'IX',10:'X',11:'XI'};
var FL={ussr:'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Flag_of_the_Soviet_Union.svg/40px-Flag_of_the_Soviet_Union.svg.png',russia:'https://flagcdn.com/w40/ru.png',germany:'https://flagcdn.com/w40/de.png',usa:'https://flagcdn.com/w40/us.png',china:'https://flagcdn.com/w40/cn.png',france:'https://flagcdn.com/w40/fr.png',uk:'https://flagcdn.com/w40/gb.png',japan:'https://flagcdn.com/w40/jp.png',czech:'https://flagcdn.com/w40/cz.png',sweden:'https://flagcdn.com/w40/se.png',poland:'https://flagcdn.com/w40/pl.png',italy:'https://flagcdn.com/w40/it.png'};
var NM={ussr:'СССР',russia:'Россия',germany:'Германия',usa:'США',china:'Китай',france:'Франция',uk:'Великобритания',japan:'Япония',czech:'Чехия',sweden:'Швеция',poland:'Польша',italy:'Италия'};
function gf(n){return FL[n]||'https://flagcdn.com/w40/xx.png'}
function gn(n){return NM[n]||n}
function ld(){
fetch(D+'?t='+Date.now()).then(function(r){
if(!r.ok)throw new Error('HTTP '+r.status);
return r.text();
}).then(function(t){
if(t.trim()==='{}')throw new Error('Пусто');
A=JSON.parse(t);
var e=document.getElementById('update-date');
if(e)e.textContent=A.updated||'...';
in();ht();rn();
}).catch(function(e){
console.error(e);
var b=document.getElementById('tanks-body');
if(b)b.innerHTML='<tr><td colspan="7" class="loading">'+e.message+'</td></tr>';
});
}
function in(){
if(!A)return;
var s=new Set;
var ks=Object.keys(A.periods);
for(var i=0;i<ks.length;i++){
var ar=A.periods[ks[i]];
if(Array.isArray(ar))for(var j=0;j<ar.length;j++)if(ar[j].nation)s.add(ar[j].nation);
}
var or=['ussr','germany','usa','china','france','uk','japan','czech','sweden','poland','italy'];
var so=Array.from(s).sort(function(a,b){var ia=or.indexOf(a),ib=or.indexOf(b);if(ia===-1&&ib===-1)return a.localeCompare(b);if(ia===-1)return 1;if(ib===-1)return-1;return ia-ib});
var c=document.getElementById('nation-filters');
if(!c)return;c.innerHTML='';
for(var i=0;i<so.length;i++){
var n=so[i],b=document.createElement('button');
b.className='nation-btn active';b.title=gn(n);
var im=document.createElement('img');im.src=gf(n);im.alt=gn(n);b.appendChild(im);
(function(na,bb){b.onclick=function(){if(F.n.has(na)){F.n.delete(na);bb.classList.remove('active')}else{F.n.add(na);bb.classList.add('active')}rn()}})(n,b);
c.appendChild(b);F.n.add(n);
}
}
function ht(){
if(!A)return;
var ar=A.periods[P]||[];
var e=document.getElementById('search-hint');
if(e)e.textContent='Поиск по '+ar.length+' танкам';
}
function gt(){
if(!A)return[];
var ar=(A.periods[P]||[]).slice();
if(F.s){var s=F.s.toLowerCase();ar=ar.filter(function(t){return t.name.toLowerCase().indexOf(s)!==-1})}
if(F.n.size>0)ar=ar.filter(function(t){return F.n.has(t.nation)});
if(F.c!=='all')ar=ar.filter(function(t){return t.type===F.c});
if(F.l!=='all'){var lv=parseInt(F.l);ar=ar.filter(function(t){return t.level===lv})}
if(F.k!=='all')ar=ar.filter(function(t){return t.category===F.k});
var f=S.f,d=S.d;
ar.sort(function(a,b){var va=a[f],vb=b[f];if(typeof va==='string'){va=va.toLowerCase();vb=vb.toLowerCase();return d==='asc'?va.localeCompare(vb):vb.localeCompare(va)}return d==='asc'?va-vb:vb-va});
return ar;
}
function wc(w){if(w>=55)return'#d32f2f';if(w>=52)return'#f57c00';if(w>=50)return'#f9a825';if(w>=48)return'#1976d2';return'#388e3c'}
function rn(){
var ts=gt(),tb=document.getElementById('tanks-body');
if(!tb)return;
var c1=document.getElementById('stat-count'),c2=document.getElementById('stat-avg'),c3=document.getElementById('stat-battles');
if(c1)c1.textContent=ts.length+' танков';
if(c2){var av=0;if(ts.length){var s=0;for(var i=0;i<ts.length;i++)s+=ts[i].win_rate;av=(s/ts.length).toFixed(2)}c2.textContent='Средний винрейт: '+av+'%'}
if(c3){var tt=0;for(var i=0;i<ts.length;i++)tt+=ts[i].battles;c3.textContent='Всего боёв: '+tt.toLocaleString('ru-RU')}
if(!ts.length){tb.innerHTML='<tr><td colspan="7" class="loading">Танки не найдены</td></tr>';return}
var h='';
for(var i=0;i<ts.length;i++){
var t=ts[i],nc=t.category==='premium'?'premium-name':t.category==='collector'?'collector-name':'',sl=L[t.category]||t.category,bw=Math.min(100,Math.max(0,(t.win_rate-40)*5)),cl=wc(t.win_rate),ic=t.icon?'<img class="tank-icon" src="'+t.icon+'" alt="" onerror="this.style.display=\'none\'">':'';
h+='<tr><td class="flag-cell"><img src="'+gf(t.nation)+'" alt="'+gn(t.nation)+'" title="'+gn(t.nation)+'"></td><td>'+(R[t.level]||t.level)+'</td><td><div class="tank-name-cell">'+ic+'<span class="tank-name '+nc+'">'+t.name+'</span></div></td><td><span class="status-badge status-'+t.category+'">'+sl+'</span></td><td>'+t.battles.toLocaleString('ru-RU')+'</td><td>'+t.wins.toLocaleString('ru-RU')+'</td><td><div class="winrate-cell"><span class="winrate-value" style="color:'+cl+'">'+t.win_rate+'%</span><div class="winrate-bar-bg"><div class="winrate-bar-fill" style="width:'+bw+'%;background:'+cl+'"></div></div></div></td></tr>';
}
tb.innerHTML=h;
}
var ps=document.getElementById('period-select');if(ps)ps.onchange=function(e){P=e.target.value;ht();rn()};
var si=document.getElementById('search-input');if(si)si.oninput=function(e){F.s=e.target.value;rn()};
var rb=document.getElementById('btn-reset');if(rb)rb.onclick=function(){F={s:'',n:new Set,c:'all',l:'all',k:'all'};var si2=document.getElementById('search-input');if(si2)si2.value='';var nb=document.querySelectorAll('.nation-btn');for(var i=0;i<nb.length;i++){nb[i].classList.add('active');F.n.add(nb[i].dataset.nation)}var fb=document.querySelectorAll('.filter-btn');for(var i=0;i<fb.length;i++)fb[i].classList.remove('active');var ab=document.querySelectorAll('.filter-btn[data-class="all"],.filter-btn[data-level="all"],.filter-btn[data-category="all"]');for(var i=0;i<ab.length;i++)ab[i].classList.add('active');rn()};
function bf(sel,key){var bs=document.querySelectorAll(sel);for(var i=0;i<bs.length;i++)(function(b){b.onclick=function(){var a=document.querySelectorAll(sel);for(var j=0;j<a.length;j++)a[j].classList.remove('active');b.classList.add('active');var k=key==='c'?'class':key==='k'?'category':'level';F[key]=b.dataset[k];rn()}})(bs[i])}
bf('.filter-btn[data-class]','c');bf('.filter-btn[data-level]','l');bf('.filter-btn[data-category]','k');
var ths=document.querySelectorAll('th.sortable');for(var i=0;i<ths.length;i++)(function(th){th.onclick=function(){var f=th.dataset.sort;if(S.f===f)S.d=S.d==='asc'?'desc':'asc';else{S.f=f;S.d=(f==='win_rate'||f==='battles'||f==='wins'||f==='level')?'desc':'asc'}var a=document.querySelectorAll('th.sortable');for(var j=0;j<a.length;j++)a[j].classList.remove('active','asc','desc');th.classList.add('active',S.d);rn()}})(ths[i]);
ld();
