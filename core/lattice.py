"""MARCHLAND core: BP-Lattice grid-density battle resolver.

1 agent ~ 10 men. No attack/defense/morale stats.
Class A constants (BATTLE_A) are identical for every human; sides differ only via
B (gear), C (fatigue/belief from campaign), D (doctrine), E (drill error).

Modes:
  stochastic — seeded RNG, the default
  deterministic — hazard accumulation (det=True), bit-identical replay from same inputs
"""
import numpy as np
from .constants import BATTLE_A as A, BATTLE_DT as DT


def _sm9(g):
    """3x3 Moore-neighbourhood sum (pad-and-slice, no loops)."""
    p = np.pad(g, 1)
    return (p[:-2,:-2]+p[:-2,1:-1]+p[:-2,2:]+p[1:-1,:-2]+p[1:-1,1:-1]
            +p[1:-1,2:]+p[2:,:-2]+p[2:,1:-1]+p[2:,2:])


class Battle:
    def __init__(self, scn, seed, det=False):
        self.scn, self.det = scn, det
        self.rng = np.random.default_rng(seed)
        self.cs = 2.0
        self.W, self.H = int(scn['field'][0]/self.cs), int(scn['field'][1]/self.cs)
        C = scn['cohorts']; self.C = C
        ci, xs, ys = [], [], []
        for k, c in enumerate(C):
            n = c['n']; ci += [k]*n
            ii = np.arange(n)
            xs.append(c['x'][0]+(c['x'][1]-c['x'][0])*((ii*0.7548776662)%1.0) if det else self.rng.uniform(*c['x'], n))
            ys.append(c['y'][0]+(c['y'][1]-c['y'][0])*((ii*0.5698402909)%1.0) if det else self.rng.uniform(*c['y'], n))
        self.ci = np.array(ci); self.N = len(ci)
        self.x = np.concatenate(xs).astype(np.float32); self.y = np.concatenate(ys).astype(np.float32)
        g = lambda k, d=0.0: np.array([C[c].get(k, d) for c in self.ci], np.float32)
        self.side = g('side').astype(int)
        self.advd = np.where(g('advdir', 99)==99, np.where(self.side==0,1,-1), g('advdir',99)).astype(np.float32)
        self.err, self.armor, self.belief = g('err',1.0), g('armor'), g('belief',0.6)
        self.disc, self.delay = g('disc',0.5), g('delay')
        self.mounted, self.ranged = g('mounted')>0, g('ranged')>0
        self.evade, self.hold = g('evade')>0, g('hold')>0
        self.crowdcap = g('crowd_cap', 99.0); self.allr = g('allround')>0; self.coverb = g('cover_bonus')
        self.ammo = g('ammo')
        self.alive = np.ones(self.N, bool); self.rout = np.zeros(self.N, bool)
        self.cap = np.zeros(self.N, bool); self.esc = np.zeros(self.N, bool)
        self.fat = g('fat0'); self.hes = np.zeros(self.N, np.float32)
        self.accs = {}; self.facc = np.zeros(self.N, np.float32)
        q = (np.arange(self.N) % 100 / 100 + .005) if det else self.rng.random(self.N)
        self.th = (1.0 + 1.2*q).astype(np.float32)
        self.t = 0.0; self.ev = []; self.bt = {0: None, 1: None}; self.vacc = {}
        self.kpre = {0:0,1:0}; self.kpost = {0:0,1:0}
        self.leader = {0:True,1:True}; self.flank = None
        self.fear = np.zeros((self.W,self.H), np.float32)
        self.deadG = [np.zeros((self.W,self.H), np.float32) for _ in (0,1)]

    def bern(self, p, key='k'):
        p = np.clip(p, 0, .95)
        if not self.det:
            return self.rng.random(self.N) < p
        if key not in self.accs: self.accs[key] = np.zeros(self.N, np.float32)
        a = self.accs[key]; a += p; out = a >= 1.0; a[out] -= 1.0; return out

    def tick(self):
        scn = self.scn
        act = self.alive & (self.t >= self.delay)
        std = act & ~self.rout & ~self.cap
        cx = np.clip((self.x/self.cs).astype(int), 0, self.W-1)
        cy = np.clip((self.y/self.cs).astype(int), 0, self.H-1)
        cnt, rtg = [], []
        for s in (0,1):
            m = std & (self.side==s)
            gC = np.zeros((self.W,self.H), np.float32); np.add.at(gC,(cx[m],cy[m]),1)
            mr = act & self.rout & (self.side==s) & ~self.cap
            gR = np.zeros((self.W,self.H), np.float32); np.add.at(gR,(cx[mr],cy[mr]),1)
            cnt.append(_sm9(gC)); rtg.append(_sm9(gR))
        own = np.where(self.side==0, cnt[0][cx,cy], cnt[1][cx,cy])
        foe = np.where(self.side==0, cnt[1][cx,cy], cnt[0][cx,cy])
        frt = np.where(self.side==0, rtg[0][cx,cy], rtg[1][cx,cy])
        fdn = np.where(self.side==0, self.deadG[0][cx,cy], self.deadG[1][cx,cy])
        bx = np.clip(((self.x - self.advd*8)/self.cs).astype(int), 0, self.W-1)
        foeB = np.where(self.side==0, cnt[1][bx,cy], cnt[0][bx,cy])
        contact = (foe>0) & std & ~self.mounted
        mud = np.zeros(self.N, bool)
        if 'mud' in scn:
            a,b = scn['mud']; mud = (self.x>a)&(self.x<b)
        # movement
        go = std & ~contact & (self.hes<=0) & ~self.hold & ~self.mounted & ~getattr(self,'_halt',False)
        spd = 1.5*(1-0.6*self.fat)*np.where(mud,0.45,1.0)
        self.x[go] += (self.advd*spd*DT)[go]
        self.fat[go] += (A['fat_move']*DT*np.where(mud,A['fat_mud'],1.0))[go]
        cv = std & self.mounted & (self.hes<=0)
        if cv.any():
            if 'stakes_x' in scn:
                sx = scn['stakes_x']
                blk = cv & (((self.advd<0)&(self.x<sx+4)&(self.x>sx-30)) | ((self.advd>0)&(self.x>sx-4)&(self.x<sx+30)))
                self.hes[blk] = A['hes']; self.x[blk] -= (self.advd*10)[blk]; cv &= ~blk
            reach = cv & (foe>0)
            solid = reach & (foe >= A['horse_solid'])
            self.hes[solid] = A['hes']*0.8; self.x[solid] -= (self.advd*12)[solid]
            ix, iy = cx[solid], cy[solid]
            if solid.any(): np.add.at(self.fear,(ix,iy),1.5)
            pen = reach & ~solid
            if pen.any():
                cells = set(zip(cx[pen].tolist(), cy[pen].tolist()))
                vict = std & ~self.mounted & np.array([(a,b) in cells for a,b in zip(cx,cy)])
                vict &= (self.side != self.side[np.argmax(pen)])
                self._kill(vict & self.bern(np.where(vict,0.30,0), 'cv'))
                np.add.at(self.fear,(cx[pen],cy[pen]),2.0)
            self.x[cv & (foe==0)] += (self.advd*5.0*DT)[cv&(foe==0)]
        if 'wall' in scn:
            wx, gates, dside = scn['wall']
            atk = (self.side != dside) & self.alive
            past = atk & (((self.advd<0)&(self.x<wx)) | ((self.advd>0)&(self.x>wx)))
            ingate = np.zeros(self.N, bool); inbreach = np.zeros(self.N, bool)
            for g_ in gates:
                y0,y1 = g_[0], g_[1]
                m_ = (self.y>=y0)&(self.y<=y1)
                ingate |= m_
                if len(g_)>2 and g_[2]=='breach': inbreach |= m_
            push = past & ~ingate
            self.x[push] = wx + np.where(self.advd[push]<0, 7.0, -7.0)
            nearwall = (self.side != dside) & self.alive & (np.abs(self.x - wx) < 14) & ~ingate
            if nearwall.any():
                centers = np.array([(g_[0]+g_[1])/2 for g_ in gates])
                tgt = centers[np.argmin(np.abs(self.y[nearwall][:,None]-centers[None,:]),axis=1)]
                self.y[nearwall] += np.sign(tgt - self.y[nearwall])*1.6
            deep = (self.side != dside) & (((self.advd<0)&(self.x < wx-12)) | ((self.advd>0)&(self.x > wx+12)))
            self._halt = deep
            self._covb = self.coverb * np.where((self.side==dside) & inbreach, 0.0, 1.0)
            self._rubble = inbreach.copy()
        else:
            self._halt = np.zeros(self.N, bool)
            self._covb = self.coverb
            self._rubble = np.zeros(self.N, bool)
        run = act & self.rout & ~self.cap & ~self.esc
        rspd = 3.0*(1-0.6*self.fat)*np.where(mud,0.4,1.0)*(1-0.4*self.armor)
        self.x[run] -= (self.advd*rspd*DT)[run]
        self.esc |= run & ((self.x<3)|(self.x>scn['field'][0]-3))
        # volleys every 5th tick
        if int(self.t/DT) % 5 == 0: self._volley(std, cx, cy)
        # melee
        eff = np.minimum(foe, own*1.6 + 2.0)
        load = np.clip(eff/np.maximum(own,1) - 1.0 - np.clip((own-1)*0.35,0,1.2)*np.where(getattr(self,'_rubble',np.zeros(self.N,bool)),0.4,1.0) - getattr(self,'_covb',self.coverb), 0, 2.5)
        lam = np.where(contact, A['lam0']*self.err*(1+A['fat_amp']*self.fat)*(1+A['lamx']*load), 0)
        op = self.bern(1-np.exp(-lam*DT), 'op')
        died = op & self.bern(np.where(op, A['p_down']*(1-self.armor*0.8), 0), 'kl')
        self.hes[op & ~died] = A['hes']
        self._kill(died)
        self.fat[contact] += A['fat_melee']*DT
        self.fat[contact & (own>self.crowdcap)] += A['fat_melee']*DT
        self.fat[std & ~contact & ~go] -= A['fat_rec']*DT
        np.clip(self.fat, 0, 1, out=self.fat)
        # appraisal
        w = A['w']; press = self.fear[cx,cy]/6.0
        nold = np.array([self.leader[s] for s in (0,1)])
        cue = (w['downs']*np.clip(fdn/6.0,0,1.5) + w['rout']*np.clip(frt/4.0,0,1.5)
               + w['expose']*np.clip(load,0,2) + w['behind']*np.clip(foeB/4,0,1.5)*(~self.allr)
               + w['fat']*self.fat + w['press']*np.clip(press,0,1.5)
               + w['banner']*(~nold[self.side]).astype(np.float32)
               - 1.1*self.belief - 0.3*np.clip((own-1)*0.2,0,0.8))
        if not self.det:
            flee = std & ~self.mounted & (cue > self.th)
        else:
            self.facc += np.clip(cue-self.th,0,None)*0.5
            flee = std & ~self.mounted & (self.facc > 1.0)
        self.rout |= flee
        # feints
        for ft, fs in scn.get('feints', []):
            if abs(self.t-ft) < DT:
                self.ev.append(('feint', self.t))
                tmpt = std & (self.side==fs) & (self.disc<0.35)
                tmpt &= (self.th < 1.55) if self.det else (self.rng.random(self.N)<0.45)
                self.x[tmpt] += (self.advd*16)[tmpt]; self.fat[tmpt]+=.06
                self.hold[tmpt] = False
                self.y[tmpt] += (np.linspace(-12,12,self.N)[tmpt] if self.det else self.rng.uniform(-12,12,int(tmpt.sum())))
        # leader lottery
        for s in (0,1):
            cf = scn.get('leader_risk',{}).get(s)
            if cf and self.leader[s]:
                m = (self.side==s)&std
                if m.any() and cnt[s].max() < cf[0]:
                    hit = (self.t>cf[2]) if self.det else (self.rng.random()<cf[1])
                    if hit:
                        self.leader[s]=False; self.ev.append((f'leader{s}_down', self.t))
        # break + pursuit
        for s in (0,1):
            m = self.side==s
            if self.bt[s] is None:
                stand = (std&m).sum() + (m & self.alive & (self.t < self.delay)).sum()
                carried = False
                if 'wall' in scn and s == scn['wall'][2]:
                    wx = scn['wall'][0]
                    inside = std & (self.side!=s) & (((self.advd<0)&(self.x<wx-4)) | ((self.advd>0)&(self.x>wx+4)))
                    if inside.sum() >= scn.get('carry_n', 9e9):
                        carried = True; self.ev.append(('wall_carried', self.t))
                if carried or stand < scn.get('break_frac',0.45)*m.sum():
                    self.bt[s]=self.t; self.ev.append((f'side{s}_broke', self.t))
                    self.hold = self.hold & (self.side==s)
            else:
                runm = m & act & self.rout & ~self.cap & ~self.esc
                if runm.any():
                    foeN = np.where(self.side==0, cnt[1][cx,cy], cnt[0][cx,cy])
                    catch = runm & (foeN>0)
                    inten = scn.get('pursuit_intensity',{}).get(1-s,0.6)
                    kp = catch & self.bern(np.where(catch,0.02*inten*DT,0), 'pk')
                    capp = scn.get('cap_p',{}).get(s,0.0)
                    cp = catch & ~kp & (self.bern(np.where(catch,capp*0.02*DT,0), 'cp'))
                    self.cap |= cp
                    self._kill(kp, post=True)
        for g in self.deadG: g *= 0.985
        self.fear *= 0.97; self.hes -= DT
        self.t += DT

    def _volley(self, std, cx, cy):
        scn = self.scn
        for s in (0,1):
            sh = std & self.ranged & (self.side==s) & (self.ammo>0) & (self.hes<=0)
            if not sh.any(): continue
            rmax = scn.get('range',{}).get(s,140)
            tg = std & (self.side==1-s)
            if not tg.any(): continue
            ys = (self.y/12).astype(int)
            for st in np.unique(ys[sh]):
                S = sh & (ys==st); T = tg & (np.abs(self.y-(st*12+6))<10)
                if not T.any(): continue
                d = (self.x[T].min()-np.median(self.x[S])) if self.advd[np.argmax(S)]>0 else (np.median(self.x[S])-self.x[T].max())
                if d>rmax or d<2: continue
                shots = int(S.sum())*10
                aT = float(self.armor[T].mean()); prone = float((self.hes[T]>0).mean())
                ph = 0.008*(1-0.9*aT)*(1-0.5*prone)*min(1.0, 80/max(d,20))
                if not self.det:
                    nh = int(self.rng.binomial(shots, ph)); ns = int(self.rng.binomial(shots, min(.95,ph*5.0)))
                else:
                    k1 = self.vacc.get((s,st,'h'),0.0)+shots*ph; nh=int(k1); self.vacc[(s,st,'h')]=k1-nh
                    k2 = self.vacc.get((s,st,'s'),0.0)+shots*ph*5.0; ns=int(k2); self.vacc[(s,st,'s')]=k2-ns
                idx = np.flatnonzero(T)
                if not self.det: self.rng.shuffle(idx)
                k = np.zeros(self.N, bool); k[idx[:nh]] = True
                self._kill(k)
                sup = idx[:min(ns,len(idx))]
                self.hes[sup] = np.where(self.evade[sup], A['hes']*1.6, A['hes']*0.5)
                self.ammo[S] -= 1
                if 'supply_xy' in scn and s == scn.get('supply_side', -1):
                    px,py = scn['supply_xy']
                    dist = np.hypot(self.x[S]-px, self.y[S]-py)
                    res = (np.exp(-dist/scn['supply_d0'])>0.5) if self.det else (self.rng.random(S.sum())<np.exp(-dist/scn['supply_d0']))
                    self.ammo[S] += res*1.0
                    stv = self.ammo[S]<=0
                    if stv.any() and self.flank is None:
                        self.flank = 'far' if abs(self.y[S][stv].mean()-py) > scn['supply_d0'] else 'near'
                        self.ev.append(('ammo_starved_'+self.flank, self.t))

    def _kill(self, died, post=False):
        died = died & self.alive
        if not died.any(): return
        cx = np.clip((self.x[died]/self.cs).astype(int),0,self.W-1)
        cy = np.clip((self.y[died]/self.cs).astype(int),0,self.H-1)
        for s in (0,1):
            m = died & (self.side==s)
            n = int(m.sum())
            if n:
                if post or self.bt[s] is not None: self.kpost[s]+=n
                else: self.kpre[s]+=n
        np.add.at(self.deadG[0], (cx[self.side[died]==0],cy[self.side[died]==0]), 1)
        np.add.at(self.deadG[1], (cx[self.side[died]==1],cy[self.side[died]==1]), 1)
        self.alive[died] = False

    def run(self, ticks=1600):
        end = None
        for _ in range(ticks):
            self.tick()
            if end is None and any(self.bt[s] is not None for s in (0,1)):
                end = self.t + 360
            if end and self.t > end: break
        r = {}
        for s in (0,1):
            m = self.side==s; tot = int(m.sum())
            r[s] = dict(total=tot*10, rout=int((self.rout&m&self.alive).sum())*10,
                        dead=(self.kpre[s]+self.kpost[s])*10,
                        pre=self.kpre[s]*10, post=self.kpost[s]*10,
                        cap=int((self.cap&m).sum())*10, broke=self.bt[s])
        if self.bt[0] is not None and (self.bt[1] is None or self.bt[0]<self.bt[1]): win=1
        elif self.bt[1] is not None: win=0
        else: win=-1
        return dict(win=win, t=self.t, s=r, ev=self.ev[:10], flank=self.flank)
