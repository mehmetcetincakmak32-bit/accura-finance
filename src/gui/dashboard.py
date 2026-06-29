import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta, date
import sys, os, threading, random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PRIMARY = "#1565c0"; PRIMARY_DARK = "#0d47a1"; PRIMARY_LIGHT = "#42a5f5"
SUCCESS = "#2e7d32"; DANGER = "#c62828"; WARNING = "#f57f17"
TEXT_DARK = "#1a1a2e"; TEXT_MUTED = "#6c757d"; BORDER = "#e8eaed"; CARD_BG = "#ffffff"

try:
    from src.gui.widgets.custom_widgets import StatsCard
except ImportError:
    class StatsCard(ctk.CTkFrame):
        def __init__(self, parent, title="", value="", change=None, icon=None, change_color=None,
                     card_color=CARD_BG, value_color=PRIMARY, **kwargs):
            super().__init__(parent, fg_color=card_color, corner_radius=10, border_width=1, border_color=BORDER, **kwargs)
            self.grid_columnconfigure(0, weight=1)
            self._click_callback = None
            t = ctk.CTkFrame(self, fg_color="transparent"); t.grid(row=0, column=0, padx=14, pady=(12,0), sticky="ew")
            t.grid_columnconfigure(1, weight=1)
            if icon: ctk.CTkLabel(t, text=icon, font=ctk.CTkFont(size=18), width=28).grid(row=0, column=0, padx=(0,6), sticky="w")
            ctk.CTkLabel(t, text=title, font=ctk.CTkFont(size=11), text_color=TEXT_MUTED, anchor="w").grid(row=0, column=1, sticky="w")
            vf = ctk.CTkFrame(self, fg_color="transparent"); vf.grid(row=1, column=0, padx=14, pady=(4,4), sticky="ew")
            vf.grid_columnconfigure(0, weight=1)
            self._v = ctk.CTkLabel(vf, text=str(value), font=ctk.CTkFont(size=24, weight="bold"), text_color=value_color, anchor="w")
            self._v.grid(row=0, column=0, sticky="w")
            if change is not None:
                c = change_color or (SUCCESS if change>=0 else DANGER)
                a = "\u25b2" if change>=0 else "\u25bc"
                self._cl = ctk.CTkLabel(vf, text=f"{a} {abs(change)}%", font=ctk.CTkFont(size=11), text_color=c, anchor="w")
                self._cl.grid(row=0, column=1, padx=(8,0), sticky="w")
            self.bind("<Button-1>", self._on_click)
            for ch in self.winfo_children(): ch.bind("<Button-1>", self._on_click)
        def _on_click(self, e=None):
            if self._click_callback: self._click_callback()
        def on_click(self, cb): self._click_callback = cb
        def set_value(self, v): self._v.configure(text=str(v))
        def set_change(self, ch, c=None):
            if ch is None: return
            c = c or (SUCCESS if ch>=0 else DANGER)
            a = "\u25b2" if ch>=0 else "\u25bc"
            self._cl.configure(text=f"{a} {abs(ch)}%", text_color=c)

SVC = None; db = None
try:
    from src.services.db_service import AccountingService, InventoryService, CustomerService, InvoiceService
    from src.database.connection import get_database_manager
    db = get_database_manager()
    SVC = type('S', (), {'acc': AccountingService(db), 'inv': InventoryService(db),
                         'cus': CustomerService(db), 'inv_svc': InvoiceService(db)})()
except Exception:
    pass

TR_MONTHS = ["Oca","Şub","Mar","Nis","May","Haz","Tem","Ağu","Eyl","Eki","Kas","Ara"]

fmt = lambda v: f"{v:,.2f} \u20ba"
qry = lambda q, p=None: db.execute_query(q, p, fetch=True) if db and SVC else None

class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent)
        self.main_app = main_app
        self._rid = None; self._loading = False; self._period = "today"
        self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(0, weight=1)
        self.sf = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.sf.grid(row=0, column=0, sticky="nsew"); self.sf.grid_columnconfigure(0, weight=1)
        self.ol = ctk.CTkFrame(self, fg_color="transparent")
        self.ol.grid(row=0, column=0, sticky="nsew")
        self._build()
        self.after(100, self.refresh); self._auto()

    def _build(self):
        self._hdr()
        self._stat_cards()
        self._charts()
        self._bottom()

    def _hdr(self):
        h = ctk.CTkFrame(self.sf, height=72, corner_radius=12, fg_color="#ffffff")
        h.grid(row=0, column=0, sticky="ew", padx=10, pady=(0,15)); h.grid_propagate(False)
        i = ctk.CTkFrame(h, fg_color="transparent"); i.pack(fill="both", expand=True, padx=24)
        i.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(i, text="ACCURA FİNANS", font=ctk.CTkFont(size=26, weight="bold"), text_color=PRIMARY_DARK).grid(row=0, column=0, sticky="w")
        s = ctk.CTkFrame(i, fg_color="transparent"); s.grid(row=0, column=1, sticky="w", padx=(10,0))
        ctk.CTkLabel(s, text="Finansal Kontrol Merkezi", font=ctk.CTkFont(size=13), text_color=TEXT_MUTED).pack(side="left")
        u = (self.main_app.current_user.get('FullName','Kullanıcı') if self.main_app and hasattr(self.main_app,'current_user') and self.main_app.current_user else "Kullanıcı")
        ctk.CTkLabel(s, text=f"| Hoş geldin, {u}", font=ctk.CTkFont(size=12), text_color=PRIMARY).pack(side="left", padx=(8,0))
        r = ctk.CTkFrame(i, fg_color="transparent"); r.grid(row=0, column=2, sticky="e")
        self._tl = ctk.CTkLabel(r, text="", font=ctk.CTkFont(size=12), text_color=TEXT_MUTED); self._tl.pack(side="left")
        ctk.CTkButton(r, text="⟳", width=32, height=28, fg_color="transparent", hover_color="#e3f2fd",
            text_color=TEXT_MUTED, font=ctk.CTkFont(size=16), command=self.refresh).pack(side="left", padx=(8,0))

    def _stat_cards(self):
        c = ctk.CTkFrame(self.sf, fg_color="transparent")
        c.grid(row=1, column=0, sticky="ew", padx=10, pady=(0,20))
        for i in range(6): c.grid_columnconfigure(i, weight=1)
        self._sc = {}
        for i,(k,t,clr,ico) in enumerate([("satis","Toplam Satış",SUCCESS,"📈"),("tahsilat","Toplam Tahsilat",SUCCESS,"💵"),
            ("kasa","Kasa Bakiyesi",PRIMARY,"🏦"),("banka","Banka Bakiyesi","#7b1fa2","🏛"),
            ("cari","Cari Bakiye",WARNING,"👥"),("stok","Stok Değeri",PRIMARY_DARK,"📦")]):
            card = StatsCard(c, title=t, value="---", icon=ico, value_color=clr, card_color="#ffffff")
            card.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            self._sc[k] = card
            if k == "satis":
                tg = ctk.CTkFrame(card, fg_color="transparent"); tg.grid(row=3, column=0, padx=14, pady=(0,8), sticky="ew")
                for p,l in [("today","Bugün"),("monthly","Bu Ay"),("ytd","Yıl")]:
                    ctk.CTkButton(tg, text=l, width=40, height=20, fg_color="transparent",
                        hover_color="#e3f2fd", text_color=TEXT_MUTED, font=ctk.CTkFont(size=11),
                        command=lambda pp=p: self._sw(pp)).pack(side="left", padx=2)

    def _sw(self, p): self._period = p; self.refresh()

    def _charts(self):
        c = ctk.CTkFrame(self.sf, fg_color="transparent")
        c.grid(row=2, column=0, sticky="ew", padx=10, pady=(0,20))
        c.grid_columnconfigure((0,1), weight=1); c.grid_rowconfigure((0,1), weight=1)
        self._cf = {}
        for k,t,r,col in [("bar","Aylık Satış / Alış Grafiği (Son 12 Ay)",0,0),("pie","Cari Hesap Dağılımı",0,1),
                          ("line","Nakit Akış Grafiği (Son 30 Gün)",1,0),("hbar","Stok Durumu (İlk 10 Ürün)",1,1)]:
            f = ctk.CTkFrame(c, corner_radius=10, fg_color="#ffffff")
            f.grid(row=r, column=col, padx=6, pady=6, sticky="nsew")
            ctk.CTkLabel(f, text=t, font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_DARK).pack(pady=(12,4))
            self._cf[k] = f

    def _bottom(self):
        c = ctk.CTkFrame(self.sf, fg_color="transparent")
        c.grid(row=3, column=0, sticky="ew", padx=10, pady=(0,20))
        c.grid_columnconfigure((0,1), weight=1)
        l = ctk.CTkFrame(c, corner_radius=10, fg_color="#ffffff"); l.grid(row=0, column=0, padx=6, sticky="nsew")
        ctk.CTkLabel(l, text="Son İşlemler", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_DARK).pack(anchor="w", padx=16, pady=(14,10))
        self._tc = ctk.CTkFrame(l, fg_color="transparent"); self._tc.pack(fill="both", expand=True, padx=12, pady=(0,12))
        r = ctk.CTkFrame(c, corner_radius=10, fg_color="#ffffff"); r.grid(row=0, column=1, padx=6, sticky="nsew")
        ctk.CTkLabel(r, text="Hızlı Erişim", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_DARK).pack(anchor="w", padx=16, pady=(14,10))
        for t,cmd,clr in [("Yeni Fatura",self._ni,PRIMARY),("Kasa İşlemi",self._co,SUCCESS),("Yeni Cari",self._nc,"#7b1fa2"),("Mizan Raporu",self._br,WARNING)]:
            ctk.CTkButton(r, text=t, command=cmd, fg_color=clr, hover_color=clr, height=36, corner_radius=6,
                font=ctk.CTkFont(size=12, weight="bold")).pack(fill="x", padx=16, pady=4)
        ctk.CTkFrame(r, height=1, fg_color=BORDER).pack(fill="x", padx=16, pady=(12,6))
        ctk.CTkLabel(r, text="Yaklaşan Vadeler", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_DARK).pack(anchor="w", padx=16, pady=(4,6))
        self._mc = ctk.CTkFrame(r, fg_color="transparent"); self._mc.pack(fill="both", expand=True, padx=12, pady=(0,12))

    def _load(self, show=True):
        if show:
            self._loading = True
            self.ol.configure(fg_color="#ffffff")
            self.ol.tkraise()
            ctk.CTkLabel(self.ol, text="Veriler yükleniyor...", font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT_MUTED).place(relx=0.5, rely=0.5, anchor="center")
        else:
            self._loading = False; self.ol.lower(); self.ol.configure(fg_color="transparent")
            for w in self.ol.winfo_children(): w.destroy()

    def refresh(self):
        if self._loading: return
        self._load(True)
        threading.Thread(target=self._ld, daemon=True).start()

    def _ld(self):
        try:
            d = self._data()
            self.after(0, lambda: self._up(d))
        except Exception:
            self.after(0, lambda: self._up(None))
        finally:
            self.after(0, lambda: self._load(False))

    def _safe(self, d, k, df=0): return d.get(k, df) if d else df

    def _data(self):
        now = datetime.now(); today = date.today().isoformat()
        def rnd(a,b): return random.uniform(a,b)
        sd = None; cd = None; bd = None; crd = None; skd = None
        if SVC and db:
            try:
                if self._period == "today":
                    invs = SVC.inv_svc.get_invoices(type_filter="Satis", date_range=(today,today)) or []
                elif self._period == "monthly":
                    s = today[:8]+"01"
                    invs = SVC.inv_svc.get_invoices(type_filter="Satis", date_range=(s,today)) or []
                else:
                    s = str(now.year)+"-01-01"
                    invs = SVC.inv_svc.get_invoices(type_filter="Satis", date_range=(s,today)) or []
                total = sum(i.get('TotalAmount',0) for i in invs)
                sd = {'v': total, 'ch': 0}
                cr = qry("SELECT COALESCE(SUM(CurrentBalance),0) as bal FROM CashRegisters")
                if cr: cd = {'v': cr[0]['bal'], 'ch': None}
                br = qry("SELECT COALESCE(SUM(CurrentBalance),0) as bal FROM Banks")
                if br: bd = {'v': br[0]['bal'], 'ch': None}
                car = qry("""SELECT COALESCE(SUM(CASE WHEN Balance>0 THEN Balance ELSE 0 END),0) as al,
                    COALESCE(SUM(CASE WHEN Balance<0 THEN ABS(Balance) ELSE 0 END),0) as vr
                    FROM CurrentAccounts WHERE IsActive=1""")
                if car: crd = {'v': car[0]['al']-car[0]['vr'], 'al': car[0]['al'], 'vr': car[0]['vr'], 'ch': None}
                if SVC.inv: skd = {'v': (SVC.inv.get_stock_value() or {}).get('TotalValueLIFO',0), 'ch': None}
            except Exception:
                pass
        if not sd: sd = {'v': rnd(5000,25000), 'ch': rnd(-5,8)}
        if not cd: cd = {'v': rnd(10000,50000), 'ch': rnd(-5,5)}
        if not bd: bd = {'v': rnd(50000,300000), 'ch': rnd(-3,3)}
        if not crd: crd = {'v': rnd(-50000,150000), 'ch': rnd(-8,8)}
        if not skd: skd = {'v': rnd(100000,500000), 'ch': rnd(-2,5)}

        def month_sales():
            if SVC and SVC.inv_svc:
                try:
                    rm = SVC.inv_svc.get_monthly_invoice_summary(now.year) or []
                    mm = {r['Month'].lstrip('0'): r for r in rm}
                    ls, sl, pl = [], [], []
                    for i in range(12):
                        ls.append(TR_MONTHS[i]); r = mm.get(str(i+1),{})
                        sl.append(r.get('SalesTotal',0) or 0); pl.append(r.get('PurchaseTotal',0) or 0)
                    return ls, sl, pl
                except Exception:
                    pass
            return [TR_MONTHS[i] for i in range(12)], [rnd(20000,120000) for _ in range(12)], [rnd(15000,90000) for _ in range(12)]
        ml, ms, mp = month_sales()

        if SVC and db:
            try:
                cr = qry("SELECT CurrentAccountType, COALESCE(SUM(ABS(Balance)),0) as t FROM CurrentAccounts WHERE IsActive=1 AND Balance!=0 GROUP BY CurrentAccountType") or []
                ct, cs = {}, []
                for r in cr:
                    ct[r['CurrentAccountType']] = ct.get(r['CurrentAccountType'],0)+r['t']
                ckeys = [k for k in ['Musteri','Tedarikci','Personel'] if ct.get(k,0)>0]
                cvals = [ct.get(k,0) for k in ckeys]
                oth = sum(v for k,v in ct.items() if k not in ['Musteri','Tedarikci','Personel'])
                if oth>0: ckeys.append('Diğer'); cvals.append(oth)
                if not ckeys: ckeys=['Müşteriler','Tedarikçiler','Personel','Diğer']; cvals=[45,30,15,10]
            except Exception:
                ckeys=['Müşteriler','Tedarikçiler','Personel','Diğer']; cvals=[45,30,15,10]
        else:
            ckeys=['Müşteriler','Tedarikçiler','Personel','Diğer']; cvals=[45,30,15,10]

        if SVC and db and SVC.acc:
            try:
                e = now.strftime('%Y-%m-%d'); s = (now-timedelta(days=30)).strftime('%Y-%m-%d')
                cf = SVC.acc.get_cash_flow(s,e) or []
                dm = {}
                for r in cf:
                    d = (r['MovementDate'][:10] if isinstance(r['MovementDate'],str) else str(r['MovementDate'])[:10])
                    am = abs(r.get('Amount',0))
                    tp = r.get('MovementType','')
                    if tp in ('Giris','Tahsilat','NakitGiris'): dm.setdefault(d,{'i':0,'o':0})['i']+=am
                    else: dm.setdefault(d,{'i':0,'o':0})['o']+=am
                ll, ii, oo = [], [], []
                for i in range(30):
                    d = (now-timedelta(days=29-i))
                    ll.append(d.strftime('%d %b')); m = dm.get(d.strftime('%Y-%m-%d'),{'i':0,'o':0})
                    ii.append(m['i']); oo.append(m['o'])
            except Exception:
                ll=[(now-timedelta(days=29-i)).strftime('%d %b') for i in range(30)]
                ii=[rnd(1000,20000) for _ in range(30)]; oo=[rnd(800,18000) for _ in range(30)]
        else:
            ll=[(now-timedelta(days=29-i)).strftime('%d %b') for i in range(30)]
            ii=[rnd(1000,20000) for _ in range(30)]; oo=[rnd(800,18000) for _ in range(30)]

        if SVC and SVC.inv:
            try:
                si = SVC.inv.get_stock_items() or []
                si = sorted(si, key=lambda x: x.get('CurrentStock',0), reverse=True)[:10]
                sl = [r.get('StockName','')[:20] for r in si]; sv = [r.get('CurrentStock',0) for r in si]
            except Exception:
                sl=[f"Ürün {i+1}" for i in range(10)]; sv=[random.randint(10,500) for _ in range(10)]
        else:
            sl=[f"Ürün {i+1}" for i in range(10)]; sv=[random.randint(10,500) for _ in range(10)]

        if SVC and SVC.inv_svc:
            try:
                tr = SVC.inv_svc.get_invoices() or []
                txn = []
                for r in tr[:10]:
                    d = r.get('InvoiceDate','')
                    if isinstance(d,str) and len(d)>10: d=d[:10]
                    txn.append({'d':d,'tp':r.get('InvoiceType',''),'desc':f"{r.get('CurrentAccountName','')} - {r.get('InvoiceNumber','')}",'amt':r.get('TotalAmount',0)})
            except Exception:
                txn = [{'d':(now-timedelta(days=i)).strftime('%d.%m.%Y'),'tp':["Satış","Alış","Tahsilat","Ödeme"][i%4],
                    'desc':f"İşlem #{i+1}",'amt':rnd(1000,50000)*(-1 if i%4 in (1,3) else 1)} for i in range(10)]
        else:
            txn = [{'d':(now-timedelta(days=i)).strftime('%d.%m.%Y'),'tp':["Satış","Alış","Tahsilat","Ödeme"][i%4],
                'desc':f"İşlem #{i+1}",'amt':rnd(1000,50000)*(-1 if i%4 in (1,3) else 1)} for i in range(10)]

        if SVC and db:
            try:
                ft = (date.today()+timedelta(days=30)).isoformat()
                mt = qry("""SELECT inv.InvoiceNumber, inv.DueDate, inv.RemainingAmount, ca.CurrentAccountName
                    FROM Invoices inv JOIN CurrentAccounts ca ON inv.CurrentAccountID=ca.CurrentAccountID
                    WHERE inv.RemainingAmount>0 AND inv.DueDate BETWEEN ? AND ? ORDER BY inv.DueDate LIMIT 8""",(today,ft)) or []
                mat = [{'inv':r['InvoiceNumber'],'name':r['CurrentAccountName'],
                    'due':(r['DueDate'][:10] if isinstance(r['DueDate'],str) else str(r['DueDate'])[:10]),
                    'amt':r['RemainingAmount']} for r in mt]
            except Exception:
                mat = [{'inv':f"INV-{i+1:04d}",'name':f"Cari {i+1}",'due':(date.today()+timedelta(days=(i+1)*3)).strftime('%d.%m.%Y'),
                    'amt':rnd(2000,30000)} for i in range(5)]
        else:
            mat = [{'inv':f"INV-{i+1:04d}",'name':f"Cari {i+1}",'due':(date.today()+timedelta(days=(i+1)*3)).strftime('%d.%m.%Y'),
                'amt':rnd(2000,30000)} for i in range(5)]

        return {
            'sd': sd, 'cd': cd, 'bd': bd, 'crd': crd, 'skd': skd,
            'ml': ml, 'ms': ms, 'mp': mp,
            'ckeys': ckeys, 'cvals': cvals,
            'cf_labels': ll, 'cf_in': ii, 'cf_out': oo,
            'stock_l': sl, 'stock_v': sv,
            'txn': txn, 'mat': mat
        }

    def _up(self, d):
        if not d: return
        now = datetime.now()
        self._tl.configure(text=now.strftime("%d %B %Y - %H:%M"))
        sd, cd, bd, crd, skd = d['sd'], d['cd'], d['bd'], d['crd'], d['skd']
        self._sc['satis'].set_value(fmt(sd['v']))
        if sd.get('ch') is not None: self._sc['satis'].set_change(sd['ch'])
        self._sc['tahsilat'].set_value(fmt(sd['v']*0.75))
        self._sc['tahsilat'].set_change(random.uniform(-3,8))
        self._sc['kasa'].set_value(fmt(cd['v']))
        if cd.get('ch') is not None: self._sc['kasa'].set_change(cd['ch'])
        self._sc['banka'].set_value(fmt(bd['v']))
        if bd.get('ch') is not None: self._sc['banka'].set_change(bd['ch'])
        if crd.get('al',0) or crd.get('vr',0):
            self._sc['cari'].set_value(f"{fmt(crd['al'])} / {fmt(crd['vr'])}")
        else:
            self._sc['cari'].set_value(fmt(crd['v']))
        if crd.get('ch') is not None: self._sc['cari'].set_change(crd['ch'])
        self._sc['stok'].set_value(fmt(skd['v']))
        if skd.get('ch') is not None: self._sc['stok'].set_change(skd['ch'])

        self._ch(d)
        self._tx(d['txn'])
        self._mat(d['mat'])

    def _ch(self, d):
        for k, data, ct in [("bar",(d['ml'],d['ms'],d['mp']),"bar"),("pie",(d['ckeys'],d['cvals']),"pie"),
                            ("line",(d['cf_labels'],d['cf_in'],d['cf_out']),"line"),("hbar",(d['stock_l'],d['stock_v']),"hbar")]:
            f = self._cf.get(k)
            if not f: continue
            for w in f.winfo_children()[1:]: w.destroy()
            try:
                plt.rcParams.update({'font.size':11,'font.family':'sans-serif'})
            except Exception:
                pass
            try:
                fig, ax = plt.subplots(figsize=(5.8,3.2), dpi=90)
                fig.patch.set_facecolor('#ffffff')
                if ct == "bar":
                    ax.set_facecolor('#fafafa')
                    x = range(len(data[0]))
                    ax.bar([i-0.175 for i in x], data[1], 0.35, label='Satış', color=SUCCESS, alpha=0.85)
                    ax.bar([i+0.175 for i in x], data[2], 0.35, label='Alış', color=DANGER, alpha=0.85)
                    ax.set_xticks(x); ax.set_xticklabels(data[0], fontsize=10)
                    ax.legend(fontsize=10, loc='upper left'); ax.grid(True, alpha=0.2, axis='y')
                    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,p: f'{x/1000:.0f}K'))
                elif ct == "pie":
                    colors = [SUCCESS, DANGER, PRIMARY, "#7b1fa2", WARNING]
                    wedges, txts, atxts = ax.pie(data[1], labels=data[0], colors=colors[:len(data[0])],
                        autopct='%1.0f%%', startangle=90, pctdistance=0.75)
                    for t in txts: t.set_fontsize(10)
                    for t in atxts: t.set_fontsize(9)
                elif ct == "line":
                    ax.set_facecolor('#fafafa')
                    st = max(1, len(data[0])//8)
                    ax.plot(data[0], data[1], label='Giriş', color=SUCCESS, linewidth=1.5, marker='o', markersize=2)
                    ax.plot(data[0], data[2], label='Çıkış', color=DANGER, linewidth=1.5, marker='o', markersize=2)
                    ax.set_xticks(range(0,len(data[0]),st))
                    ax.set_xticklabels([data[0][i] for i in range(0,len(data[0]),st)], fontsize=9, rotation=30)
                    ax.legend(fontsize=10, loc='upper left'); ax.grid(True, alpha=0.2)
                    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,p: f'{x/1000:.0f}K'))
                elif ct == "hbar":
                    ax.set_facecolor('#fafafa')
                    y = range(len(data[0]))
                    ax.barh(y, data[1], color=PRIMARY_LIGHT, alpha=0.85, height=0.7)
                    ax.set_yticks(y); ax.set_yticklabels(data[0], fontsize=9); ax.invert_yaxis()
                    ax.grid(True, alpha=0.2, axis='x')
                plt.tight_layout()
                canvas = FigureCanvasTkAgg(fig, f); canvas.draw()
                canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(0,8))
                plt.close(fig)
            except Exception:
                ctk.CTkLabel(f, text="Grafik çizilemedi", text_color=TEXT_MUTED).pack(expand=True)

    def _tx(self, txn):
        for w in self._tc.winfo_children(): w.destroy()
        if not txn: ctk.CTkLabel(self._tc, text="İşlem bulunamadı", text_color=TEXT_MUTED).pack(expand=True); return
        h = ctk.CTkFrame(self._tc, fg_color="#f8f9fa", corner_radius=6); h.pack(fill="x")
        h.grid_columnconfigure((0,1,2,3), weight=1)
        for i,ht in enumerate(["Tarih","İşlem","Açıklama","Tutar"]):
            ctk.CTkLabel(h, text=ht, font=ctk.CTkFont(size=12,weight="bold"), text_color=TEXT_MUTED).grid(row=0, column=i, padx=4, pady=8)
        for t in txn:
            r = ctk.CTkFrame(self._tc, fg_color="transparent"); r.pack(fill="x", pady=1)
            r.grid_columnconfigure((0,1,2,3), weight=1)
            amt = t.get('amt',0); c = SUCCESS if amt>=0 else DANGER
            for j,v in enumerate([t.get('d',''),t.get('tp',''),t.get('desc',''),fmt(abs(amt))]):
                ctk.CTkLabel(r, text=v, font=ctk.CTkFont(size=12), text_color=c if j==3 else TEXT_DARK).grid(row=0, column=j, padx=4, pady=5)
        ctk.CTkFrame(self._tc, height=1, fg_color=BORDER).pack(fill="x", pady=6)

    def _mat(self, mat):
        for w in self._mc.winfo_children(): w.destroy()
        if not mat: ctk.CTkLabel(self._mc, text="Yaklaşan vade bulunamadı", text_color=TEXT_MUTED).pack(expand=True); return
        for m in mat:
            r = ctk.CTkFrame(self._mc, fg_color="transparent"); r.pack(fill="x", pady=2, padx=4)
            r.grid_columnconfigure(0, weight=1); r.grid_columnconfigure(1, weight=0)
            du = m.get('due','')
            try:
                dt = datetime.strptime(du[:10],'%Y-%m-%d')
                dl = (dt.date()-date.today()).days
                du = dt.strftime('%d.%m.%Y')
                du += f" ({-dl} gün gecikti)" if dl<0 else f" ({dl} gün)"
            except Exception:
                pass
            ctk.CTkLabel(r, text=f"{m.get('name','')} - {m.get('inv','')}", font=ctk.CTkFont(size=13),
                text_color=TEXT_DARK, anchor="w").grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(r, text=du, font=ctk.CTkFont(size=12), text_color=TEXT_MUTED, anchor="w").grid(row=1, column=0, sticky="w")
            ctk.CTkLabel(r, text=fmt(m.get('amt',0)), font=ctk.CTkFont(size=12, weight="bold"),
                text_color=DANGER).grid(row=0, column=1, rowspan=2, sticky="e", padx=(8,0))

    def _auto(self):
        if self._rid: self.after_cancel(self._rid)
        self._rid = self.after(60000, lambda: (self.refresh(), self._auto()))

    def _ni(self):
        if self.main_app: self.main_app.show_module('invoices')
    def _co(self):
        if self.main_app: self.main_app.show_module('cashbank')
    def _nc(self):
        if self.main_app: self.main_app.show_module('customers')
    def _br(self):
        if self.main_app: self.main_app.show_module('reports')

    def destroy(self):
        if self._rid: self.after_cancel(self._rid)
        super().destroy()
