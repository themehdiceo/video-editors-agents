import json
D="jobs/20261118-062812-edit/work/" if __import__('os').path.exists("jobs") else "work/"
W=json.load(open(D+'words_dst.json')); M=json.load(open(D+'motions_spec.json'))
R=json.load(open(D+'aroll_cut.mp4.timemap.json'))['ranges']
def s2d(t):
  for r in R:
    if r['src_end']>=t: return r['dst_start']+max(0,t-r['src_start'])
  return 1e9
n=lambda s: s.replace('\xa0',' ').lower()
for m in M:
  last=s2d(m['hint_src']); m['t']=[]
  for ln in m['lines']:
    after=s2d(ln[2]) if len(ln)>2 else last
    t=next((w['t'] for w in W if w['t']>=after and n(w['w']).startswith(n(ln[1]))),None)
    m['t'].append(t); last=t if t else last
json.dump(M,open(D+'motions_timed.json','w'),ensure_ascii=False,indent=0)
if __name__=="__main__":
  prev=-99
  for i,m in enumerate(M): print(i+1,m['t'],'gap',round(m['t'][0]-prev,1),m['lines'][0][0][:28]); prev=m['t'][0]
