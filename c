<!DOCTYPE html><html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#ffcc00">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="https://unpkg.com/html5-qrcode"></script>
<script>if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js')}</script>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
body{background:#0a0a0a;color:#fff;padding:14px;overflow-x:hidden;transition:0.3s}
body.light{background:#f4f1ea;color:#111}
.bg{position:fixed;inset:0;z-index:-1;overflow:hidden;background:radial-gradient(800px at 20% -10%,rgba(255,204,0,0.15),transparent),radial-gradient(600px at 90% 20%,rgba(0,208,132,0.12),transparent),#0a0a0a}
.bg span{position:absolute;display:block;width:50px;height:50px;background:rgba(255,204,0,0.07);animation:move 18s linear infinite;bottom:-100px;border-radius:50%}
.bg span:nth-child(1){left:15%;width:80px;height:80px;animation-delay:0s}
.bg span:nth-child(2){left:35%;width:30px;height:30px;background:rgba(0,208,132,0.1);animation-delay:3s}
.bg span:nth-child(3){left:75%;width:60px;height:60px;animation-delay:6s}
.bg span:nth-child(4){left:90%;width:45px;height:45px;background:rgba(255,0,0,0.07);animation-delay:9s}
@keyframes move{0%{transform:translateY(0) rotate(0);opacity:1}100%{transform:translateY(-1100px) rotate(720deg);opacity:0}}
.card{background:rgba(30,30,30,0.88);backdrop-filter:blur(14px);border-radius:20px;padding:16px;margin:12px 0;border:1px solid #2a2a2a;transition:0.4s;animation:fade 0.6s}
.card:hover{transform:translateY(-4px);border-color:#ffcc00;box-shadow:0 12px 40px rgba(255,204,0,0.22)}
@keyframes fade{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}
.total{font-weight:bold;text-align:center;background:linear-gradient(135deg,#ffcc00,#ff8800);color:#000;padding:18px;border-radius:18px}
.profit{background:linear-gradient(135deg,#00d084,#00a86b);color:#000}
.debt{background:linear-gradient(135deg,#ff4b4b,#b30000);color:#fff}
.ai{background:linear-gradient(135deg,#0a3d1f,#00d084);border:none;color:#fff}
input,select{width:100%;padding:12px;margin:6px 0;border-radius:12px;border:1px solid #444;background:#222;color:#fff;font-size:16px;transition:0.3s}
input:focus{border-color:#ffcc00;box-shadow:0 0 0 3px rgba(255,204,0,0.2);outline:none;transform:scale(1.01)}
button{width:100%;padding:13px;border:none;border-radius:12px;font-weight:bold;cursor:pointer;transition:0.25s;margin-top:6px}
button:hover{transform:translateY(-2px)}button:active{transform:scale(0.98)}
.btn-sell{background:#ffcc00;color:#000}.btn-stock{background:#00d084;color:#000}.btn-debt{background:#ff4b4b;color:#fff}
li{background:#242424;padding:11px 12px;margin:6px 0;border-radius:12px;display:flex;justify-content:space-between;align-items:center;transition:0.3s;border-left:3px solid transparent}
li:hover{background:#2e2e2e;transform:translateX(6px);border-left:3px solid #ffcc00}
.low{border:2px solid #ff4b4b!important;animation:pulse 1.5s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(255,75,75,0.7)}70%{box-shadow:0 0 0 10px rgba(255,75,75,0)}100%{box-shadow:0 0 0 0 rgba(255,75,75,0)}}
.badge{background:#ffcc00;color:#000;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:bold}
.top{display:grid;grid-template-columns:1fr 1fr;gap:10px}
</style></head><body>
<div class="bg"><span></span><span></span><span></span><span></span></div>

<h2 style="text-align:center;background:linear-gradient(90deg,#ffcc00,#ff8800);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:32px;margin:6px">BizTrack Africa</h2>
<p style="text-align:center;color:#666;font-size:11px">BEST IN AFRICA • <a href="/logout" style="color:#666">Logout</a> • <a href="/export" style="color:#ffcc00;text-decoration:none">Export</a></p>

<div class="top">
<div class="card total">Sales<br>{{total_sales}} UGX</div>
<div class="card total profit">Profit<br>{{total_profit}} UGX</div>
</div>
<div class="card debt">Abanja / Debt: {{total_debt}} UGX | Stock Value: {{total_stock_value}} UGX</div>

<div class="card ai">
<h4>🤖 AI Advisor</h4>
<p style="margin-top:8px"><b>{{advice}}</b></p>
<p style="font-size:12px;opacity:0.8;margin-top:4px">Best: {{best_seller}} • Low Stock: {{low_stock|length}} items</p>
{% if low_stock %}<div style="margin-top:8px;background:#ff4b4b;padding:8px;border-radius:10px;font-size:12px">⚠️ {% for s in low_stock %}{{s[0]}} ({{s[1]}} left) {% endfor %}</div>{% endif %}
</div>

<div style="display:flex;gap:8px">
<button onclick="document.body.classList.toggle('light')" style="background:#222;color:#fff;flex:1">🌙 Theme</button>
<button onclick="toggleLang()" id="langBtn" style="background:#222;color:#fff;flex:1">🇺🇬 Luganda</button>
</div>

<div class="card"><h4>📊 Weekly Sales</h4><canvas id="chart" height="140"></canvas></div>

<div class="card" style="border:2px solid #ffcc00">
<h4>📱 MTN / Airtel MoMo</h4>
<form action="/momo_pay" method="post">
<select name="network" style="background:#ffcc00;color:#000;font-weight:bold"><option value="MTN">MTN MoMo</option><option value="AIRTEL">Airtel Money</option></select>
<input name="phone" placeholder="078XXXXXXX" required>
<input name="amount" type="number" placeholder="Amount UGX" required>
<input name="item" placeholder="Item" required>
<button style="background:#ffcc00;color:#000">💸 Record MoMo Payment</button>
</form>
</div>

<div class="card">
<h4>🎤 Voice + 📷 Smart Barcode</h4>
<button onclick="startVoice()" style="background:#333;color:#fff">🎤 Say "Sell Sugar 5000"</button>
<div id="reader" style="margin-top:10px"></div>
<button onclick="startScan()" style="background:#333;color:#fff">📷 Scan (Auto Name Lookup)</button>
<form action="/sell" method="post" style="margin-top:10px">
<input name="item" id="itemInput" placeholder="Item / Barcode" required>
<input name="sell_price" id="priceInput" type="number" placeholder="Selling Price" required>
<input name="buy_price" type="number" placeholder="Buying Price (new)">
<input name="customer" placeholder="Customer (optional)">
<select name="method"><option value="Cash">Cash</option><option value="MTN">MTN</option><option value="AIRTEL">AIRTEL</option><option value="MoMo">MoMo</option></select>
<button class="btn-sell">Sell →</button>
</form>
</div>

<div class="card">
<h4>📦 Stock (with Barcode Save)</h4>
<form action="/add_stock" method="post">
<input name="item" placeholder="Item Name" required>
<input name="qty" type="number" placeholder="Qty" required>
<input name="buy_price" type="number" placeholder="Buy Price" required>
<input name="barcode" placeholder="Barcode (optional, for auto-lookup)">
<button class="btn-stock">Add Stock</button>
</form>
<ul>{% for s in stock %}<li class="{% if s[1]<5 %}low{% endif %}"><span>{{s[0]}} {% if s[3] %}<small style="color:#888">({{s[3]}})</small>{% endif %}</span><span class="badge">{{s[1]}} pcs</span></li>{% endfor %}</ul>
</div>

<div class="card">
<h4>💳 Debt Book</h4>
<form action="/add_debt" method="post"><input name="customer" placeholder="Customer" required><input name="item" placeholder="Item" required><input name="amount" type="number" placeholder="Amount" required><button class="btn-debt">Add Debt</button></form>
<ul>{% for d in debts %}<li><span>{{d[1]}} - {{d[2]}}</span><span>{{d[3]}} UGX <a href="/pay_debt/{{d[0]}}" style="color:#00d084;text-decoration:none">[PAID]</a></span></li>{% endfor %}</ul>
</div>

<div class="card">
<h4>🧾 Sales</h4>
<input id="search" placeholder="Search..." onkeyup="filterSales()">
<ul id="salesList">{% for s in sales %}<li><span>{{s[1]}}<br><small style="color:#888">{{s[5]}} • {{s[6]}}</small></span><span>{{s[2]}} UGX <a href="/receipt/{{s[0]}}" target="_blank" style="color:#ffcc00;text-decoration:none">🧾</a></span></li>{% endfor %}</ul>
</div>

<script>
const labels={{chart_labels|tojson}}; const data={{chart_data|tojson}};
if(labels.length>0){new Chart(document.getElementById('chart'),{type:'bar',data:{labels:labels,datasets:[{label:'UGX',data:data,backgroundColor:'#ffcc00',borderRadius:10}]},options:{plugins:{legend:{display:false}},scales:{y:{ticks:{color:'#888'}},x:{ticks:{color:'#888'}}}}})}
function filterSales(){let q=document.getElementById('search').value.toLowerCase();document.querySelectorAll('#salesList li').forEach(li=>{li.style.display=li.innerText.toLowerCase().includes(q)?'flex':'none'})}
function startVoice(){let r=new(window.SpeechRecognition||window.webkitSpeechRecognition)();r.onresult=e=>{let t=e.results[0][0].transcript.toLowerCase().split(' ');if(t[0]=='sell'){document.getElementById('itemInput').value=t[1]||'';document.getElementById('priceInput').value=t[2]||''}};r.start();}
async function lookupBarcode(bc){
 let box=document.getElementById('reader'); box.innerHTML="<p style='color:#ffcc00'>🔍 "+bc+"...</p>";
 try{let res=await fetch(`https://world.openfoodfacts.org/api/v0/product/${bc}.json`);let j=await res.json();if(j.status==1){let name=j.product.product_name||j.product.generic_name||bc; let brand=j.product.brands||''; let full=brand?brand+' '+name:name; document.getElementById('itemInput').value=full; box.innerHTML=`<p style='color:#00d084'>✓ ${full}</p>`; if(navigator.vibrate)navigator.vibrate(200); return;}}catch(e){}
 document.getElementById('itemInput').value=bc; box.innerHTML=`<p style='color:#888'>Barcode ${bc} - not found online, type name once and I'll remember</p>`;
}
let qrScanner=null;
function startScan(){
 let box=document.getElementById('reader');
 if(qrScanner){qrScanner.stop().then(()=>{qrScanner=null;box.innerHTML="";});return;}
 box.innerHTML="<p style='color:#ffcc00'>Opening camera...</p>";
 qrScanner=new Html5Qrcode("reader");
 qrScanner.start({facingMode:"environment"},{fps:10,qrbox:{width:250,height:250}},(dec)=>{try{new Audio('https://actions.google.com/sounds/v1/cartoon/pop.ogg').play()}catch{};qrScanner.stop().then(()=>{qrScanner=null;lookupBarcode(dec);});},()=>{}).catch(e=>{
   box.innerHTML=`<p style='color:#ff4b4b'>Camera blocked on http</p><input type='file' id='fileScan' accept='image/*'><p style='font-size:12px;color:#666'>Upload barcode photo</p>`;
   document.getElementById('fileScan').addEventListener('change',function(){let f=this.files[0];if(!f)return;let h=new Html5Qrcode("reader");h.scanFile(f,true).then(d=>lookupBarcode(d)).catch(()=>box.innerHTML="Can't read");});
 });
}
let lug=false;
function toggleLang(){lug=!lug;document.getElementById('langBtn').innerText=lug?'🇬🇧 English':'🇺🇬 Luganda'; if(lug) alert('Luganda mode: Ebyamaguzi=Stock, Abanja=Debts, Okutunda=Sales');}
</script>
</body></html>
