# -*- coding: utf-8 -*-
"""
Created on Tue Apr 25 10:51:16 2017

@author: bjr21
"""

import numpy as np
import pandas as pd
import os
import datetime

mydir = os.getcwd()
Psim = pd.read_pickle(os.path.join(mydir,'Psim.pkl'))
Wsim = pd.read_pickle(os.path.join(mydir,'Wsim.pkl'))
volsim = pd.read_pickle(os.path.join(mydir,'volsim.pkl'))

#added in because they belong to sections above that take significant space to run
niter=2
event_converter = 14600 #40 years converted to days

Wsim = np.zeros((niter,int(event_converter), 7))
Wsim = pd.Panel(Wsim)
Wsim = Wsim.reindex_axis(Psim[0].index, axis = 'major_axis')

volsim = np.zeros((niter,int(event_converter), 7))
volsim = pd.Panel(volsim)
volsim = volsim.reindex_axis(Psim[0].index, axis = 'major_axis')

for n in range(0,niter):
    simslice = Psim[n]

    W = np.zeros((Psim.shape[1],7))
    vol = np.zeros((Psim.shape[1],7))
    kmat = np.zeros((Psim.shape[1],(9)))

    for j in [0,1,2,3, 4, 5, 6]:
        i = 0
        timebase = True
        driftbase = False
        if j==0:
            a = simslice.resample('D').first() #daily rebalance
        elif j==1:
            a = simslice.resample('MS').first() #monthly rebalance
        elif j==2:
            a = simslice.resample('AS').first() #yearly rebalance
        elif j==3:
            timebase = False
        elif j==4:
            timebase = False
            driftbase = True
            driftpoint = 0.01
        elif j==5:
            timebase = False
            driftbase = True
            driftpoint = 0.03
        elif j==6:
            timebase = False
            driftbase = True
            driftpoint = 0.05
        print(j)
        #initial number of shares of each stock
        W_init = 1000 #dollars
        kcurr = [0.35*1.125, 0.1*1.125, 0.1*1.125, 0.15*1.125, 0.1*1.125, 0, 0, 0, 0.1]
        delta = np.divide(np.multiply(kcurr,W_init),simslice.iloc[0].values)
        for k in range(0,len(kmat)):
            toret = simslice.index.year[-1] - simslice.index.year[k]
            if toret == 5:
                kcurr = [0.35*0.75, 0.1*0.75, 0.1*0.75, 0.15*0.75, 0.1*0.75, 0, 0, 0, 0.4]
            elif toret == 15:
                kcurr = [0.35*0.9375, 0.1*0.9375, 0.1*0.9375, 0.15*0.9375, 0.1*0.9375, 0, 0, 0, 0.25]
            elif toret == 20:
                kcurr = [0.35, 0.1, 0.1, 0.15, 0.1, 0, 0, 0, 0.2]
            elif toret == 25:
                kcurr = [0.35*1.1, 0.1*1.1, 0.1*1.1, 0.15*1.1, 0.1*1.1, 0, 0, 0, 0.12]
            
            W_ind = np.multiply(delta,simslice.iloc[k].values)
            W[k,j] = W_ind.sum()
            kmat[k,:] = np.multiply(simslice.iloc[k], delta/W[k,j])
        
            period = pd.date_range(simslice.iloc[k].name - datetime.timedelta(days=30),simslice.iloc[k].name)
            varperiod = simslice.loc[period]
            varperiod = varperiod.dropna()
            covmat = varperiod.cov()
            variance = np.dot(np.dot(kmat[k,:].T,covmat.values),kmat[k,:])
            vol[k,j] = np.sqrt(variance)
        
            drift = np.divide(kcurr,kmat[k])
            drift = abs(drift[~np.isnan(drift)])-1
    
            if timebase == True and i<=len(a.index)-1 and (simslice.index[k].year*10000000 + simslice.index[k].month*1000 + simslice.index[k].day) >= (a.index[i].year*10000000 + a.index[i].month*1000 + a.index[i].day):
                delta = np.divide(np.multiply(kcurr,W[k,j]), simslice.iloc[k])
                i += 1
        
            if driftbase == True and np.amax(drift) >= driftpoint:
                delta = np.divide(np.multiply(kcurr,W[k,j]), simslice.iloc[k])
    
    Wstore = pd.DataFrame(W, index = simslice.index)
    Wsim[n] = Wstore
    volstore = pd.DataFrame(vol, index = simslice.index)
    volsim[n] = volstore