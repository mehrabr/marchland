import sys, json, numpy as np
sys.path.insert(0,'/home/claude')
from marchland_toy import Battle
from scenarios import SCN
name, seeds = sys.argv[1], int(sys.argv[2])
det = len(sys.argv)>3 and sys.argv[3]=='det'
ticks = int(sys.argv[4]) if len(sys.argv)>4 else 2200
out=[]
for sd in range(seeds):
    out.append(Battle(SCN[name](), sd, det=det).run(ticks))
json.dump(out, open(f'/home/claude/res_{name}{"_det" if det else ""}.json','w'))
w=[r['win'] for r in out]
print(name, 'win0=%.2f win1=%.2f none=%.2f'%(np.mean([x==0 for x in w]),np.mean([x==1 for x in w]),np.mean([x==-1 for x in w])))
for s in (0,1):
    print(' side%d dead pre/post/cap (med): %d/%d/%d of %d'%(s,
        np.median([r['s'][str(s)]['pre'] if str(s) in r['s'] else r['s'][s]['pre'] for r in out]),
        np.median([r['s'][s]['post'] for r in out]), np.median([r['s'][s]['cap'] for r in out]),
        out[0]['s'][s]['total']))
print(' sample events:', out[0]['ev'], 'flank:', out[0]['flank'], 't=%.0f'%out[0]['t'])
