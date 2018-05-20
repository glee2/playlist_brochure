# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .charts import LineChart
from .charts import GaugeChart
from wordcloud import WordCloud
from PIL import Image

import base64
import StringIO
import json
import os
import csv
import numpy as np

def index(request):

    list_num = 20   # initialize

    try:
        list_num = request.GET['list_num']
        list_num = int(list_num)
    except:
        list_num = 43
        print "not passed"

    playlists = np.array(list(csv.reader(open("../../dataset/yes_small/train.txt", 'r'), delimiter=str(' '))))[2:]

    ind = playlists[list_num-1][:-1]

    data_origin = np.array(list(csv.reader(open("../songs.csv", 'r'))))

    temp = []
    for i in range(len(ind)):
        temp.append(np.where(data_origin[:,0]==ind[i])[0][0])
    ind = temp

    data = np.vstack((data_origin[0].reshape(1,-1),data_origin[ind]))

    context = summary(data, data_origin)

    return render(request, 'playlist/index.html', context)

def summary(data, data_origin):
    
    data_max = stats(data_origin)
    
    line_chart = LineChart(height=600, width=800, explicit_size=True, tooltip_fancy_mode=True)
    gauge_chart = GaugeChart(height=600, width=800, explicit_size=True, tooltip_fancy_mode=True)

    tracks = toDict(data, [], chart_type="tracklist")
    line = toDict(data, ['energy','liveness','acousticness','danceability'])
    gauge = toDict(data, ['energy','liveness','tempo','instrumentalness','loudness','popularity','acousticness','danceability'], chart_type="gauge", stat=data_max)

    tags = ""
    for tag in data[:,-1]:
        try:
            tags += tag 
        except:
            continue

    wordcloud = WordCloud().generate(tags)
    image = wordcloud.to_image()
    image.save("playlist/static/temp.png")
    im = Image.open("playlist/static/temp.png")
#    im = "<img src=\"../../static/temp.png\" style=\"height:600px; width:800px;\"></img>"

    recommended = data_origin[np.random.randint(data_origin.shape[0])]
    recommended = str(recommended[3])+" - "+str(recommended[4])

    result = { 'song_list' : tracks, 'lineChart'  : line_chart.generate(line), 'gaugeChart' : gauge_chart.generate(gauge), 'tags' : im, 'recommended' : recommended }

    return result

def toDict(dat, keys, chart_type="line", stat={}):
    cols = dict()

    if chart_type=="tracklist":
        tracks = []
        for i in range(1, dat.shape[0]):
            tracks.append(str(dat[i][3])+" - "+str(dat[i][4]))

        return tracks

    if chart_type=="line":
        for key in keys:
            temp = dat[1:,np.where(dat[0]==key)[0][0]].astype(float)
            cols[key] = list(temp)

        return cols

    elif chart_type=="gauge":
        for key in keys:
            temp = dat[1:,np.where(dat[0]==key)[0][0]].astype(float)
            cols[key] = []
            if key=="loudness":
                cols[key].append({ 'value' : (temp.mean()+23)/(stat[key]+23)*100, 'max_value' : 100})
            else:
                cols[key].append({ 'value' : temp.mean()/stat[key]*100, 'max_value' : 100})
    
        return cols

    else:
        return cols

def stats(dat):
    res = {}
    for i in range(5, dat[0].shape[0]-2):
        res[dat[0][i]] = dat[1:,i].astype(float).max()
    
    return res


