import itertools, collections

def v_allsubstr_prefix(s):
    """D = all substrings of prefix s[0:i]; phrase = longest factor in D + 1 char."""
    n=len(s); i=0; c=0
    while i<n:
        c+=1; j=i+1
        while j<=n and s.find(s[i:j],0,i)>=0: j+=1
        i=j
    return c

def v_phrase_tokens(s):
    """D = previously emitted phrases (exact strings only)."""
    n=len(s); i=0; c=0; D=set()
    while i<n:
        start=i; j=i+1
        while j<=n and s[i:j] in D: j+=1
        if s[i:j] in D: i=n
        else: i=j
        c+=1; D.add(s[start:i])
    return c

def v_substr_of_phrases(s):
    """D = union of substrings of each emitted phrase (no cross-phrase spanning)."""
    n=len(s); i=0; c=0; D=set()
    while i<n:
        start=i; j=i+1
        while j<=n and s[i:j] in D: j+=1
        if s[i:j] in D: i=n
        else: i=j
        c+=1; ph=s[start:i]
        for a in range(len(ph)):
            for b in range(a+1,len(ph)+1): D.add(ph[a:b])
    return c

def v_phrases_cumulative(s):
    """D = cumulative set of emitted phrases AND their substrings (grows only at boundaries)."""
    return v_substr_of_phrases(s)

def v_till_first_unseen_then_all(s):
    """phrase = shortest not a substring of prefix (A), but D only updated with phrase+its substrings."""
    n=len(s); i=0; c=0; D=set()
    while i<n:
        start=i; j=i+1
        while j<=n and s[i:j] in D: j+=1
        if s[i:j] in D: i=n
        else: i=j
        c+=1; ph=s[start:i]
        # add all substrings of prefix that END before i (i.e. within phrase)
        for a in range(start,i):
            for b in range(a+1,i+1): D.add(s[a:b])
    return c

def census(fn,label):
    dist=collections.Counter()
    ex=collections.defaultdict(list)
    for bits in itertools.product('01',repeat=10):
        s=''.join(bits); v=fn(s); dist[v]+=1; ex[v].append(s)
    print(f"{label}: {dict(sorted(dist.items()))}")
    return ex

exA=census(v_allsubstr_prefix,"A all-substrings-of-prefix")
exB=census(v_phrase_tokens,"B phrase-tokens")
exC=census(v_substr_of_phrases,"C substrings-of-phrases")
exD=census(v_till_first_unseen_then_all,"D substrings-of-prefix-up-to-i")
# show which strings have extreme counts
for name,ex in [("A",exA),("B",exB),("C",exC),("D",exD)]:
    ks=sorted(ex)
    print(f"  {name}: min c={ks[0]} e.g. {ex[ks[0]][:6]}; max c={ks[-1]} count={len(ex[ks[-1]])}")
