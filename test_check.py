import requests
r = requests.post('http://127.0.0.1:5000', data={
    'project':'project2',
    'p2_excel_file':'NIFTY 50_Historical_PR_01011990to11102024.csv',
    'p2_start_date':'1999-01-01',
    'p2_invest_amt':'1000','p2_freq':'monthly',
    'p2_day_rule':'first_trading_day','p2_price_col':'Close',
    'p2_bond_ret':'6.5','p2_bond_comp':'continuous',
    'p2_trigger_mode':'highest_only','p2_output':'t.xlsx',
    'alloc_count':'3',
    'alloc_min_0':'0','alloc_max_0':'20','alloc_eq_0':'80','alloc_bd_0':'20',
    'alloc_min_1':'20','alloc_max_1':'30','alloc_eq_1':'90','alloc_bd_1':'10',
    'alloc_min_2':'30','alloc_max_2':'100','alloc_eq_2':'100','alloc_bd_2':'0',
    'bshift_count':'4',
    'bshift_tr_0':'10','bshift_pct_0':'20','bshift_once_0':'on',
    'bshift_tr_1':'20','bshift_pct_1':'40','bshift_once_1':'on',
    'bshift_tr_2':'30','bshift_pct_2':'70','bshift_once_2':'on',
    'bshift_tr_3':'40','bshift_pct_3':'100','bshift_once_3':'on',
    'p2_show_roi':'on','p2_show_dd':'on','p2_show_cagr':'on','p2_show_split':'on',
})
h = r.text
print('Charts:', 'OK' if 'data:image/png;base64,' in h else 'MISSING')
print('Cards:', 'OK' if 'class="card"' in h else 'MISSING')
print('Split layout:', 'OK' if 'section split' in h else 'MISSING')
print('Kitchen table:', 'OK' if 'kitchen' in h.lower() else 'MISSING')
print('Drawdown chart:', 'OK' if 'drawdown' in h.lower() else 'MISSING')
print('Errors:', 'NONE' if 'class="error"' not in h else h[h.find('class="error"'):h.find('class="error"')+200])
print(f'Page size: {len(h)} bytes')
