# -*- coding: utf-8 -*-
"""
Created on Thu Aug  1 21:16:22 2024

@author: Zoletnik
"""
import numpy as np
import os
import re
import time
import matplotlib.pyplot as plt

import flap
import flap_w7x_abes

flap_w7x_abes.register()

def exp_summary(exp_ID,timerange=None,datapath=None,channels=range(10,26),test=False):
    """
    Return a single line summary of the experiment: expID, max APDCAM signal (uncalibrated), time range, channel range

    Parameters
    ----------
    exp_ID : string
        The exp ID, YYYMMDD.xxx
    timerange : listE, optional
        The processing timerange. The default is None.
    datapath : string, optional
        The datapath. The default is None.

    Returns
    -------
    txt : string
        The experiment summary.

    """
    

    options = {'Resample':1e4,
                'Scaling':'Volt',
                'Amplitude calibration' : False
                }
    if (datapath is not None):
        options['Datapath'] = datapath

    channels_str = ['ABES-'+str(a) for a in channels]
    txt = exp_ID
    print('Processing ' + exp_ID,flush=True)
    
    try:
        d_beam_on=flap.get_data('W7X_ABES',
                                 exp_id='20181018.003',
                                 name='Chopper_time',
                                 options={'State':{'Chop': 0, 'Defl': 0},'Start':1000,'End':-1000}
                                 )
        d_beam_off=flap.get_data('W7X_ABES',
                                 exp_id='20181018.003',
                                 name='Chopper_time',
                                 options={'State':{'Chop': 1, 'Defl': 0},'Start':1000,'End':-1000}
                                 )           
        print('Chopper mode: '+ d_beam_on.info['Chopper mode'],flush=True)
        chopper = True
        error = ''
    except Exception as e:
        chopper = False
        error = str(e)

    if (chopper):
         try:
            sig = np.zeros(len(channels))
            test_fig = None
            for i in range(len(channels)):
                print('  Processing '+channels_str[i],flush=True)
                d=flap.get_data('W7X_ABES',
                                exp_id = exp_ID,
                                name = channels_str[i],
                                options = options,
                                coordinates = {'Time': timerange}
                                )
                d_on = d.slice_data(slicing={'Time':d_beam_on},
                                    summing={'Rel. Sample in int(Time)':'Mean'},
                                    options={'Regenerate':True}
                                    )
                d_off = d.slice_data(slicing={'Time':d_beam_off},
                                     summing={'Rel. Sample in int(Time)':'Mean'},
                                     options={'Regenerate':True}
                                     )
                d_off = d_off.slice_data(slicing={'Time':d_on},
                                         options={'Interpolation':'Linear'}
                                         )
                if (test):
                    if (test_fig is None):
                        test_fig = plt.figure()
                    else:
                        plt.figure(test_fig.number)
                        plt.clf()
                    d.plot()
                    flap.list_data_objects(d_beam_on)
                    d_beam_on.plot(plot_type='scatter',axes=['Time',0],options={'Force':True})
                    plt.pause(2)
                    return
                d_on_data = d_on.data
                d_off_data = d_off.data
                ind = np.nonzero(np.logical_and(np.isfinite(d_off_data),
                                                np.isfinite(d_on_data)
                                                )
                                 )[0]
                d_on_data = d_on_data[ind]
                d_off_data = d_off_data[ind]
                d = d_on_data - d_off_data
                if (i == 0):
                    sig = np.zeros((len(d),len(channels)))
                sig[:,i] = d
            d_max = np.max(sig)
            txt += ' ... Chopper:{:6s} ... Max:{:4.0f}[mV] '.format(d_beam_on.info['Chopper mode'],d_max * 1000)
            timescale = d_on.coordinate('Time')[0][ind]
            s = np.sum(sig,axis=1)
            ind = np.nonzero(s > np.max(s) * 0.1)[0]
            txt += ' ... Time range:({:6.2f}-{:6.2f})[s]'.format(timescale[ind[0]], timescale[ind[-1]])
         except Exception as e:
            txt += ' --- {:s} ---'.format(str(e))
    else:
        txt += ' --- {:s} --- '.format(str(error))
    return txt
        
         
def exp_summaries(exp_ids,datapath=None,timerange=None,file='exp_summaries.txt'):  
    """
    Generate an experiment summary of a series of experiments.

    Parameters
    ----------
    exp_ids : string
        Experiment IDs. *, ? supported as in Unix regexp. Like 2018101?.*
    datapath : string, optional
        The data path. The default is None.
    timerange : listE, optional
         The processing timerange. The default is None.
    file: string
        File name where to write the list       
  
    Returns
    -------
    txts : list of texts
        The list of summary texts.

    """
    
    if (datapath is not None):
        options = {'Datapath':datapath}
    else:
        options = {}
    default_options = {'Datapath':datapath}
    _options = flap.config.merge_options(default_options,options,data_source='W7X_ABES')
    dp = _options['Datapath']
    regexp = exp_ids.replace('.','\.') 
    regexp = regexp.replace('*','.*') 
    txts = []
    id_list = os.scandir(dp)
    exp_list = []
    for idi in id_list:
        if (idi.is_dir()):
            if ((len(idi.name) == 12) and (idi.name[8] == '.') and (re.search(regexp,idi.name) is not None)):
                exp_list.append(idi.name)
    exp_list.sort()
#    print(exp_list)
    with open(file,"wt") as f:
        for exp in exp_list:
            txt = exp_summary(exp,datapath=dp,timerange=timerange)
            time.sleep(2)
            f.writelines(txt + '\n')
            f.flush()
    return txts
        
#exp_summary('20230328.028')
