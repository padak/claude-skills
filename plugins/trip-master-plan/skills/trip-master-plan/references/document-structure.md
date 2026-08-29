# Document structure & design system

The MASTER plan is ONE self-contained HTML artifact. No external stylesheets, images or scripts — the artifact sandbox blocks every third-party request (fetch, script, stylesheet, image AND iframe). Google Fonts links are the only allowed external resource. Publish via the Artifact tool; republish the same file path (or `url`) to keep one URL.

## Page skeleton (in order)

1. `<title>` — short name, e.g. "Labor Day z Chicaga".
2. Header: label line (dates · occasion · party · vehicle), `<h1>`, version chip (`.vchip`: VERZE n · timestamp · what pipeline built it), lede paragraph with the marker legend, `.meta-row` chips for key facts (water temp, holiday note).
3. "Rychlé srovnání" — table of all routes; first cell links `#trasa-x`; rating dots `●●○` per interest dimension; "nejdelší úsek"; character. One-line recommendation under it.
4. Weather section (see weather.md): day-tab buttons + own SVG weather map + `#wx-stamp` + `#wx-data` JSON + Windy point links per route base.
5. One `<section class="route x" id="trasa-x">` per alternative (colors: a=lake, b=pine, c=brick, d=steel, e=dune, f=muted).
6. Practical grid (`.grid2` of `.pract` cards): book-now list, timezones, tolls/fees, safety/water checks with official links.
7. "Co zbývá doverifikovat" — honest, shrinking list; when only live-booking/phone items remain, list phone numbers.
8. Footer: version history (one line per version), sources, photo credits.

## Route section fragment

```html
<section class="route a" id="trasa-a">
  <div class="route-head">
    <div class="badge">A</div>
    <div>
      <h2>Název trasy — tři slova, co ji vystihují</h2>
      <p class="route-sub">Zastávka → Zastávka → Zastávka → zpět. Proč právě tento víkend (které akce zrovna běží).</p>
      <p class="route-stats">≈ 790 km · ~8 h 30 čisté jízdy za víkend · <a href="GMAPS_ROUTE_URL" target="_blank" rel="noopener">otevřít trasu v Google Maps ↗</a></p>
      <p class="route-pitch">Prodejní odstavec: konkrétní obrazy z trasy, žádná generická adjektiva. 4–6 vět.</p>
    </div>
  </div>
  <figure class="map"><!-- overview SVG map --><figcaption>Okruh ≈ 790 km · nejdelší úsek ~2 h 10 · pěšky 2–6 km denně · trasa vede po skutečných silnicích</figcaption></figure>
  <!-- day cards … -->
  <div class="note"><span class="label">Čemu se vyhnout</span><br>Pojmenovaná turistická past + poctivá alternativa.</div>
</section>
```

## Day card fragment

Drive bars (`.drive`) carry ONLY logistics; every attraction lives as a full `<li>` with substance. Day cards with a map get class `has-map` (desktop: text left, sticky day map right).

```html
<div class="day has-map">
    <div class="day-head"><span class="day-num">Pá 4. 9.</span><span class="day-title">Přílet → Milwaukee</span><span class="wx" title="NWS předpověď — klik: živě na Windy"><span class="wxv" data-wx="milwaukee:pa">⛅ 27° · 20 %</span> · <a href="https://www.windy.com/43.04/-87.91?temp,43.04,-87.91,9" target="_blank" rel="noopener">Windy ↗</a></span></div>
    <figure class="dmap"><!-- per-day SVG map from genmaps.py --><figcaption>Pá 4. 9. — ≈ 165 km · ~1 h 45 jízdy · čísla = pořadí zastávek · <a href="GMAPS_DAY_URL" target="_blank" rel="noopener">Google Maps ↗</a></figcaption></figure>
    <span class="drive">O'Hare → Wilmette → Milwaukee · <b>~40 min + ~1 h</b> podél jezera po Sheridan Rd / I-94</span>
    <ul>
      <li>Zastávka <a href="OFFICIAL_URL" target="_blank" rel="noopener"><b>Jméno atrakce</b></a> — 1–3 věty proč stojí za to, kolik času, vstupné. <span class="verified">✓ pá: 6–20</span> <span class="src">ChatGPT</span></li>
      <li>Nocleh: Město (čtvrť / tip na hotel). <span class="check">ceny ověřit</span></li>
    </ul>
    <div class="phs"><a class="ph" href="COMMONS_FILE_PAGE" target="_blank" rel="noopener" title="Autor · Licence"><img src="data:image/jpeg;base64,..." alt="Popis" loading="lazy"><span>Popisek fotky</span></a></div>
    <div class="tags"><span class="tag art">umění</span><span class="tag tech">technika</span><span class="tag swim">koupání</span><span class="tag nature">příroda</span></div>
  </div>
```

## Marker vocabulary

- `<span class="verified">✓ …</span>` — confirmed for the exact trip dates (say what and per which source).
- `<span class="check">…ověřit</span>` — plausible, unconfirmed; be specific about what to check.
- `<span class="src">ChatGPT</span>` / `Perplexity` / assistant name — provenance of an idea taken from elsewhere.

## Copy-to-clipboard research prompt buttons

Append this script at the end of the body. It decorates every itinerary `<li>` (and drive bars containing "zastávka") with a `⎘`-button that copies a complete research prompt built from: a WHO constant (party, dates, interests, anti-tourist-trap stance), the route name, the day context, the li text, and 8 standard questions. Adapt WHO to the trip; keep the fallback copy path.

```html
<script>
(function(){
 var WHO = "Jsme 3 dospělí na roadtripu pronajatým autem z Chicaga (letiště O'Hare), víkend Labor Day: pátek 4. 9. až pondělí 7. 9. 2026 (pondělí je státní svátek). Zajímá nás příroda, technické památky, umění, americká historie, koupání a lokální akce (trhy, festivaly, farmy); vyhýbáme se turistickým pastem a řetězcům.";
 function cleanText(el){
  var c = el.cloneNode(true);
  c.querySelectorAll('button.pxq').forEach(function(b){b.remove();});
  return c.textContent.replace(/\s+/g,' ').trim();
 }
 function routeName(el){
  var sec = el.closest('section.route');
  if(!sec) return '';
  var h2 = sec.querySelector('h2');
  if(!h2) return '';
  var c = h2.cloneNode(true);
  c.querySelectorAll('.src').forEach(function(s){s.remove();});
  return c.textContent.replace(/\s+/g,' ').trim();
 }
 function buildPrompt(el){
  var day = el.closest('.day');
  var when = 'v průběhu víkendu 4.–7. 9. 2026';
  if(day){
   var n = day.querySelector('.day-num'), t = day.querySelector('.day-title');
   if(n) when = n.textContent.trim() + (t ? ' — den s programem „' + t.textContent.trim() + '“' : '');
  }
  var bolds = Array.prototype.map.call(el.querySelectorAll('b'), function(b){return b.textContent.trim();})
    .filter(function(x){return x.length > 2;});
  var subject = bolds.length ? bolds.join(' + ') : cleanText(el).slice(0,90);
  var ctx = cleanText(el).slice(0,450);
  var rn = routeName(el);
  return WHO +
   "\n\nMísto/zážitek, který mě teď zajímá: " + subject + "." +
   (rn ? "\nJe to součást naší trasy „" + rn + "“." : '') +
   "\nKdy tam budu: " + when + "." +
   "\nKontext z mého itineráře: „" + ctx + "“" +
   "\n\nDohledej mi prosím AKTUÁLNÍ informace k tomuto místu přesně k datu mé návštěvy:" +
   "\n1) otevírací doba v ten den (pozor na sváteční režim o Labor Day) a případné vstupné," +
   "\n2) nutnost rezervace/vstupenek předem + přímý odkaz, kde koupit," +
   "\n3) co se tam přesně ten den koná (program, koncerty, akce, časy)," +
   "\n4) parkování a logistika příjezdu (kde zaparkovat, kolik to stojí)," +
   "\n5) kolik času si vyhradit a co rozhodně nevynechat," +
   "\n6) 2–3 doporučení na dobré lokální jídlo poblíž (žádné řetězce)," +
   "\n7) aktuální uzavírky, omezení, práce, změny v roce 2026," +
   "\n8) náhradní plán poblíž, kdyby celý den pršelo." +
   "\n\nOvěřuj primárně na oficiálních webech a uveď zdroje s odkazy. Pokud se něco nekoná nebo je zavřeno, napiš to na rovinu a navrhni alternativu. Odpověz česky.";
 }
 function copyText(txt, btn){
  function done(ok){
   var old = '⎘ Perplexity';
   btn.textContent = ok ? '✓ zkopírováno' : 'chyba – zkuste znovu';
   btn.classList.add('ok');
   setTimeout(function(){ btn.textContent = old; btn.classList.remove('ok'); }, 1800);
  }
  function fallback(){
   try{
    var ta = document.createElement('textarea');
    ta.value = txt; ta.style.position='fixed'; ta.style.opacity='0';
    document.body.appendChild(ta); ta.select();
    var ok = document.execCommand('copy');
    ta.remove(); done(ok);
   }catch(e){ done(false); }
  }
  if(navigator.clipboard && navigator.clipboard.writeText){
   navigator.clipboard.writeText(txt).then(function(){done(true);}, function(){fallback();});
  } else { fallback(); }
 }
 var targets = [];
 document.querySelectorAll('section.route .day li').forEach(function(li){ targets.push(li); });
 document.querySelectorAll('section.route .drive').forEach(function(d){
  if(d.textContent.indexOf('zastávka') !== -1) targets.push(d);
 });
 targets.forEach(function(el){
  var b = document.createElement('button');
  b.type = 'button'; b.className = 'pxq'; b.textContent = '⎘ Perplexity';
  b.title = 'Zkopírovat prompt pro Perplexity s kontextem této zastávky';
  b.addEventListener('click', function(){ copyText(buildPrompt(el), b); });
  el.appendChild(b);
 });
})();
</script>
```

## Weather chips + widget wiring

```html
<script>
  document.addEventListener('DOMContentLoaded',function(){
    var data;
    try{ data=JSON.parse(document.getElementById('wx-data').textContent); }catch(e){ return; }
    function fmt(v){
      if(!v||v.t==null) return null;
      var s=(v.i||'')+' '+v.t+'°';
      if(v.p!=null&&v.p>0) s+=' · '+v.p+' %';
      return s;
    }
    function show(day){
      document.querySelectorAll('.wx-val[data-loc]').forEach(function(el){
        var v=fmt((data[el.getAttribute('data-loc')]||{})[day]);
        el.textContent=v||'—';
        el.style.opacity=v?1:.45;
      });
      document.querySelectorAll('.wx-tab').forEach(function(b){
        b.classList.toggle('active', b.getAttribute('data-day')===day);
      });
    }
    document.querySelectorAll('.wx-tab').forEach(function(b){
      b.addEventListener('click',function(){ show(b.getAttribute('data-day')); });
    });
    // chips in itinerary
    document.querySelectorAll('.wxv[data-wx]').forEach(function(el){
      var kd=el.getAttribute('data-wx').split(':');
      var v=fmt((data[kd[0]]||{})[kd[1]]);
      if(v) el.textContent=v;
    });
    show('pa');
  });
  </script>
```

## Design system (complete stylesheet)

Use this verbatim as the base; it is token-driven and renders in light, dark and system themes. Route accent colors and all component classes referenced above are defined here.

```html
<style>
:root{
  --paper:#F4F3ED;
  --card:#FCFBF7;
  --ink:#25313A;
  --muted:#5C6A72;
  --line:#D8D6CC;
  --lake:#175E7A;
  --lake-ink:#FFFFFF;
  --lake-soft:#E3EDF1;
  --dune:#A5721F;
  --dune-soft:#F3EAD6;
  --pine:#3E6B4F;
  --pine-soft:#E4EDE6;
  --brick:#96482F;
  --brick-soft:#F2E4DE;
  --steel:#46608C;
  --steel-soft:#E4E9F2;
  --shadow:0 1px 3px rgba(20,30,38,.08);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --paper:#151B20;
    --card:#1D242B;
    --ink:#E6E2D6;
    --muted:#9AA5AA;
    --line:#38434C;
    --lake:#6FB4CE;
    --lake-ink:#0F1A20;
    --lake-soft:#1E3540;
    --dune:#D9A94E;
    --dune-soft:#382E1B;
    --pine:#8CBF9C;
    --pine-soft:#22322A;
    --brick:#D98A6E;
    --brick-soft:#3A2620;
    --steel:#9DB4E0;
    --steel-soft:#232C3B;
    --shadow:0 1px 3px rgba(0,0,0,.4);
  }
}
:root[data-theme="dark"]{
  --paper:#151B20;
  --card:#1D242B;
  --ink:#E6E2D6;
  --muted:#9AA5AA;
  --line:#38434C;
  --lake:#6FB4CE;
  --lake-ink:#0F1A20;
  --lake-soft:#1E3540;
  --dune:#D9A94E;
  --dune-soft:#382E1B;
  --pine:#8CBF9C;
  --pine-soft:#22322A;
  --brick:#D98A6E;
  --brick-soft:#3A2620;
  --steel:#9DB4E0;
  --steel-soft:#232C3B;
  --shadow:0 1px 3px rgba(0,0,0,.4);
}
body{
  background:var(--paper);
  color:var(--ink);
  font-family:"Source Serif 4", Georgia, "Times New Roman", serif;
  font-size:16.5px;
  line-height:1.6;
  margin:0;
}
.wrap{max-width:1140px;margin:0 auto;padding:40px 22px 80px;}
h1,h2,h3,.label,.tag,.badge,.drive,.day-num,th,.src,.vchip{
  font-family:"Overpass", "Helvetica Neue", Arial, sans-serif;
}
h1{font-size:2.3rem;font-weight:800;line-height:1.1;margin:.2em 0 .3em;text-wrap:balance;}
h2{font-size:1.45rem;font-weight:800;margin:0;text-wrap:balance;}
h3{font-size:1.02rem;font-weight:700;margin:0 0 .35em;}
p{margin:.55em 0;}
a{color:var(--lake);text-decoration-thickness:1px;text-underline-offset:2px;}
a:focus-visible,button:focus-visible{outline:2px solid var(--lake);outline-offset:2px;border-radius:3px;}
.label{text-transform:uppercase;letter-spacing:.12em;font-weight:700;font-size:.72rem;color:var(--muted);}
.lede{font-size:1.08rem;}
.vchip{
  display:inline-flex;gap:10px;align-items:baseline;flex-wrap:wrap;
  background:var(--card);border:1px solid var(--line);border-radius:6px;
  padding:7px 14px;font-size:.82rem;font-weight:600;box-shadow:var(--shadow);margin:4px 0 14px;
}
.vchip b{font-weight:800;letter-spacing:.05em;}
.meta-row{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0 6px;}
.meta{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:8px 14px;font-size:.85rem;box-shadow:var(--shadow);font-family:"Overpass",Arial,sans-serif;font-weight:600;}
.compare{overflow-x:auto;margin:14px 0 8px;}
table{border-collapse:collapse;width:100%;min-width:780px;background:var(--card);border:1px solid var(--line);border-radius:8px;overflow:hidden;font-size:.88rem;}
th,td{padding:9px 12px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top;}
th{font-size:.7rem;text-transform:uppercase;letter-spacing:.09em;color:var(--muted);font-weight:700;background:var(--paper);}
tr:last-child td{border-bottom:none;}
td:first-child{font-family:"Overpass",Arial,sans-serif;font-weight:700;white-space:nowrap;}
td:first-child a{text-decoration:none;border-bottom:2px solid currentColor;}
.dots{color:var(--dune);letter-spacing:2px;white-space:nowrap;}
.route{margin-top:48px;border-top:3px solid var(--line);padding-top:22px;scroll-margin-top:16px;}
.route-head{display:flex;align-items:flex-start;gap:16px;margin-bottom:6px;}
.badge{flex:none;width:52px;height:56px;display:grid;place-items:center;background:var(--lake);color:var(--lake-ink);font-weight:800;font-size:1.5rem;border-radius:8px 8px 22px 22px;box-shadow:var(--shadow);border:2px solid var(--card);}
.route.b .badge{background:var(--pine);}
.route.c .badge{background:var(--brick);}
.route.d .badge{background:var(--steel);}
.route.e .badge{background:var(--dune);}
.route.f .badge{background:var(--muted);}
.route-sub{color:var(--muted);font-size:.95rem;margin:.2em 0 0;}
.route-stats{font-family:"Overpass",Arial,sans-serif;font-size:.85rem;font-weight:700;margin:.55em 0 0;color:var(--ink);}
.route-stats a{font-weight:700;}
.route-pitch{margin:.75em 0 0;font-size:1.02rem;}
button.pxq{font-family:"Overpass",Arial,sans-serif;font-size:.68rem;font-weight:700;letter-spacing:.04em;
 color:var(--muted);background:var(--paper);border:1px solid var(--line);border-radius:99px;
 padding:2px 9px;margin-left:8px;cursor:pointer;vertical-align:1px;white-space:nowrap;}
button.pxq:hover{color:var(--lake);border-color:var(--lake);}
button.pxq.ok{color:var(--pine);border-color:var(--pine);}
details.hod{margin:14px 0;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 16px;box-shadow:var(--shadow);}
details.hod summary{cursor:pointer;font-family:"Overpass",Arial,sans-serif;font-weight:700;font-size:.95rem;}
details.hod table{min-width:0;border:none;margin:.6em 0;}
details.hod td:first-child{color:var(--muted);font-size:.8rem;}
details.hod h3{margin-top:.8em;}
.day{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px 14px;margin:14px 0;box-shadow:var(--shadow);}
.day-head{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin-bottom:4px;}
.day-num{font-weight:800;font-size:.78rem;text-transform:uppercase;letter-spacing:.1em;color:var(--lake);border-bottom:3px solid var(--lake);padding-bottom:2px;}
.route.b .day-num{color:var(--pine);border-color:var(--pine);}
.route.c .day-num{color:var(--brick);border-color:var(--brick);}
.route.d .day-num{color:var(--steel);border-color:var(--steel);}
.route.e .day-num{color:var(--dune);border-color:var(--dune);}
.wx-tabs{display:flex;gap:8px;margin:10px 0;}
.wx-tab{font:700 .8rem "Overpass",Arial,sans-serif;color:var(--muted);background:var(--card);border:1px solid var(--line);border-radius:99px;padding:5px 16px;cursor:pointer;}
.wx-tab.active{color:var(--lake-ink);background:var(--lake);border-color:var(--lake);}
.wx-tab:hover{border-color:var(--lake);}
.wx-dot{fill:var(--lake);}
.wx-val{font:800 13px "Overpass",Arial,sans-serif;fill:var(--ink);paint-order:stroke;stroke:var(--card);stroke-width:3px;stroke-linejoin:round;}
.wx-name{font:600 10.5px "Overpass",Arial,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--card);stroke-width:3px;stroke-linejoin:round;}
.wx{font:600 .72rem "Overpass",Arial,sans-serif;color:var(--muted);background:var(--paper);border:1px solid var(--line);border-radius:99px;padding:2px 10px;white-space:nowrap;}
.day-title{font-family:"Overpass",Arial,sans-serif;font-weight:700;font-size:1.05rem;}
.drive{display:block;margin:10px 0 2px;padding:7px 12px;border-left:3px dashed var(--dune);color:var(--muted);font-size:.83rem;font-weight:600;background:var(--dune-soft);border-radius:0 6px 6px 0;}
.drive b{color:var(--ink);font-weight:800;}
ul{margin:.5em 0 .3em;padding-left:1.25em;}
li{margin:.45em 0;}
li::marker{color:var(--dune);}
.tags{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px;}
.tag{font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;padding:3px 9px 2px;border-radius:99px;border:1px solid var(--line);color:var(--muted);background:var(--paper);}
.tag.swim{background:var(--lake-soft);color:var(--lake);border-color:transparent;}
.tag.tech{background:var(--dune-soft);color:var(--dune);border-color:transparent;}
.tag.nature{background:var(--pine-soft);color:var(--pine);border-color:transparent;}
.tag.art{background:var(--brick-soft);color:var(--brick);border-color:transparent;}
.note{border:1px solid var(--line);border-left:4px solid var(--dune);background:var(--card);border-radius:0 8px 8px 0;padding:10px 16px;margin:14px 0;font-size:.93rem;}
.note .label{color:var(--dune);}
.verified{color:var(--pine);font-weight:600;white-space:nowrap;font-family:"Overpass",Arial,sans-serif;font-size:.78rem;}
.check{color:var(--muted);font-family:"Overpass",Arial,sans-serif;font-size:.78rem;font-weight:600;white-space:nowrap;}
.src{font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);border:1px solid var(--line);border-radius:4px;padding:1px 6px;white-space:nowrap;vertical-align:1px;}
.small{font-size:.88rem;color:var(--muted);}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;margin-top:12px;}
.pract{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;box-shadow:var(--shadow);}
.pract p{font-size:.92rem;margin:.4em 0;}
.phs{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0 4px;}
.ph{display:block;width:132px;text-decoration:none;}
.ph img{width:132px;height:94px;object-fit:cover;border-radius:6px;display:block;border:1px solid var(--line);}
.ph span{display:block;font:600 .62rem "Overpass",Arial,sans-serif;color:var(--muted);padding-top:3px;line-height:1.25;}
figure.dmap{margin:10px 0 4px;background:var(--paper);border:1px solid var(--line);border-radius:8px;padding:8px 8px 4px;}
figure.dmap svg{display:block;max-width:100%;height:auto;}
figure.dmap figcaption{font:600 .72rem "Overpass",Arial,sans-serif;color:var(--muted);padding:5px 2px 2px;}
@media (min-width:1000px){
  .day.has-map{display:grid;grid-template-columns:minmax(0,1fr) 350px;column-gap:20px;grid-auto-rows:min-content;}
  .day.has-map .day-head{grid-column:1/-1;}
  .day.has-map figure.dmap{grid-column:2;grid-row:2/span 40;margin-top:6px;position:sticky;top:12px;align-self:start;}
  .day.has-map > *:not(figure.dmap):not(.day-head){grid-column:1;}
}
figure.map{margin:14px 0 4px;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px 8px;box-shadow:var(--shadow);}
figure.map svg{display:block;max-width:100%;height:auto;}
figure.map figcaption{font-family:"Overpass",Arial,sans-serif;font-size:.8rem;font-weight:600;color:var(--muted);padding:8px 2px 4px;border-top:1px dashed var(--line);margin-top:6px;}
.m-stop{font:600 11px "Overpass",Arial,sans-serif;fill:currentColor;}
.m-time{font:600 9.5px "Overpass",Arial,sans-serif;fill:var(--muted);}
.m-lake-label{font:700 10px "Overpass",Arial,sans-serif;fill:var(--lake);opacity:.7;letter-spacing:.1em;}
.gm-land{fill:var(--paper);}
.gm-water{fill:var(--lake-soft);}
.gm-river{stroke:var(--lake-soft);stroke-width:1.6;}
.gm-border{stroke:var(--line);stroke-width:1;stroke-dasharray:5 4;}
.gm-road{stroke:var(--line);stroke-width:.8;opacity:.55;}
.gm-stop{font:600 12px "Overpass",Arial,sans-serif;fill:var(--ink);paint-order:stroke;stroke:var(--card);stroke-width:3px;stroke-linejoin:round;}
.gm-num{font:800 9.5px "Overpass",Arial,sans-serif;fill:var(--card);}
.gm-state{font:700 11px "Overpass",Arial,sans-serif;fill:var(--muted);opacity:.55;letter-spacing:.18em;}
.gm-sea{font:700 11px "Overpass",Arial,sans-serif;fill:var(--lake);opacity:.65;letter-spacing:.14em;}

footer{margin-top:48px;border-top:1px solid var(--line);padding-top:16px;font-size:.85rem;color:var(--muted);}
@media (max-width:560px){
  h1{font-size:1.8rem;}
  .badge{width:44px;height:48px;font-size:1.25rem;}
}
</style>
```

## Publishing checklist (every version)

1. Bump `.vchip` version + timestamp (user's timezone, honest clock).
2. Append one history line to the footer.
3. Programmatic tag-balance check (`<div>`/`</div>` counts etc.).
4. Playwright screenshot at ~1500 px and mobile width; check a light AND dark render at least once per big layout change.
5. Republish same path/URL via Artifact; never create a second artifact for the same trip.
