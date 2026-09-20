from flask import Flask, render_template, request, redirect, session, Response, send_from_directory
import sqlite3, datetime, csv, io, os

app = Flask(__name__)
app.secret_key = "africa_best_final"

def get_db():
    conn = sqlite3.connect('database.db')
    conn.execute('CREATE TABLE IF NOT EXISTS stock (item TEXT PRIMARY KEY, qty INTEGER, buy_price INTEGER, barcode TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, item TEXT, sell_price INTEGER, buy_price INTEGER, profit INTEGER, method TEXT, date TEXT, customer TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS debts (id INTEGER PRIMARY KEY, customer TEXT, item TEXT, amount INTEGER, date TEXT, paid INTEGER DEFAULT 0)')
    conn.execute('CREATE TABLE IF NOT EXISTS barcodes (barcode TEXT PRIMARY KEY, name TEXT)')
    # Auto-migrate old database
    try: conn.execute('ALTER TABLE stock ADD COLUMN barcode TEXT')
    except: pass
    try: conn.execute('ALTER TABLE sales ADD COLUMN customer TEXT')
    except: pass
    return conn

@app.route('/manifest.json')
def manifest():
    if os.path.exists('static/manifest.json'): return send_from_directory('static','manifest.json')
    return Response('{"name":"BizTrack Africa","short_name":"BizTrack","start_url":"/","display":"standalone","background_color":"#0a0a0a","theme_color":"#ffcc00"}', mimetype='application/json')

@app.route('/sw.js')
def sw():
    return Response("self.addEventListener('fetch',e=>{})", mimetype='application/javascript')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST' and request.form.get('pass')=='admin123':
        session['logged']=True
        return redirect('/')
    try: return render_template('login.html')
    except: return '''<body style="background:#0a0a0a;display:flex;justify-content:center;align-items:center;height:100vh;font-family:sans-serif"><div style="background:#1e1e1e;padding:30px;border-radius:16px;border:1px solid #ffcc00;width:90%;max-width:320px;text-align:center"><h2 style="color:#ffcc00">BizTrack Africa</h2><p style="color:#888">admin123</p><form method="post"><input name="pass" type="password" placeholder="Password" style="width:100%;padding:12px;border-radius:10px;border:1px solid #333;background:#222;color:#fff"><button style="background:#ffcc00;width:100%;padding:12px;border-radius:10px;font-weight:bold;margin-top:10px;border:none">Login</button></form></div></body>'''

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/')
def home():
    if not session.get('logged'): return redirect('/login')
    conn=get_db()
    sales=conn.execute('SELECT * FROM sales ORDER BY id DESC LIMIT 100').fetchall()
    stock=conn.execute('SELECT * FROM stock').fetchall()
    debts=conn.execute('SELECT * FROM debts WHERE paid=0').fetchall()
    total_sales=sum([s[2] for s in sales]) if sales else 0
    total_profit=sum([s[4] for s in sales]) if sales else 0
    total_stock_value=sum([s[1]*s[2] for s in stock]) if stock else 0
    total_debt=sum([d[3] for d in debts]) if debts else 0
    dates={}
    for s in sales:
        try: d=s[6].split()[0]; dates[d]=dates.get(d,0)+s[2]
        except: pass
    chart_labels=list(dates.keys())[-7:]
    chart_data=[dates[k] for k in chart_labels]
    top={}
    for s in sales: top[s[1]]=top.get(s[1],0)+s[4]
    best_seller=max(top, key=top.get) if top else "None yet"
    advice=f"Focus on {best_seller} - highest profit!" if best_seller!="None yet" else "Start selling to get AI advice"
    low_stock=[s for s in stock if s[1]<5]
    conn.close()
    return render_template('index.html', sales=sales, stock=stock, debts=debts, total_sales=total_sales, total_profit=total_profit, total_debt=total_debt, total_stock_value=total_stock_value, best_seller=best_seller, advice=advice, low_stock=low_stock, chart_labels=chart_labels, chart_data=chart_data)

@app.route('/sell', methods=['POST'])
def sell():
    conn=get_db()
    item=request.form['item']; sell_price=int(request.form['sell_price']); method=request.form['method']; customer=request.form.get('customer','Walk-in')
    row=conn.execute('SELECT buy_price, qty FROM stock WHERE item=?',(item,)).fetchone()
    buy_price=row[0] if row else int(request.form.get('buy_price',0) or 0)
    conn.execute('INSERT INTO sales (item,sell_price,buy_price,profit,method,date,customer) VALUES (?,?,?,?,?,?,?)',(item,sell_price,buy_price,sell_price-buy_price,method,datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),customer))
    if row and row[1]>0: conn.execute('UPDATE stock SET qty=qty-1 WHERE item=?',(item,))
    conn.commit(); conn.close(); return redirect('/')

@app.route('/add_stock', methods=['POST'])
def add_stock():
    conn=get_db()
    conn.execute('INSERT OR REPLACE INTO stock VALUES (?,?,?,?)',(request.form['item'], int(request.form['qty']), int(request.form['buy_price']), request.form.get('barcode','')))
    if request.form.get('barcode'): conn.execute('INSERT OR REPLACE INTO barcodes VALUES (?,?)',(request.form.get('barcode'), request.form['item']))
    conn.commit(); conn.close(); return redirect('/')

@app.route('/add_debt', methods=['POST'])
def add_debt():
    conn=get_db(); conn.execute('INSERT INTO debts (customer,item,amount,date) VALUES (?,?,?,?)',(request.form['customer'],request.form['item'],int(request.form['amount']),datetime.datetime.now().strftime("%Y-%m-%d"))); conn.commit(); conn.close(); return redirect('/')

@app.route('/pay_debt/<int:id>')
def pay_debt(id): conn=get_db(); conn.execute('UPDATE debts SET paid=1 WHERE id=?',(id,)); conn.commit(); conn.close(); return redirect('/')

@app.route('/momo_pay', methods=['POST'])
def momo_pay():
    conn=get_db(); conn.execute('INSERT INTO sales (item,sell_price,buy_price,profit,method,date,customer) VALUES (?,?,?,?,?,?,?)',(f"{request.form['item']} ({request.form['network']} {request.form['phone']})",int(request.form['amount']),0,int(request.form['amount']),request.form['network'],datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),request.form['phone'])); conn.commit(); conn.close()
    return f"<script>alert('✓ {request.form['network']} {request.form['amount']} UGX Recorded!'); location.href='/'</script>"

@app.route('/export')
def export_csv():
    conn=get_db(); sales=conn.execute('SELECT * FROM sales').fetchall(); conn.close()
    out=io.StringIO(); w=csv.writer(out); w.writerow(['Item','Sell','Profit','Method','Date','Customer']); w.writerows([(s[1],s[2],s[4],s[5],s[6],s[7]) for s in sales])
    return Response(out.getvalue(), mimetype='text/csv', headers={"Content-Disposition":"attachment;filename=BizTrack_Africa.csv"})

@app.route('/receipt/<int:id>')
def receipt(id):
    conn=get_db(); s=conn.execute('SELECT * FROM sales WHERE id=?',(id,)).fetchone(); conn.close()
    if not s: return "Not found"
    return f"<div style='font-family:monospace;padding:20px;max-width:300px;margin:auto'><h2>BizTrack Africa</h2><p>Item: {s[1]}<br>Price: {s[2]} UGX<br>Method: {s[5]}<br>Date: {s[6]}<br>Customer: {s[7] if len(s)>7 else 'Walk-in'}<br><br>Webale nyo!</p><button onclick='window.print()'>Print</button> <a href='/'>Home</a></div>"

if __name__=='__main__':
    import os
    port=int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
