import json
D="jobs/20261118-062812-edit/work/"
R=json.load(open(D+'aroll_cut.mp4.timemap.json'))['ranges']; W=json.load(open(D+'sub_words.json'))['words']; out=[]
for w in W:
  m=(w['start']+w['end'])/2
  for r in R:
    if r['src_start']<=m<=r['src_end']: out.append({'w':w['w'],'t':round(r['dst_start']+w['start']-r['src_start'],2)}); break
json.dump(out,open(D+'words_dst.json','w'),ensure_ascii=False)
