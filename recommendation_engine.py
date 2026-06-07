import pandas as pd

def match_guidance(kb,text):
    q=(text or '').lower(); matches=[]
    for _,r in kb.iterrows():
        blob=' '.join([str(r.issue),str(r.root_cause),str(r.recommendation)]).lower()
        score=sum(1 for t in q.split() if t in blob)
        for k in ['bigquery','dataflow','storage','budget','logging']:
            if k in q and k in blob: score+=3
        if score: matches.append((score,r))
    matches=sorted(matches,key=lambda x:x[0],reverse=True)[:3]
    if not matches: matches=[(0,r) for _,r in kb.head(3).iterrows()]
    return pd.DataFrame([m[1] for m in matches])
