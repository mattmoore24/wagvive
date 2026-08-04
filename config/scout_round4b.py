import json, re, sys
sys.path.insert(0, 'config')
from scout_round4 import scan, pick, econ_table

deep = {
    'feeding': {'Feeding Tools': '2410110341451628800'},
    'mats': {'Pet Mats': '2410110357391611900'},
    'plush': {'Plush': '2410110340531618900'},
    'shower': {'Shower Products': '2410110355151622300'},
    'trainers': {'Trainers': '2410110342161616300'},
    'bowls': {'Pet Bowls': '2410110341061612000'},
    'chase': {'Chase': '2410110339311602900'},
    'nests': {'Pet Nests': '2410110357511615700'},
}
rows=[]
for k,c in deep.items():
    rows += scan(c, pages=12)
print(f'scanned {len(rows)} unique rows')
out={}
out['snuffle']=econ_table('SNUFFLE / SNIFF MATS',
    pick(rows, name_re=re.compile(r'snuffle|sniff(ing)? ?(mat|pad|bowl)|foraging', re.I), min_listed=5, top=8))
out['heartbeat']=econ_table('HEARTBEAT / CALMING PLUSH',
    pick(rows, name_re=re.compile(r'heartbeat|heart beat|calming (plush|toy|puppy)|behavioral aid', re.I), min_listed=3, top=8))
out['pawclean']=econ_table('PAW CLEANER',
    pick(rows, name_re=re.compile(r'paw.*(clean|wash|cup)|foot.*wash', re.I), min_listed=5, allow_nondog=True, top=8))
out['steam']=econ_table('STEAM / SPRAY BRUSH',
    pick(rows, name_re=re.compile(r'steam|spray.*brush|misting', re.I), min_listed=5, allow_nondog=True, top=8))
out['lickmat']=econ_table('LICK MAT',
    pick(rows, name_re=re.compile(r'lick(ing)? ?(mat|pad)', re.I), min_listed=5, allow_nondog=True, top=6))
json.dump(out, open('config/scout_round4b_results.json','w'), indent=1, default=str)
print('saved')
