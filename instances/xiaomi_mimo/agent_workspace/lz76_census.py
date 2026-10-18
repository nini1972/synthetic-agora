import itertools, json, collections

def lz76_full(s):
    """LZ-76 where dictionary D = ALL substrings of s[0:i]; phrase = longest factor in D + 1 char."""
    n=len(s); i=0; c=0
    while i<n:
        c+=1
        j=i+1
        while j<=n and s.find(s[i:j],0,i)>=0:
            j+=1
        # phrase ends at j if s[i:j] not in D and j>i+1; else length 1
        if j>i+1:
            i=j
        else:
            i=i+1
    return c

def lz76_phrase(s):
    """LZ-76 where dictionary D = previously emitted phrases (all their substrings)."""
    n=len(s); i=0; c=0; D=set()
    while i<n:
        c+=1
        j=i+1
        while j<=n and s[i:j] in D:
            j+=1
        if j>i+1:
            # s[i:j] not in D but s[i:j-1] in D -> phrase = s[i:j]
            i=j
        else:
            i=i+1
        D.add(s[i-  (1 if (j==i) else 0) :]) if False else None
    return c

def lz76_phrase2(s):
    """Standard textbook: dictionary accumulates phrases; phrase grows while current+1 is prefix-free match."""
    n=len(s); i=0; c=0; D=set()
    while i<n:
        # grow phrase s[i:j] while in D
        j=i+1
        while j<=n and s[i:j] in D:
            j+=1
        # if j==i+1 and s[i:i+1] not in D -> new phrase = 1 char
        # if s[i:j] not in D and j>i+1 -> phrase = s[i:j]
        if s[i:j] in D:   # j==n and all found -> remaining already in D
            i=n
        else:
            i=j
        c+=1
        # add the phrase and all its substrings? classic adds only the phrase token
        # here add phrase itself plus prefixes for 'all substrings' semantics
        D.add(s[i-  (i- (i)) :]) if False else None
    return c

# simplest: two plausible variants, count distributions
def variantA(s):
    # D = all substrings of prefix; phrase = longest factor in D + 1 char
    return lz76_full(s)

def variantB(s):
    # D = phrases only (tokens); phrase = shortest NEW string
    n=len(s); i=0; c=0; D=set()
    while i<n:
        c+=1
        j=i+1
        while j<=n and s[i:j] in D:
            j+=1
        i=j
        D.add(s[i-1:i])   # only the single character? no...
    return c

def variantC(s):
    # D = all substrings emitted so far (cumulative), phrase = shortest not-in-D
    n=len(s); i=0; c=0; D=set()
    while i<n:
        c+=1
        j=i+1
        while j<=n and s[i:j] in D:
            j+=1
        i=j
        # add ALL substrings ending in the new phrase
        for st in range(i-(i- (i)), i):  # placeholder
            pass
    return c

def variant_sub(s):
    """phrase = shortest string not a substring of prefix; D = all substrings (equivalent to lz76_full but incremental)."""
    n=len(s); i=0; c=0
    while i<n:
        c+=1
        j=i+1
        while j<=n and s[i:j] in s[:i]:   # substring of prefix
            j+=1
        i=j
    return c

def variant_phrase(s):
    """D = previously emitted phrases only; phrase = shortest not in D (classic dictionary of words)."""
    n=len(s); i=0; c=0; D=set()
    while i<n:
        j=i+1
        while j<=n and s[i:j] in D:
            j+=1
        i=j
        c+=1
        D.add(s[i-1:i]) if False else None
        # add the phrase itself
        # (phrase was s[start:i]) -- need start
    return c

def census(fn):
    dist=collections.Counter()
    for bits in itertools.product('01',repeat=10):
        s=''.join(bits)
        dist[fn(s)]+=1
    return dict(sorted(dist.items()))

print("variantA (D=all substrings):", census(variantA))
print("variant_sub (phrase=shortest not substring of prefix):", census(variant_sub))
