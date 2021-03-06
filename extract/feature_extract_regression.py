# -*- coding: utf-8 -*-
"""
Created on Thu Apr 20 17:25:40 2017

@author: vurga
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Apr  3 10:34:32 2017

Args: corpusA corpusB ctxA ctxB nos save_feas(True/False) classifier(sv/gb/ens) features(all/set/ctx)

@author: vurga
"""

import sys
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict as ddict
import math
import unicodedata
import string
import pandas as pd
import pickle
import re

## whether to save extrcted features for later reuse

if  sys.argv[6] == "True":
    save_feas = True
else:
    save_feas = False

with open(sys.argv[5]+'.'+sys.argv[8]+'.rsim', 'w'):
    pass
if save_feas:
    with open(sys.argv[5]+'.fea', 'w'):
        pass

def cosine_sim(dictionary):
    
    cosine_sim = 0
    for value in dictionary.values():
        cosine_sim += value[0] * value[1]

    length1 = sum([value[0] ** 2 for value in dictionary.values()]) 
    length2 = sum([value[1] ** 2 for value in dictionary.values()])
    
    try:            
        cosine_sim /= math.sqrt(length1) * math.sqrt(length2)
    except ZeroDivisionError:
        cosine_sim = None
        
    return cosine_sim

def char_ngram(line1, line2, n=2):
    
    ngramdict = ddict(lambda: ddict(lambda: 0))
    line_pair = [line1, line2]
    
    for i, line in enumerate(line_pair):
        line = ''.join(line.split())
        j = 0
        while (j + (n - 1)) < len(line):
            ngramdict[line[j:j+n]][i] += 1
            j += 1
    
    return cosine_sim(ngramdict)

def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')
   
def cognate(line1, line2):
    
    cognatedict = ddict(lambda: ddict(lambda: 0))
    line_pair = [line1, line2]
    
    for i, line in enumerate(line_pair):
        for word in line.split():
            if word.isdigit():
                cognatedict[word][i] += 1
            elif len(word) >= 4:
                cognatedict[strip_accents(word[:4])][i] += 1
            elif len(word) == 1 and word in string.punctuation:
                cognatedict[word][i] += 1

    return cosine_sim(cognatedict)

def lf(line1, line2):
    return math.exp(-.5*((((len(line2)/len(line1))-1.133)/0.415))**2)
      

def extract_fea(tA, tB):
    
    ngram_cosine_sims = {}
    for n in range(2,6):
        ngram_cosine_sims[n] = char_ngram(tA, tB, n) 
    
    cognate_cosine_sims = cognate(tA, tB)
    lfs = lf(tA, tB)
    tokens = (len(tA.split()), len(tB.split()))
    chars=(sum([len(word) for word in tA.split()]), sum([len(word) for word in tB.split()]))
    
    return np.array([ngram_cosine_sims[2], ngram_cosine_sims[3], ngram_cosine_sims[4], ngram_cosine_sims[5], chars[0], chars[1], cognate_cosine_sims, lfs, tokens[0], tokens[1]])

with open(sys.argv[5], 'r') as source:
    nos = source.readlines()
    
with open(sys.argv[1], 'r') as corpusA, open(sys.argv[2]) as corpusB, open(sys.argv[3]) as ctxA, open(sys.argv[4]) as ctxB:

    with open(sys.argv[8]+'.sv_regression.pkl', 'rb') as fid:
        sv = pickle.load(fid)
    with open(sys.argv[8]+'.gb_regression.pkl', 'rb') as fid:
        gb = pickle.load(fid) 
    with open(sys.argv[8]+'.regression_ensemble.pkl', 'rb') as fid:
        ens = pickle.load(fid)

       
    for n, num in enumerate(nos):
        source_nos = int(num.strip().split()[0])
        target_nos = int(num.strip().split()[1])
        
        textA = []
        textB = []
        contxA = []
        contxB = []
        
        for i in range(source_nos):
            textA.append(next(corpusA))
            contxA.append(next(ctxA))
        for i in range(target_nos):
            textB.append(next(corpusB))
            contxB.append(next(ctxB))
        
        for i, tA in enumerate(textA):
            for j, tB in enumerate(textB):
                
                lA = len(tA.strip().split())
                lB = len(tB.strip().split())
                if lA == 0 or lB == 0:
                    continue
                r = lA / lB
                if r > 2.0 or r < 0.5 or lA < 4 or lB < 4 or lA > 50 or lB > 50 or re.match('\\\\', tA) or re.match('\\\\', tB):
                    continue
                else:
                    if save_feas:
                        ## compute cosine sim
                        cvec_1 = np.fromstring(contxA[i].strip(), sep=" ")
                        cvec_2 = np.fromstring(contxB[j].strip(), sep=" ")
                        ## compute cosine sim
                        sim = cosine_similarity(cvec_1, cvec_2)
                                
                        ## extract all sx feas
                        feas = extract_fea(tA, tB)
                        ## get appropriate feature set
                        if sys.argv[8] == 'ctx':
                            feas_c = sim
                        elif sys.argv[8] == 'set':
                            feas_c = feas
                        else:
                            feas_c = np.append(feas, sim)
                        
                    else:
                        with open(sys.argv[5]+'.fea', 'r') as source:
                            idx = None
                            while idx != i * j:
                                line = next(source)
                                idx = int(line.strip().split()[0])
                            ## get appropriate feature set
                            if sys.argv[8] == 'ctx':
                                feas_c = np.fromstring(' '.join(line.strip().split()[-1]), sep=' ')
                            elif sys.argv[8] == 'set':
                                feas_c = np.fromstring(' '.join(line.strip().split()[:-1]), sep=' ')
                            else:
                                feas_c = np.fromstring(' '.join(line.strip().split()[1:]), sep=' ')

                       
                    try:
                            
                            if sys.argv[7] == 'ens':
                                sv_pred = sv.predict(feas_c)
                                gb_pred = gb.predict(feas_c)
                                ens_pred = ens.predict(np.concatenate((sv_pred, gb_pred)))
                            elif sys.argv[7] == 'sv':
                                sv_pred = sv.predict(feas_c)
                                ens_pred = sv_pred
                            else:
                                gb_pred = gb.predict(feas_c)
                                ens_pred = gb_pred
                            if ens_pred > 2.5:
                                with open(sys.argv[5]+'.'+sys.argv[8]+'.rsim', 'a+') as target:
                                    target.write('%d %d %d %f \n' % (n, i, j, ens_pred))
                                if save_feas:
                                    with open(sys.argv[5]+'.fea', 'a+') as target:
                                        target.write(str(i*j)+' '+' '.join([str(x) for x in feas_c])+' \n')
                            else:
                                continue
                            
                    except:
                        continue
