# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from .charts import LineChart
from pygal.style import DarkStyle

import csv
import numpy as np

def index(request):
    
    dat_head = np.array(list(csv.reader(open("../audio_features_mod.csv", 'r'))))[0]
    dat = np.array(list(csv.reader(open("../audio_features_mod.csv", 'r'))))[100:110]
    dat = np.vstack((dat_head,dat))

    line_chart = LineChart(height=600, width=800, explicit_size=True)
   
    tracks = []
    for i in range(1, dat.shape[0]):
        tracks.append(str(dat[i][2])+" - "+str(dat[i][3]))

    line = toDict(dat, ['energy','liveness','acousticness','instrumentalness','danceability'])

    context = { 'song_list' : tracks, 'lineChart'  : line_chart.generate(line)}

    return render(request, 'playlist/index.html', context)

def toDict(dat, keys):
    cols = dict()

    for key in keys:
        cols[key] = list(dat[1:,np.where(dat[0]==key)[0][0]].astype(float))

    return cols

def play(request):
    result = ''
    result = gen_head(result)
    
    dat_head = np.array(list(csv.reader(open("../audio_features_mod.csv", 'r'))))[0]
    dat = np.array(list(csv.reader(open("../audio_features_mod.csv", 'r'))))[100:110]
    dat = np.vstack((dat_head,dat))

    columns = toDict(dat)

    result += charting_line(columns['tempo'])
    result += '</head>'

    result_tmp = '''<body>
<div class = "container-fluid">
<div class = "row-fluid">
<div class = "span7">
<div class = "fixed-bottom">
<nav>
<ul class="pager">
<li><a href="#">Next &rarr;</a></li>
</ul>
</nav>
</div>
<div id="chartContainer" style="height: 500px; width: 60%; position: absolute; top: 200px; right: 30px;"></div>
</div>
</div>
<div class = "span3">
<div class = "absolute">
<style>
div.absolute{
  position: absolute;
  width: 400px;
  left: 30px;
  top: 230px;
}
</style>
<h2>User Playlist</h2>
<div class="list-group">'''
    list_song_head = '''<a href="#" class="list-group-item list-group-item-action">'''

    for i in range(1,dat.shape[0]):
        if i == 5:
            list_song = '''<a href="#" class="list-group-item list-group-item-action list-group-item-primary">''' + dat[i][2] + " - " + dat[i][3] + '''</a>'''
            result_tmp += list_song
            continue
        list_song = list_song_head + dat[i][2] + " - " + dat[i][3]  + '''</a>'''
        result_tmp += list_song

    result_tmp += '''
</div>
</div>
</div>
</div>
</div>
<script src="https://canvasjs.com/assets/script/jquery-1.11.1.min.js"></script>
<script src="https://canvasjs.com/assets/script/jquery.canvasjs.min.js"></script>
</body></html>'''

    result += result_tmp
    return HttpResponse(result)

def charting_line(data):

    temp = str(data).replace("'", "")
    temp = temp.replace('u'+data[0].keys()[0], "x")
    temp = temp.replace(data[0].keys()[1], "y")

    result = '''<script>
window.onload = function () {

var chart = new CanvasJS.Chart("chartContainer",{
    title:{
        text: '''
    title_tmp = str(data[0].keys()[1])
    result += '"'+title_tmp+' flow"'
    result += '''
    },
    data:[{
        type: "line",
        dataPoints:'''
    result += temp
    result += '''
    }]});

    chart.render();
}
    
/*
var options = {
	animationEnabled: true,
	theme: "light2",
	title:{
		text: "Popularity"
	},
	axisY: {
		title: "Number of Sales",
		suffix: "K",
		minimum: 30
	},
	toolTip:{
		shared:true
	},
	legend:{
		cursor:"pointer",
		verticalAlign: "bottom",
		horizontalAlign: "left",
		dockInsidePlotArea: true,
		itemclick: toogleDataSeries
	},
	data: [{
		type: "line",
		showInLegend: true,
		name: "Projected Sales",
		markerType: "square",
		color: "#F08080",
		yValueFormatString: "#,##0K",
		dataPoints:'''
    result += temp
    result += '''
	}]
};
$("#chartContainer").CanvasJSChart(options);

function toogleDataSeries(e){
	if (typeof(e.dataSeries.visible) === "undefined" || e.dataSeries.visible) {
		e.dataSeries.visible = false;
	} else{
		e.dataSeries.visible = true;
	}
	e.chart.render();
}

}*/
</script>
'''

    return result


def gen_head(result):
    result = '''<!DOCTYPE HTML>
    <html>
    <head>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta/css/bootstrap.min.css" integrity="sha384-/Y6pD6FV/Vv2HJnA6t+vslU6fwYXjCFtcEpHbNJ0lyAFsXTsjBbfaDjzALeQsN6M" crossorigin="anonymous">
    <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.12.3/umd/popper.min.js" integrity="sha384-vFJXuSJphROIrBnz7yo7oB41mKfc8JzQZiCq4NCceLEaO4IHwicKwpJf9c9IpFgh" crossorigin="anonymous"></script>
<script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta/js/bootstrap.min.js" integrity="sha384-h0AbiXch4ZDo7tp9hKZ4TsHbi047NrKGLO3SEJAg45jXxnGIfYzk4Si90RDIqNm1" crossorigin="anonymous"></script>'''

    return result

