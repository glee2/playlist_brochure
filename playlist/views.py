# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .charts import LineChart
from .charts import GaugeChart
from wordcloud import WordCloud
from PIL import Image
from sklearn.cluster import KMeans
from matplotlib.patches import Arc, RegularPolygon
from numpy import radians as rad

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
import StringIO
import json
import os
import csv
import numpy as np
import json
import mpld3

@csrf_exempt
def toplist(request):

    track_sch = ''
    try:
        track_sch = request.POST['searchitem']
    except:
        print "not passed!"

    data_origin = np.array(list(csv.reader(open("../songs_cls.csv", 'r'))))

    tops = top_100(data_origin)

    tops = toDict(tops, [], chart_type="tracklist")

    if track_sch:
        song_ind = np.where(data_origin[:,4]==track_sch)[0]
        artist_ind = np.where(data_origin[:,3]==track_sch)[0]
        indices = np.unique(np.concatenate(([0],song_ind,artist_ind)))
        searched = toDict(data_origin[indices], [], chart_type="tracklist")
    else:
        indices = []
        searched = []

    return render(request, 'playlist/toplist.html', { 'tops' : tops, 'searchitems' : searched })

@csrf_exempt
def index(request):

    list_num = 20   # initialize

    data_origin = np.array(list(csv.reader(open("../songs_cls.csv", 'r'))))
    
    if request.method == 'POST':

        try:
            sending = request.POST.getlist('sendlist[]')
        except:
            sending = []
            print "not passed list"
    
        seq_list = []
        
        ind_temp = []
        ind_temp = findindex(data_origin, sending)
        temp = []
        for i in range(len(ind_temp)):
            temp.append(np.where(data_origin[:,0]==str(ind_temp[i]))[0][0])
        ind_temp = temp

        if ind_temp:
            data = np.vstack((data_origin[0].reshape(1,-1),data_origin[ind_temp]))
            context = summary(data, data_origin, seq_list)
            return render(request, 'playlist/index.html', context)
    
    else:
        try:
            list_num = request.GET['list_num']
            list_num = int(list_num)
        except:
            list_num = 43
    
        playlists = np.array(list(csv.reader(open("../../dataset/yes_small/train.txt", 'r'), delimiter=str(' '))))[2:]
        seq_list = list(csv.reader(open("../../dataset/yes_small/freq_songs.csv", 'r')))
#        seq_list=[]
    
        ind = playlists[list_num-1][:-1]
    
        temp = []
        for i in range(len(ind)):
            temp.append(np.where(data_origin[:,0]==ind[i])[0][0])
        ind = temp
    
        data = np.vstack((data_origin[0].reshape(1,-1),data_origin[ind]))
        context = summary(data, data_origin, seq_list)
        return render(request, 'playlist/index.html', context)

def summary(data, data_origin, freq_songs):
    centers = np.array(list(csv.reader(open("../centers_.csv", 'r'))))
    data_max = stats(data_origin)
    
    line_chart = LineChart(height=600, width=800, explicit_size=True, tooltip_fancy_mode=True)
    gauge_chart = GaugeChart(height=600, width=800, explicit_size=True, tooltip_fancy_mode=True)

    tracks = toDict(data, [], chart_type="tracklist")
    line = toDict(data, ['energy','liveness','acousticness','danceability'])
    gauge = toDict(data, ['energy','liveness','tempo','instrumentalness','loudness','popularity','acousticness','danceability'], chart_type="gauge", stat=data_max)

    # Cluster
    clusters = []

    clusters.append(plt.Circle((0.2,0.2),0.1, color='r', fc='none'))
    clusters.append(plt.Circle((0.2,0.8),0.1, color='g', fc='none'))
    clusters.append(plt.Circle((0.8,0.2),0.1, color='b', fc='none'))
    clusters.append(plt.Circle((0.8,0.8),0.1, color='y', fc='none'))

    fig, ax = plt.subplots(figsize=(8,6))
    
    dict_arrow = { '00': [ax,0.1,0.2,0.35,310,270,'black'], '01': [ax,0.2,0.2,0.45,0,0.05,'k'], '02': [ax,0.2,0.2,0,0.45,0.05,'k'], '03': [ax,0.2,0.2,0.5,0.49,0.05,'k'], \
                '11': [ax,0.1,0.8,0.35,310,270,'black'], '10': [ax,0.8,0.2,-0.45,0,0.05,'k'], '12': [ax,0.8,0.2,-0.5,0.49,0.05,'k'], '13': [ax,0.8,0.2,0,0.45,0.05,'k'], \
                '22': [ax,0.1,0.2,0.65,130,270,'black'], '20': [ax,0.2,0.8,0,-0.45,0.05,'k'], '21': [ax,0.2,0.8,0.5,-0.49,0.05,'k'], '23': [ax,0.2,0.8,0.45,0,0.05,'k'], \
                '33': [ax,0.1,0.8,0.65,130,270,'black'], '30': [ax,0.8,0.8,-0.5,-0.49,0.05,'k'], '31': [ax,0.8,0.8,0,-0.45,0.05,'k'], '32': [ax,0.8,0.8,-0.45,0,0.05,'k']
                }

    dict_color = { 0: 'black', 1: 'cyan', 2: 'magenta', 3: 'blue' }

    for i in clusters:
        ax.add_artist(i)

    ax.text(0.15,0.07,'Cluster 1')
    ax.text(0.75,0.07,'Cluster 2')
    ax.text(0.15,0.67,'Cluster 3')
    ax.text(0.75,0.67,'Cluster 4')
    ax.text(0.07,0.2,centers[1][-1])
    ax.text(0.6,0.2,centers[2][-1])
    ax.text(0.03,0.8,centers[3][-1])
    ax.text(0.67,0.8,centers[4][-1])

    dat_t = data_origin[1:,5:16]
    km = KMeans(n_clusters=4, n_init=20, max_iter=400)
    km.fit(dat_t)

    num = data[1:].shape[0]
    div = 0.2
    n_loop = 5
    if num < 5:
        div = 1/float(num)
        n_loop = num

    ind_cls = []
    for i in range(n_loop):
        ind_cls.append(range(int(num*div*i)+1,int(num*div*(i+1))+1))
    
    cls_global = []
    cls_local = []
    for i in range(n_loop):
        temp = np.mean(data[ind_cls[i],5:16].astype(float), axis=0)
        cls_global.append(str(km.predict(temp.reshape(1,-1))[0]))
        cls_local.append(data[-(i+1)][-1])

    for i in range(n_loop-1):
        to = cls_global[i]+cls_global[i+1]
        temp = dict_arrow[to]
        temp[-1] = dict_color[i]

        if cls_global[i] == cls_global[i+1]:
            drawCirc(temp)
        else:
            add_arrow(temp)

    plt.title('Global trend')
    plt.savefig("playlist/static/fig_global.png")
    fig_cls_global = Image.open("playlist/static/fig_global.png")

    plt.close()

    fig2, ax2 = plt.subplots(figsize=(8,6))

    dict_arrow2 = { '00': [ax2,0.1,0.2,0.35,310,270,'black'], '01': [ax2,0.2,0.2,0.45,0,0.05,'k'], '02': [ax2,0.2,0.2,0,0.45,0.05,'k'], '03': [ax2,0.2,0.2,0.5,0.49,0.05,'k'], \
                '11': [ax2,0.1,0.8,0.35,310,270,'black'], '10': [ax2,0.8,0.2,-0.45,0,0.05,'k'], '12': [ax2,0.8,0.2,-0.5,0.49,0.05,'k'], '13': [ax2,0.8,0.2,0,0.45,0.05,'k'], \
                '22': [ax2,0.1,0.2,0.65,130,270,'black'], '20': [ax2,0.2,0.8,0,-0.45,0.05,'k'], '21': [ax2,0.2,0.8,0.5,-0.49,0.05,'k'], '23': [ax2,0.2,0.8,0.45,0,0.05,'k'], \
                '33': [ax2,0.1,0.8,0.65,130,270,'black'], '30': [ax2,0.8,0.8,-0.5,-0.49,0.05,'k'], '31': [ax2,0.8,0.8,0,-0.45,0.05,'k'], '32': [ax2,0.8,0.8,-0.45,0,0.05,'k']
                }

    clusters = []

    clusters.append(plt.Circle((0.2,0.2),0.1, color='r', fc='none'))
    clusters.append(plt.Circle((0.2,0.8),0.1, color='g', fc='none'))
    clusters.append(plt.Circle((0.8,0.2),0.1, color='b', fc='none'))
    clusters.append(plt.Circle((0.8,0.8),0.1, color='y', fc='none'))

    for i in clusters:
        ax2.add_artist(i)

    ax2.text(0.15,0.07,'Cluster 1')
    ax2.text(0.75,0.07,'Cluster 2')
    ax2.text(0.15,0.67,'Cluster 3')
    ax2.text(0.75,0.67,'Cluster 4')
    ax2.text(0.05,0.2,centers[1][-1])
    ax2.text(0.6,0.2,centers[2][-1])
    ax2.text(0.03,0.8,centers[3][-1])
    ax2.text(0.67,0.8,centers[4][-1])

    for i in range(n_loop-1): 
        to2 = cls_local[i]+cls_local[i+1]
        temp2 = dict_arrow2[to2]
        temp2[-1] = dict_color[i]

        if cls_local[i] == cls_local[i+1]:
            drawCirc(temp2)
        else:
            add_arrow(temp2)

    plt.title('Local trend')
    plt.savefig("playlist/static/fig_local.png")
    fig_cls_local = Image.open("playlist/static/fig_local.png")

    plt.close()

    # Word cloud
    tags = ""
    for tag in data[:,-2]:
        try:
            tags += tag 
        except:
            continue

    wordcloud = WordCloud(background_color="white").generate(tags)
    image = wordcloud.to_image()
    image.save("playlist/static/temp.png")
    im = Image.open("playlist/static/temp.png")

#    recommended = data_origin[np.random.randint(data_origin.shape[0])]
    rec_ind = recommend(data[:,0], freq_songs)
    recommended = data_origin[np.where(data_origin[:,0]==rec_ind)].reshape(-1)
    recommended = str(recommended[3])+" - "+str(recommended[4])

    result = { 'song_list' : tracks, 'lineChart'  : line_chart.generate(line), 'gaugeChart' : gauge_chart.generate(gauge), \
                'tags' : im, 'recommended' : recommended, 'cls_global': fig_cls_global, 'cls_local': fig_cls_local }

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
    for i in range(5, dat[0].shape[0]-3):
        res[dat[0][i]] = dat[1:,i].astype(float).max()
    
    return res

def recommend(query, ranks):
    existing = query
    q = existing[-1]
    out = str(np.random.randint(3028))
    flag = 0
    for row in ranks:
        if q in row:
            for item in row:
                if item not in existing:
                    flag = 1
                    out = item
                    break
            if flag:
                break
    
    return out

def top_100(data):
    a = data[1:,-4].astype(int)
    b = np.argsort(a)[::-1]
    return data[1:][b][:101]

def findindex(data, li):
    indices = []
    for row in li:
        song = row.split(' - ')
        temp = data[np.where(data[:,3]==song[0])]
        temp2 = temp[np.where(temp[:,4]==song[1])]
        try:
            indices.append(int(temp2[0][0]))
        except:
            print "index error"
    
    return indices

def drawCirc(to):
    ax = to[0]
    radius = to[1]
    centX = to[2]
    centY = to[3]
    angle_ = to[4]
    theta2_ = to[5]
    color_ = to[6]

    arc = Arc([centX,centY],radius,radius,angle=angle_,
        theta1=0,theta2=theta2_,capstyle='round',linestyle='-',lw=3,color=color_)
    ax.add_patch(arc)

    #========Create the arrow head
    endX=centX+(radius/2)*np.cos(rad(theta2_+angle_)) #Do trig to determine end position
    endY=centY+(radius/2)*np.sin(rad(theta2_+angle_))

    ax.add_patch(                    #Create triangle as arrow head
        RegularPolygon(
            (endX, endY),            # (x,y)
            3,                       # number of vertices
            radius/5,                # radius
            rad(angle_+theta2_),     # orientation
            color=color_
        )
    )
#    ax.set_xlim([centX-radius,centY+radius]) and ax.set_ylim([centY-radius,centY+radius])

def add_arrow(to):
   to[0].arrow(to[1], to[2], to[3], to[4], head_width=to[5], head_length=to[5], fc=to[6], ec=to[6])

