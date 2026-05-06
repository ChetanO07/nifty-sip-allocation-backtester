import requests
r = requests.post('http://127.0.0.1:5000', data={
    'project':'project2',
    'p2_excel_file':'NIFTY MIDCAP 100_Data.csv',
    'p2_start_date':'2005-01-01',
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
    'p2_run_report':'1'
})
h = r.text
print('Midcap used?:', 'OK' if 'NIFTY MIDCAP 100' in h else 'MISSING')
import re
print('Benchmark section exists?:', 'YES' if 'Benchmark Comparison' in h else 'NO')

error_match = re.search(r'<div class="error">(.*?)</div>', h, re.DOTALL)
if error_match:
    print('Error message:', error_match.group(1).strip())
else:
    print('Errors: NONE')
