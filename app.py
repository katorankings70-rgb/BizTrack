from flask import Flask, render_template, request, redirect, session, Response, send_from_directory
import sqlite3, datetime, csv, io, os
app = Flask(__name__)
app.secret_key = "trackbiz_fix_v61"
BUSINESS_NAME = "TrackBiz Africa"
BUSINESS_PHONE = "0742965591"
BUSINESS_EMAIL = "katorankings70@gmail.com"

def get_db():
    conn = sqlite3.connect('database.db')
    try:
        cols = [r[1] for r in conn.execute('PRAGMA table_info(stock)').fetchall()]
        if cols and len(cols)!= 5:
            print("OLD DB FOUND - FIXING...")
            conn.execute('DROP TABLE IF EXISTS stock')
    except: pass
    conn.execute('CREATE TABLE IF NOT EXISTS stock (item TEXT PRIMARY KEY, qty INTEGER, buy_price INTEGER, barcode TEXT, image TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, item TEXT, sell_price INTEGER, buy_price INTEGER, profit INTEGER, method TEXT, date TEXT, customer TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS debts (id INTEGER PRIMARY KEY, customer TEXT, item TEXT, amount INTEGER, date TEXT, paid INTEGER DEFAULT 0)')
    conn.execute('CREATE TABLE IF NOT EXISTS barcodes (barcode TEXT PRIMARY KEY, name TEXT)')
    return conn

@app.route('/manifest.json')
def manifest(): return Response('{"name":"TrackBiz Africa","short_name":"TrackBiz","start_url":"/","display":"standalone","background_color":"#0a0a0a","theme_color":"#ffcc00"}', mimetype='application/json')
@app.route('/sw.js')
def sw(): return Response("self.addEventListener('fetch',e=>{});", mimetype='application/javascript')
@app.route('/static/<path:p>')
def static_files(p): return send_from_directory('static', p)
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST' and request.form['pass']=='admin123':
        session['logged']=True; return redirect('/')
    return f'<body style="background:#0a0a0a;color:white;display:flex;align-items:center;justify-content:center;height:100vh;font-family:sans-serif"><form method="post" style="background:#1e1e1e;padding:30px;border-radius:20px;border:1px solid #ffcc00;text-align:center"><h2 style="color:#ffcc00">{BUSINESS_NAME}</h2><p>{BUSINESS_PHONE}</p><input name="pass" type="password" placeholder="admin123" style="padding:12px;width:100%;margin:10px 0;border-radius:10px"><button style="padding:12px;width:100%;background:#ffcc00;border:none;border-radius:10px;font-weight:bold">Login</button></form></body>'
@app.route('/logout')
def logout(): session.clear(); return redirect('/login')
@app.route('/')
def home():
    if not session.get('logged'): return redirect('/login')
    conn=get_db(); sales=conn.execute('SELECT * FROM sales ORDER BY id DESC LIMIT 100').fetchall(); stock=conn.execute('SELECT * FROM stock').fetchall(); debts=conn.execute('SELECT * FROM debts WHERE paid=0').fetchall()
    total_sales=sum([s[2] for s in sales]) if sales else 0; total_profit=sum([s[4] for s in sales]) if sales else 0; total_stock_value=sum([s[1]*s[2] for s in stock]) if stock else 0; total_debt=sum([d[3] for d in debts]) if debts else 0
    top_item={};
    for s in sales: top_item[s[1]]=top_item.get(s[1],0)+s[4]
    best_seller=max(top_item, key=top_item.get) if top_item else "None"; advice=f"Sell more {best_seller}" if best_seller!="None" else "Start selling"
    low_stock=[s for s in stock if s[1]<5]; dates={}
    for s in sales:
        try: d=s[6].split()[0]; dates[d]=dates.get(d,0)+s[2]
        except: pass
    chart_labels=list(dates.keys())[-7:]; chart_data=[dates[k] for k in chart_labels]; conn.close()
    return render_template('index.html', sales=sales, stock=stock, debts=debts, total_sales=total_sales, total_profit=total_profit, total_debt=total_debt, total_stock_value=total_stock_value, best_seller=best_seller, advice=advice, low_stock=low_stock, chart_labels=chart_labels, chart_data=chart_data, biz_name=BUSINESS_NAME, biz_phone=BUSINESS_PHONE)
@app.route('/sell', methods=['POST'])
def sell():
    conn=get_db(); item=request.form['item']; sell_price=int(request.form['sell_price']); method=request.form['method']; customer=request.form.get('customer','Walk-in')
    row=conn.execute('SELECT buy_price, qty FROM stock WHERE item=?',(item,)).fetchone(); buy_price=row[0] if row else int(request.form.get('buy_price',0))
    conn.execute('INSERT INTO sales (item,sell_price,buy_price,profit,method,date,customer) VALUES (?,?,?,?,?,?,?)',(item, sell_price, buy_price, sell_price-buy_price, method, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), customer))
    if row and row[1]>0: conn.execute('UPDATE stock SET qty=qty-1 WHERE item=?',(item,))
    conn.commit(); conn.close(); return redirect('/')
@app.route('/add_stock', methods=['POST'])
def add_stock():
    conn=get_db()
    conn.execute('INSERT OR REPLACE INTO stock (item, qty, buy_price, barcode, image) VALUES (?,?,?,?,?)',(request.form['item'], int(request.form['qty']), int(request.form['buy_price']), request.form.get('barcode',''), ''))
    if request.form.get('barcode'): conn.execute('INSERT OR REPLACE INTO barcodes VALUES (?,?)',(request.form.get('barcode'), request.form['item']))
    conn.commit(); conn.close(); return redirect('/')
@app.route('/add_debt', methods=['POST'])
def add_debt(): conn=get_db(); conn.execute('INSERT INTO debts (customer,item,amount,date) VALUES (?,?,?,?)',(request.form['customer'],request.form['item'],int(request.form['amount']), datetime.datetime.now().strftime("%Y-%m-%d"))); conn.commit(); conn.close(); return redirect('/')
@app.route('/pay_debt/<int:id>')
def pay_debt(id): conn=get_db(); conn.execute('UPDATE debts SET paid=1 WHERE id=?',(id,)); conn.commit(); conn.close(); return redirect('/')
@app.route('/delete_sale/<int:id>')
def delete_sale(id): conn=get_db(); conn.execute('DELETE FROM sales WHERE id=?',(id,)); conn.commit(); conn.close(); return redirect('/')
@app.route('/edit_sale/<int:id>', methods=['GET','POST'])
def edit_sale(id):
    conn=get_db()
    if request.method=='POST':
        row=conn.execute('SELECT buy_price FROM sales WHERE id=?',(id,)).fetchone(); buy=row[0] if row else 0
        conn.execute('UPDATE sales SET item=?, sell_price=?, profit=?, method=? WHERE id=?',(request.form['item'], int(request.form['sell_price']), int(request.form['sell_price'])-buy, request.form['method'], id)); conn.commit(); conn.close(); return redirect('/')
    s=conn.execute('SELECT * FROM sales WHERE id=?',(id,)).fetchone(); conn.close()
    return f'<body style="background:#0a0a0a;color:white;padding:20px"><div style="background:#1e1e1e;padding:20px;border-radius:16px;max-width:400px;margin:auto"><h3>Edit Sale #{id}</h3><form method="post"><input name="item" value="{s[1]}" style="width:100%;padding:12px;margin:6px 0;border-radius:10px" required><input name="sell_price" type="number" value="{s[2]}" style="width:100%;padding:12px" required><select name="method" style="width:100%;padding:12px"><option>{s[5]}</option><option>Cash</option><option>MTN</option><option>AIRTEL</option></select><button style="background:#ffcc00;padding:12px;width:100%;border-radius:10px;margin-top:10px">Update</button></form></div></body>'
@app.route('/delete_stock/<item>')
def delete_stock(item): conn=get_db(); conn.execute('DELETE FROM stock WHERE item=?',(item,)); conn.commit(); conn.close(); return redirect('/')
@app.route('/edit_stock/<item>', methods=['GET','POST'])
def edit_stock(item):
    conn=get_db()
    if request.method=='POST': conn.execute('UPDATE stock SET qty=?, buy_price=? WHERE item=?',(int(request.form['qty']), int(request.form['buy_price']), item)); conn.commit(); conn.close(); return redirect('/')
    s=conn.execute('SELECT * FROM stock WHERE item=?',(item,)).fetchone(); conn.close()
    return f'<body style="background:#0a0a0a;color:white;padding:20px"><div style="background:#1e1e1e;padding:20px;border-radius:16px;max-width:400px;margin:auto"><h3>Edit {item}</h3><form method="post"><input name="qty" type="number" value="{s[1]}" style="width:100%;padding:12px" required><input name="buy_price" type="number" value="{s[2]}" style="width:100%;padding:12px" required><button style="background:#00d084;padding:12px;width:100%;border-radius:10px;margin-top:10px">Update</button></form></div></body>'
@app.route('/momo_pay', methods=['POST'])
def momo_pay():
    phone_raw=request.form['phone']; phone=phone_raw.replace("+","").replace(" ","");
    if phone.startswith("0"): phone="256"+phone[1:]
    amount=request.form['amount']; network=request.form['network']; item=request.form['item']; conn=get_db(); date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    conn.execute('INSERT INTO sales (item,sell_price,buy_price,profit,method,date,customer) VALUES (?,?,?,?,?,?,?)',(f"{item} ({network} {phone_raw})", int(amount), 0, int(amount), f"{network}-MANUAL", date, phone_raw)); conn.commit(); conn.close()
    return f'<body style="background:#0a0a0a;color:white;text-align:center;padding:20px"><div style="background:#1e1e1e;padding:30px;border-radius:20px;max-width:400px;margin:auto"><h2>{network} {amount} UGX</h2><p>MANUAL - Tell customer *165*3# or *185*9#</p><br><a href="/" style="background:#00d084;padding:12px 20px;border-radius:10px;text-decoration:none;color:black;font-weight:bold">Back</a></div></body>'
@app.route('/export')
def export():
    conn=get_db(); sales=conn.execute('SELECT * FROM sales').fetchall(); conn.close(); out=io.StringIO(); w=csv.writer(out); w.writerow(['Item','Sell','Profit','Method','Date','Customer']); w.writerows([(s[1],s[2],s[4],s[5],s[6],s[7]) for s in sales]); return Response(out.getvalue(), mimetype='text/csv', headers={"Content-Disposition":f"attachment;filename={BUSINESS_NAME}_Report.csv"})
@app.route('/receipt/<int:id>')
def receipt(id):
    conn=get_db(); s=conn.execute('SELECT * FROM sales WHERE id=?',(id,)).fetchone(); conn.close()
    if not s: return "Not found"
    if request.args.get('download')=="txt": return Response(f"{BUSINESS_NAME}\nPhone: {BUSINESS_PHONE}\nReceipt BIZ-{s[0]:05d}\nItem: {s[1]}\nPrice: {s[2]} UGX", mimetype='text/plain', headers={"Content-Disposition": f"attachment;filename=receipt_{s[0]}.txt"})
    logo_exists = os.path.exists('static/logo.png'); logo_html = '<img src="/static/logo.png" style="width:90px;height:90px;object-fit:contain;border-radius:14px;margin-bottom:10px;border:2px solid #ffcc00">' if logo_exists else '<div style="width:80px;height:80px;background:linear-gradient(135deg,#ffcc00,#ff8800);border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:32px;color:#000;margin:0 auto 10px auto">T</div>'
    return f"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script><style>body{{background:#ddd;display:flex;justify-content:center;padding:20px;font-family:monospace}}#receipt{{background:white;width:360px;padding:22px;border-radius:14px}}.center{{text-align:center}}.line{{border-top:1px dashed #000;margin:12px 0}}.btn{{width:100%;padding:12px;margin:6px 0;border-radius:10px;border:none;font-weight:bold}}@media print{{.btn,a{{display:none}}}}</style></head><body><div><div id="receipt"><div class="center">{logo_html}<h2>{BUSINESS_NAME}</h2><p>Tel: {BUSINESS_PHONE}<br>Kampala</p></div><div class="line"></div><p>Receipt: BIZ-{s[0]:05d}<br>Date: {s[6]}<br>Customer: {s[7]}</p><div class="line"></div><p>Item: <b>{s[1]}</b><br>Total: <b>{s[2]} UGX</b><br>Method: {s[5]}</p><div class="line"></div><p class="center">Thank you!</p></div><button class="btn" style="background:#ffcc00" onclick="window.print()">🖨️ PRINT</button><button class="btn" style="background:#00d084;color:white" onclick="html2canvas(document.getElementById('receipt'),{{scale:3}}).then(c=>{{let a=document.createElement('a'); a.download='Receipt_{s[0]}.png'; a.href=c.toDataURL(); a.click();}})">⬇️ DOWNLOAD PNG</button><button class="btn" style="background:#111;color:white" onclick="location.href='/receipt/{s[0]}?download=txt'">📄 DOWNLOAD TXT</button><button class="btn" style="background:#25D366;color:white" onclick="window.open('https://wa.me/?text=Receipt BIZ-{s[0]:05d} {s[1]} {s[2]} UGX','_blank')">📲 SHARE WHATSAPP</button><a href="/" style="display:block;text-align:center;margin-top:10px">← Back</a></div></body></html>"""
if __name__=='__main__': app.run(host='0.0.0.0', port=5000, debug=True)
