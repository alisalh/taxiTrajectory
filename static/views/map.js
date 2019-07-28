/**
 * Created by yan on 18-5-16.
 */
var bool_scatter_move_out_event = false;
var bool_scatter_move_in_event = true;

var height = 853; //window.innerHeight * 0.8368;
$("#map").height(height);
var dom = document.getElementById("map");
var selected_topics = [];
var mapchart = echarts.init(dom);
var app = {};
var map_line_width = 20;
var map_lines_data = null;
var map_lines_data_new = null;
var embedding_data = null;
var table_data = null;
var map_id = 0;
var detail_ids = [];
var time_speed_height = height * 0.351;
var time_dist_data_bk = null;
var time_speed_data_bk = null;

//getregiondist("6");
var bmap_option = {
    // title: {
    //     text: 'Trajectory View',
    //     textStyle: {
    //         fontSize: 12
    //     }
    // },
    tooltip: {},
    toolbox: {
        showTitle: true,
        // show: true,
        itemSize: 20,
        zlevel: 1000,
        // left:'left' ,
        top: 8,
        right: 6,
        feature: {
            myTool1: {
                show: true,
                title: "reset",
                icon: 'image://static/images/reset.png',
                onclick: function () {
                    // map_option.series[0].data = map_lines_data;
                    map_option.series[1].data = [];
                    update_by_topics();
                    // mapchart.setOption(map_option, true);
                    // $("#similar_sub_trajectory").children().remove();
                    bool_scatter_move_out_event = false;
                    bool_scatter_move_in_event = true;
                    map_id = map_coords.length-1;
                    detail_ids = [];
                    ////////////////////
                    start_time_span_option.series = time_dist_data_bk;
                    start_time_span_chart.setOption(start_time_span_option, true);
                    //////////////////////
                    var time_speed_width = $("#time_speed_chart").parent().width();
                    var seg_height = (time_speed_height - 40) / 2 / 8;
                    time_speed_chart.segmentHeight(seg_height)
                        .innerRadius(seg_height).margin({
                        top: 20,
                        right: time_speed_width / 2 - seg_height * 8,
                        bottom: 20,
                        left: time_speed_width / 2 - seg_height * 8
                    });
                    d3.select("#time_speed_chart").selectAll("svg").remove();
                    d3.select("#time_speed_chart").selectAll("svg").data([time_speed_data_bk])
                        .enter()
                        .append('svg').attr("height", time_speed_height).attr("width", time_speed_width)
                        .call(time_speed_chart);
                    // start_time_option.series[0].data = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
                    // start_time_chart.setOption(start_time_option, true);
                    //
                    // time_span_option.series[0].data = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
                    // time_span_chart.setOption(time_span_option, true);
                }
            }
        }
    },
    // bmap: {
    //     center: [104.06, 30.65],
    //     zoom: 13,
    //     roam: true,
    //     mapStyle: {
    //         styleJson: [{
    //             'featureType': 'water',
    //             'elementType': 'all',
    //             'stylers': {
    //                 'color': '#d1d1d1'
    //             }
    //         }, {
    //             'featureType': 'land',
    //             'elementType': 'all',
    //             'stylers': {
    //                 'color': '#f3f3f3'
    //             }
    //         }, {
    //             'featureType': 'railway',
    //             'elementType': 'all',
    //             'stylers': {
    //                 'visibility': 'off'
    //             }
    //         }, {
    //             'featureType': 'highway',
    //             'elementType': 'all',
    //             'stylers': {
    //                 'color': '#999999'
    //             }
    //         }, {
    //             'featureType': 'highway',
    //             'elementType': 'labels',
    //             'stylers': {
    //                 'visibility': 'off'
    //             }
    //         }, {
    //             'featureType': 'arterial',
    //             'elementType': 'geometry',
    //             'stylers': {
    //                 'color': '#fefefe'
    //             }
    //         }, {
    //             'featureType': 'arterial',
    //             'elementType': 'geometry.fill',
    //             'stylers': {
    //                 'color': '#fefefe'
    //             }
    //         }, {
    //             'featureType': 'poi',
    //             'elementType': 'all',
    //             'stylers': {
    //                 'visibility': 'off'
    //             }
    //         }, {
    //             'featureType': 'green',
    //             'elementType': 'all',
    //             'stylers': {
    //                 'visibility': 'off'
    //             }
    //         }, {
    //             'featureType': 'subway',
    //             'elementType': 'all',
    //             'stylers': {
    //                 'visibility': 'off'
    //             }
    //         }, {
    //             'featureType': 'manmade',
    //             'elementType': 'all',
    //             'stylers': {
    //                 'color': '#d1d1d1'
    //             }
    //         }, {
    //             'featureType': 'local',
    //             'elementType': 'all',
    //             'stylers': {
    //                 'color': '#d1d1d1'
    //             }
    //         }, {
    //             'featureType': 'arterial',
    //             'elementType': 'labels',
    //             'stylers': {
    //                 'visibility': 'off'
    //             }
    //         }, {
    //             'featureType': 'boundary',
    //             'elementType': 'all',
    //             'stylers': {
    //                 'color': '#fefefe'
    //             }
    //         }, {
    //             'featureType': 'building',
    //             'elementType': 'all',
    //             'stylers': {
    //                 'color': '#d1d1d1'
    //             }
    //         }, {
    //             'featureType': 'label',
    //             'elementType': 'labels.text.fill',
    //             'stylers': {
    //                 'color': 'rgba(0,0,0,0)'
    //             }
    //         }]
    //     }
    // }
    leaflet: {
        center: [104.0639, 30.6592], //[114.13, 22.64],
        zoom: 13,
        roam: true,
        layerControl: {
            position: 'topright'
        },
        mapStyle:
            {
                "id": "background",
                "type": "background",
                "paint": {
                    "background-color": "rgb(242,243,240)"
                }
            },
        tiles: [{
            label: 'Open Street Map',
            //urlTemplate: 'https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png'

            urlTemplate:  'http://cache1.arcgisonline.cn/ArcGIS/rest/services/ChinaOnlineStreetGray/MapServer/tile/{z}/{y}/{x}'
            //'http://t3.tianditu.com/DataServer?T=vec_w&x={x}&y={y}&l={z}'
           // options: {
            //     attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>, Tiles courtesy of <a href="http://hot.openstreetmap.org/" target="_blank">Humanitarian OpenStreetMap Team</a>'
            // }
        }

        ]
    }
};

var map_option = {
    brush: {
        toolbox: ['rect', 'polygon', 'keep', 'clear'],
        xAxisIndex: 0,
        throttleType: 'debounce',
        throttleDelay: 300
        // geoIndex: 'leaflet'
    },
    // geo: {
    //     map: 'china',
    //     center: [104.06, 30.65],
    //     zoom: 13,
    //     roam: true,
    //     z: 10000
    // },
    series: [
        {
            type: 'lines',
            coordinateSystem: 'leaflet',
            polyline: true,
            zlevel: 20,
            // data: lines,
            // large: true,
            // progressive: 400,
            // progressiveThreshold: 3000,
            animation: false,
            symbol: 'arrow',
            symbolSize: 12,
            effect: {
                show: true,
                period: 50,
                trailLength: 0,
                symbol: 'arrow',
                symbolSize: 10
            },
            emphasis: {
                lineStyle: {
                    color: '#9e0142'
                    // opacity: 0.1
                }
            }
        },
        {
            type: 'lines',
            coordinateSystem: 'leaflet',
            polyline: true,
            zlevel: 10,
            // data: lines,
            // large: true,
            // progressive: 400,
            // progressiveThreshold: 3000,
            animation: false,
            symbol: 'arrow',
            symbolSize: 5,

            effect: {
                show: true,
                period: 50,
                trailLength: 0,
                symbol: 'arrow',
                symbolSize: 4
            },
            emphasis: {
                lineStyle: {
                    color: '#1f78b4'
                    // opacity: 0.1
                }
            }
        },
        {
            type: 'scatter',
            coordinateSystem: 'leaflet',
            zlevel: 2,
            symbolSize: 0
        }
    ]
};
map_option = $.extend(map_option, bmap_option);
// map_option = bmap_option;
//
$("#map").dblclick(map_interactive_change, function () {
    map_option.leaflet.roam = !map_option.leaflet.roam;
    map_interactive_change();
});
function map_interactive_change() {
    // map_option.leaflet.roam = !map_option.leaflet.roam;
    var roam = map_option.leaflet.roam;
    var leaflet = map_coords[map_id].getLeaflet();
    if (roam && roam !== 'move') {
        leaflet.scrollWheelZoom.enable();
        leaflet.touchZoom.enable();
        leaflet.dragging.enable()
      } else {
        leaflet.scrollWheelZoom.disable();
        leaflet.touchZoom.disable();
        leaflet.dragging.disable()
      }
}

var topic_bar_height = height * 0.315+3;
$("#topic_bar").height(topic_bar_height);
var topic_bar_dom = document.getElementById("topic_bar");
var topic_bar_chart = echarts.init(topic_bar_dom);
var topic_bar_option = {
    tooltip : {
        trigger: 'axis',
        axisPointer : {            // 坐标轴指示器，坐标轴触发有效
            type : 'shadow'        // 默认为直线，可选为：'line' | 'shadow'
        }
    },
    grid: {
        left: '1%',
        right: '4%',
        bottom: '0%',
        top: '5%',
        containLabel: true
    },
    xAxis : [
        {
            type : 'category',
            data : topics,
            axisTick: {
                alignWithLabel: true
            }
        }
    ],
    yAxis : [
        {
            type : 'value',
            axisLabel: {
                show: false
            }
        }
    ],
    series : [
        {
            // name:'直接访问',
            type:'bar',
            barWidth: '60%'
        }
    ],
     itemStyle:{
        color: function (params) {
            var rgb = hexToRgb(topic_colors[params.data[0]]);
            if(params.data[2] === 1){
                return 'rgba('+rgb.r +","+rgb.g+','+ rgb.b+',' +1.0+')';
            }else {
                return 'rgba('+rgb.r +","+rgb.g+','+ rgb.b+',' +0.3+')';
            }

        }
    }
};


function update_topic_region(lines_data) {
    var lines = [];
    for (var i = 0; i < lines_data.length; i++) {
        var line_data = lines_data[i][0];
        var coords = [];
        for (var j = 0; j < line_data.length; j++) {
            coords.push(line_data[j]);
        }
        lines.push({
            "coords": coords, index: lines_data[i][10], "id": lines_data[i][3], "lineStyle": {
                "normal": {
                    "color": topic_colors[lines_data[i][1]], //"opacity": 0.6,
                    "width": Math.sqrt(lines_data[i][2]) * map_line_width,
                    'opacity': 0.5
                }
            }
        });
    }

    map_lines_data = lines;

    map_option.series[0].data = lines;
    var map_center_scatter = lines_data.map(function (d) {return d[8]});
    // var map_center_scatter = lines[0]['coords'];
    map_option.series[2].data = map_center_scatter;
    mapchart.setOption(map_option, true);
    // mapchart.on('brushSelected', mapBrushSelected);
    // if (!app.inNode) {
    //     // 添加百度地图插件
    //     var bmap = mapchart.getModel().getComponent('bmap').getBMap();
    //     //bmap.addControl(new BMap.MapTypeControl());
    //     //$(".anchorBL").remove();
    //     //$('.BMap_cpyCtrl').remove();
    //     // $(".anchorBL").remove();
    // }

}

function gettopicregiondist() {
    var min_trajectory_length = $("#min_trajectory_length").slider('getValue');
    var min_support = $("#min_support").slider('getValue');
    var min_confidence = $("#min_confidence").slider('getValue');
    var topic_threshold = $("#topic_threshold").slider("getValue");
    $.post('/gettopicregion/', {
        "min_support": min_support, "min_confidence": min_confidence,
        "min_trajectory_length": min_trajectory_length, "topic_threshold": topic_threshold
    }, function (jsondata) {
        var topic_dist = jsondata.data.topic;
        topic_bar_option.series[0].data = topic_dist;
        for(var i=0;i<topic_dist.length;i++){
            selected_topics.push(topic_dist[i][0]);
        }
        topic_bar_chart.setOption(topic_bar_option, true);
        topic_bar_chart.on("click", topic_bar_click);
        var topic_phrase_data = jsondata.data.topic_phrase;
        console.log(topic_phrase_data);
        update_topic_region(topic_phrase_data);
        var phrase_embedding_data = jsondata.data.embedding;
        console.log(phrase_embedding_data);
        phrase_embedding_option.series[0].data = phrase_embedding_data;
        embedding_data = phrase_embedding_data;
        phrase_embedding_chart.setOption(phrase_embedding_option, true);
        create_sub_trajectory_table(topic_phrase_data, null);
        table_data = topic_phrase_data;
        //////////////////////
        var time_dist_data = jsondata.data.time_dist;
        start_time_span_option.series = time_dist_data;
        start_time_span_chart.setOption(start_time_span_option, true);
        //////////////////////
        var time_speed_data = jsondata.data.time_speed;
        var time_speed_width = $("#time_speed_chart").parent().width();
        var seg_height = (time_speed_height - 40) / 2 / 8;
        time_speed_chart.segmentHeight(seg_height)
            .innerRadius(seg_height).margin({
            top: 20,
            right: time_speed_width / 2 - seg_height * 8,
            bottom: 20,
            left: time_speed_width / 2 - seg_height * 8
        });
        d3.select("#time_speed_chart").selectAll("svg").remove();
        d3.select("#time_speed_chart").selectAll("svg").data([time_speed_data])
            .enter()
            .append('svg').attr("height", time_speed_height).attr("width", time_speed_width)
            .call(time_speed_chart);
        time_dist_data_bk = time_dist_data;
        time_speed_data_bk = time_speed_data;
        /////////////////////
    });
}

function update_by_topics() {
  $.post('/gettopicregionbytopic/', {"topics": JSON.stringify(selected_topics)}, function (jsondata) {
        var indexes = jsondata.data.search;
        console.log(indexes);

        var phrase_embedding_data = embedding_data;
        for(var pei=0;pei<phrase_embedding_data.length;pei++){
            phrase_embedding_data[pei][3] = 0.2;
            // map_lines_data[pei]['lineStyle']['color'] = 'rgba(128, 128, 128, 0)';
        }
        var lines_new = [];
        var table_data_new = [];
        for(var i=0;i<indexes.length;i++){
            phrase_embedding_data[indexes[i]][3] = 1.0;
            // phrase_embedding_data.push(embedding_data[indexes[i]]);
            table_data_new.push(table_data[indexes[i]]);
            lines_new.push(map_lines_data[indexes[i]]);
            // map_lines_data[indexes[i]]['lineStyle']['width'] = Math.sqrt(table_data[indexes[i]][2]) * map_line_width;

        }
        map_option.series[0].data = lines_new;
        map_lines_data_new = lines_new;
        // var map_center_scatter = map_lines_data.map(function (d) {return d[8]});
        // map_option.series[2].data = map_center_scatter;
        mapchart.setOption(map_option, true);

        phrase_embedding_option.series[0].data = phrase_embedding_data;
        phrase_embedding_chart.setOption(phrase_embedding_option, true);
        create_sub_trajectory_table(table_data_new, null);
        //////////
        //////////////////////
        var time_dist_data = jsondata.data.time_dist;
        start_time_span_option.series = time_dist_data;
        start_time_span_chart.setOption(start_time_span_option, true);
        //////////////////////
        var time_speed_data = jsondata.data.time_speed;
        var time_speed_width = $("#time_speed_chart").parent().width();
        var seg_height = (time_speed_height - 40) / 2 / 8;
        time_speed_chart.segmentHeight(seg_height)
            .innerRadius(seg_height).margin({
            top: 20,
            right: time_speed_width / 2 - seg_height * 8,
            bottom: 20,
            left: time_speed_width / 2 - seg_height * 8
        });
        d3.select("#time_speed_chart").selectAll("svg").remove();
        d3.select("#time_speed_chart").selectAll("svg").data([time_speed_data])
            .enter()
            .append('svg').attr("height", time_speed_height).attr("width", time_speed_width)
            .call(time_speed_chart);
        time_dist_data_bk = time_dist_data;
        time_speed_data_bk = time_speed_data;
        /////////////////////
        console.log("done");
    });
}
function topic_bar_click(params) {
    console.log(params);
    if(params.componentSubType==="bar"){
        var row = params.data[0];
        var index = selected_topics.indexOf(row);
        if (index > -1) {
            selected_topics.splice(index, 1);
            topic_bar_option.series[0].data[row][2] = 0;
        }else {
            selected_topics.push(row);
            topic_bar_option.series[0].data[row][2] = 1;
        }
        topic_bar_chart.setOption(topic_bar_option, true);
        update_by_topics();
    }
}
$("#min_support").slider().on("slideStop", gettopicregiondist);
$("#min_confidence").slider().on("slideStop", gettopicregiondist);
$("#min_trajectory_length").slider().on("slideStop", gettopicregiondist);

gettopicregiondist();
// mapchart.setOption(map_option, true);
//

function mapBrushSelected (params) {
    console.log("map brush");
    var brushComponent = params.batch[0];
    var new_brush_data = [];
    var new_brush_tabel_index_data = [];
    for (var sIdx = 0; sIdx < brushComponent.selected.length; sIdx++) {
        var rawIndices = brushComponent.selected[sIdx].dataIndex;
        for(var j =0; j<rawIndices.length;j++){
            new_brush_data.push(map_lines_data[rawIndices[j]]);
            new_brush_tabel_index_data.push(rawIndices[j]);
        }
    }
    // console.log(new_brush_tabel_index_data);
    // if(map_option.leaflet.roam === true && new_brush_tabel_index_data.length === 0){
    //     map_option.leaflet.roam = false;
    //     map_interactive_change();
    // }
    // if(map_option.leaflet.roam === false && new_brush_tabel_index_data.length === 0){
    //     map_option.leaflet.roam = true;
    //     map_interactive_change();
    // }
    if(new_brush_tabel_index_data.length !== 0){
        for(var i=0; i < embedding_data.length;i++) {
            embedding_data[i][3] = 0.1;
        }
        for(i=0; i < new_brush_tabel_index_data.length;i++){
            embedding_data[new_brush_tabel_index_data[i]][3] = 1.0;
        }
    } else {
        for(var i=0; i < embedding_data.length;i++){
            embedding_data[i][3] = 1.0;
        }
        new_brush_tabel_index_data = null;
    }
    phrase_embedding_option.series[0].data = embedding_data;
    phrase_embedding_chart.setOption(phrase_embedding_option, true);
    create_sub_trajectory_table(table_data, new_brush_tabel_index_data);
    // map_option.series[0].data = new_brush_data;
    // mapchart.setOption(map_option, true);
}

// function filter_topic_region_by_topics(topics) {
//     $.post('/gettopicregionbytopic/', {"topics": JSON.stringify(topics)}, function (jsondata) {
//         var data = jsondata.data.data;
//         console.log(data);
//         update_topic_region(data);
//     });
// }

// var start_time_option = {
//     title: {
//         text: 'Taxi Time Distribution of a trajectory',
//         textStyle:{
//             fontSize: 12
//         }
//     },
//     grid: {
//         left: 0,
//         top: 30,
//         right: 0,
//         bottom: 15,
//         containLabel: true
//     },
//     xAxis: {
//         type: 'category',
//         data: hours
//     },
//     yAxis: {
//         type: 'value'
//     },
//     series: [{
//         type: 'bar',
//         data: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
//     }]
// };
//
// var start_time_height = window.innerHeight * 0.33;
// $("#start_time_bar").height(start_time_height);
// var start_time_dom = document.getElementById("start_time_bar");
// var start_time_chart = echarts.init(start_time_dom);
// start_time_chart.setOption(start_time_option);

var start_time_span_option = {
    // title: {
    //     text: 'Taxi Pick-up Time and Interval Distribution of a trajectory',
    //     textStyle:{
    //         fontSize: 12
    //     }
    // },
    legend: {
        data: ['0-10km', '10-20km', '20-30km', '>30km']
    },
    grid: {
        left: 0,
        top: 30,
        right: 0,
        bottom: 15,
        containLabel: true
    },
    xAxis: {
        type: 'category',
        data: ['6-8am', '9-11am', '12-2pm', '3-5pm', '6-8pm', '9-11pm']
    },
    yAxis: {
        type: 'value'
    }
    // series:
};

var start_time_span_height = height*0.279+7;
$("#start_time_span_bar").height(start_time_span_height);
var start_time_span_dom = document.getElementById("start_time_span_bar");
var start_time_span_chart = echarts.init(start_time_span_dom);
start_time_span_chart.setOption(start_time_span_option);


function hexToRgb(hex) {
    var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : null;
}

var phrase_embedding_option = {
    // title: {
    //     text: 'Sub-trajectory Embedding',
    //     textStyle: {
    //         fontSize: 12
    //     }
    // },
    brush: {
        toolbox: ['rect', 'polygon', 'keep', 'clear'],
        xAxisIndex: 0,
        throttleType: 'debounce',
        throttleDelay: 300,
        outOfBrush: {
            colorAlpha: 0.1
        }
    },
    xAxis: {
        show: false,
        axisLabel:{
            show: false
        },
        axisLine:{
          show: false
        },
        splitLine:{
            show: false,
            interval: 2
         }
    },
    yAxis: {
         show: false,
         axisLabel:{
            show: false
         },
         axisLine:{
          show: false
        },
        splitLine:{
            show: false,
            interval: 2
         }
    },
    grid: {
        left: 3,
        top: 25,
        right: 10,
        bottom: 3,
        containLabel: true,
        show: true,
        borderWidth: 1,
        borderColor: "#252525"
    },
    series: [{
        symbolSize: function (params) {
            //console.log(params);
            return Math.sqrt(params[6])*30;
        },
        type: 'scatter'
    }],
    itemStyle:{
        color: function (params) {
            var rgb = hexToRgb(topic_colors[params.data[2]]);
            return 'rgba('+rgb.r +","+rgb.g+','+ rgb.b+',' + params.data[3]+')';
        }
    }
};

var phrase_embedding_height = height * 0.424;
$("#phrase_embedding").height(phrase_embedding_height);
var phrase_embedding_dom = document.getElementById("phrase_embedding");
var phrase_embedding_chart = echarts.init(phrase_embedding_dom);


// phrase_embedding_chart.setOption(phrase_embedding_option);
phrase_embedding_chart.on('mouseover', function (params) {
    console.log(params); // do whatever you want with another chart say chartTwo here
    if (params.seriesType === 'scatter'&& bool_scatter_move_in_event === true) {
        // var data_id = params.data.id;
        var data_index = params.dataIndex;
        //map_lines_data[data_index].lineStyle.normal.color = "#ffff00";
        //update_detail(data_id, data_index, null);
        map_option.series[0].data = [map_lines_data[data_index]];
        mapchart.setOption(map_option, true);
        bool_scatter_move_out_event = true;
        bool_scatter_move_in_event = false;
    }
});
phrase_embedding_chart.on('mouseout', function (params) {
    console.log(params); // do whatever you want with another chart say chartTwo here
    if (params.seriesType === 'scatter' && bool_scatter_move_out_event === true) {
        // var data_id = params.data.id;
        // var data_index = params.dataIndex;
        //map_lines_data[data_index].lineStyle.normal.color = "#ffff00";
        //update_detail(data_id, data_index, null);
        map_option.series[0].data = map_lines_data_new;
        mapchart.setOption(map_option, true);
        bool_scatter_move_out_event = false;
        bool_scatter_move_in_event = true;
    }
});
phrase_embedding_chart.on('click', function (params) {
    console.log(params); // do whatever you want with another chart say chartTwo here
    if (params.seriesType === 'scatter') {
        var data_index = params.dataIndex;
        var data_id = map_lines_data[data_index].id;
        //map_lines_data[data_index].lineStyle.normal.color = "#ffff00";
        bool_scatter_move_out_event = false;
        bool_scatter_move_in_event = false;
        var centre = map_lines_data[data_index]['coords'];
        var x_sum =0;
        var y_sum =0;
        for(var i=0; i< centre.length; i++){
            x_sum += centre[i][0];
            y_sum += centre[i][1];
        }
        var x_mean = x_sum/centre.length;
        var y_mean = y_sum/centre.length;
        var id_name = "#"+data_id+"_"+data_index;
        //console.log($(id_name).offset().top);
        //$('#sub_traj_table').parent().animate({
        //    scrollTop: 0
        //}, 200);
        //$('#sub_traj_table').parent().animate({
        //    scrollTop: $(id_name).offset().top-30
        //}, 2000);
        $('#sub_traj_table').parent().animate({
            scrollTop: 0
        }, 200);
        $('#sub_traj_table').parent().animate({
            scrollTop: $(id_name).offset().top-30
        }, 2000);
        //console.log($('#sub_traj_table').scrollTop());
        update_detail(data_id, data_index, [x_mean, y_mean]);

    }
});

phrase_embedding_chart.on('brushSelected', renderBrushed);

function renderBrushed(params) {
    if(bool_scatter_move_in_event || bool_scatter_move_out_event){
        var brushComponent = params.batch[0];
        var new_brush_data = [];
        var new_brush_table_index_data = [];
        for (var sIdx = 0; sIdx < brushComponent.selected.length; sIdx++) {
            var rawIndices = brushComponent.selected[sIdx].dataIndex;
            for(var j =0; j<rawIndices.length;j++){
                if(selected_topics.indexOf(embedding_data[rawIndices[j]][2]) !== -1){
                    new_brush_data.push(map_lines_data[rawIndices[j]]);
                    new_brush_table_index_data.push(rawIndices[j]);
                }
            }
        }
        if(new_brush_data.length === 0){
            map_option.series[0].data = map_lines_data_new;
            new_brush_table_index_data = null;
        }else {
            map_option.series[0].data = new_brush_data;
        }
        if(new_brush_data.length !== 0){
            $.post('/getdetailbyid/', {"id": JSON.stringify(new_brush_table_index_data)}, function (jsondata) {
                var data = jsondata.data;
                console.log(data);
                var start_time_span_data = data['start_time_span'];
                // var start_time_data = data['start_time'];
                var time_speed_data = data['time_speed'];

                start_time_span_option.series = start_time_span_data;
                start_time_span_chart.setOption(start_time_span_option, true);

                //////////////////////
                var time_speed_width = $("#time_speed_chart").parent().width();
                var seg_height = (time_speed_height - 40) / 2 / 8;
                time_speed_chart.segmentHeight(seg_height)
                    .innerRadius(seg_height).margin({
                    top: 20,
                    right: time_speed_width / 2 - seg_height * 8,
                    bottom: 20,
                    left: time_speed_width / 2 - seg_height * 8
                });
                d3.select("#time_speed_chart").selectAll("svg").remove();
                d3.select("#time_speed_chart").selectAll("svg").data([time_speed_data])
                    .enter()
                    .append('svg').attr("height", time_speed_height).attr("width", time_speed_width)
                    .call(time_speed_chart);
                /////////////////////
            });
        }else{
             ////////////////////
            start_time_span_option.series = time_dist_data_bk;
            start_time_span_chart.setOption(start_time_span_option, true);
            //////////////////////
            var time_speed_width = $("#time_speed_chart").parent().width();
            var seg_height = (time_speed_height - 40) / 2 / 8;
            time_speed_chart.segmentHeight(seg_height)
                .innerRadius(seg_height).margin({
                top: 20,
                right: time_speed_width / 2 - seg_height * 8,
                bottom: 20,
                left: time_speed_width / 2 - seg_height * 8
            });
            d3.select("#time_speed_chart").selectAll("svg").remove();
            d3.select("#time_speed_chart").selectAll("svg").data([time_speed_data_bk])
                .enter()
                .append('svg').attr("height", time_speed_height).attr("width", time_speed_width)
                .call(time_speed_chart);
        }

        mapchart.setOption(map_option, true);
        create_sub_trajectory_table(table_data, new_brush_table_index_data);
    }

}
// phrase_embedding_chart.on('click', function (params) {
//     console.log(params); // do whatever you want with another chart say chartTwo here
//     if (params.seriesType === 'scatter') {
//         var data_id = params.data.id;
//         var data_index = params.dataIndex;
//         //map_lines_data[data_index].lineStyle.normal.color = "#ffff00";
//         update_detail(data_id, data_index, null);
//     }
// });

var time_speed_chart = circularHeatChart()
// .segmentHeight(20)
// .innerRadius(20)
    .numSegments(18)
    .range(["#1a9641", "#a6d96a", "#ffffbf", "#fdae61", "#d7191c"])
    .radialLabels(["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", ">60"])
    .segmentLabels(["6am", "7am", "8am", "9am", "10am", "11am",
        "12am", "1pm", "2pm", "3pm", "4pm", "5pm", "6pm", "7pm", "8pm", "9pm", "10pm", "11pm"]);
// .margin({top: 20, right: 20, bottom: 20, left: 20});

// d3.select("#time_speed_chart").selectAll("svg").data([])
//     .enter()
//     .append('svg')
//     .call(time_speed_chart);
var sub_traj_height = height * 0.303;
$("#sub_traj_table").parent().height(sub_traj_height);
function create_sub_trajectory_table(table_data, sort_index) {
    $("#sub_traj_table").children().remove();
    if(sort_index===null || sort_index===undefined){
        sort_index = [...Array(table_data.length).keys()];
    }
    var table = document.getElementById('sub_traj_table');
    var colum_index = [4, 1, 2, 5, 6];
    var tr = [];
    for (var si = 0; si < sort_index.length; si++) {
        var i = sort_index[si];
        tr[i] = document.createElement('a');
        tr[i].classList.add('list-group-item');
        tr[i].id = table_data[i][3] + "_" + table_data[i][10];
        // tr.href = "#";
        if(selected_topics.indexOf(table_data[i][colum_index[1]]) === -1){
            continue
        };
        var road_name_list = document.createElement('div');
        for (var j = 0; j < table_data[i][colum_index[0]].length; j++) {
            var road_name = document.createElement('p');
            road_name.classList.add("label");
            road_name.style['background-color'] = topic_colors[table_data[i][colum_index[1]]];
            road_name.style.color = 'white';
            road_name.style['font-size'] = '11px';
            //road_name.style['line-height'] = '1';
            //road_name.style['text-size-adjust'] = 'none';
            var road_name_text = document.createTextNode(table_data[i][colum_index[0]][j]);
            road_name.appendChild(road_name_text);
            road_name_list.appendChild(road_name);
            if (j !== table_data[i][colum_index[0]].length - 1) {
                var arrow = document.createElement('span');
                //var road_name_text = document.createTextNode(table_data[i][colum_index[0]][j]);
                //road_name.appendChild(road_name_text);
                arrow.classList.add("glyphicon");
                arrow.classList.add("glyphicon-arrow-right");
                road_name_list.appendChild(arrow);
            }

        }

        tr[i].appendChild(road_name_list);

        // var meta_name = document.createElement('p');
        // meta_name.style['font-size'] = '10px';
        // var meta_name_text = document.createTextNode("support: " + table_data[i][colum_index[2]] + " subtrajectory distance: " + table_data[i][colum_index[4]]);
        // meta_name.appendChild(meta_name_text);
        var meta_name = document.createElement('div');
        var support_svg = d3.select(meta_name).append("svg").attr("width", "400").attr("height", "40");

        support_svg.append("text").attr("y", 18).style("font-size", '14px').text("topic:");
        var topic_x = [60];
        for(var k=0; k<table_data[i][9].length;k++){
            var x_tmp = topic_x[k] + table_data[i][9][k]*340;
            topic_x.push(x_tmp);
        }
        support_svg.selectAll("rect.topic").data(table_data[i][9]).enter().append("rect")
            .attr("width", 10).attr("height", "14").attr("y", 8)
            .attr("x", function(d, i){
                return topic_x[i];
            }).attr("width", function(d){
            return d*340;
        }).attr("fill", function(d, i){
            return topic_colors[i];
        });

        support_svg.append("text").attr("y", 38).style("font-size", '14px').text("support:");
        support_svg.append("rect").attr("y", 28).attr("x", "60px").attr("width", table_data[i][colum_index[2]]*map_line_width*100)
            .attr("fill", "#91bfdb").attr("height", "14");

        support_svg.append("text").attr("x", 150).attr("y", 38).style("font-size", '14px').text("distance:");
        support_svg.append("rect").attr("y", 28).attr("x", "220px").attr("width", table_data[i][colum_index[4]]*10)
            .attr("fill", "#fc8d59").attr("height", "14");


        tr[i].appendChild(meta_name);

        tr[i].addEventListener("click", function () {
            var id_value = $(this).attr('id');
            var field_values = id_value.split("_");
            var centre = map_lines_data[parseInt(field_values[1])]['coords'];
            var x_sum =0;
            var y_sum =0;
            for(var i=0; i< centre.length; i++){
                x_sum += centre[i][0];
                y_sum += centre[i][1];
            }
            var x_mean = x_sum/centre.length;
            var y_mean = y_sum/centre.length;
            update_detail(parseInt(field_values[0]), parseInt(field_values[1]), [x_mean, y_mean]);
        });
        table.appendChild(tr[i]);
    }
    // $('#sub_traj_table').removeAttr('width').DataTable({
    //     scrollY:        "200px",
    //     scrollX:        true,
    //     scrollCollapse: true,
    //     // paging:         false,
    //     columnDefs: [
    //         { width: 50,  targets: 0}
    //     ],
    //     fixedColumns: {
    //         leftColumns: 1
    //     },
    //     searching:false,
    //     pagingType: 'simple'
    //  });
    // // $('td.traj').css("white-space","nowrap");
    // // $('td.traj').css("overflow", "hidden");
    // // $('td.traj').width("10px");
    // $('td.traj div').css("white-space","nowrap");
    // $('td.traj div').css("overflow", "hidden");
    // // $('td.traj div').width("10px");
    // // $('.dataTables_length').addClass('bs-select');
    // $("#sub_traj_table_length").remove();
}

function create_table(table_data) {
    // // $("#detail_table").DataTable.destory();
    // // $("#detail_table").empty();
    if (detail_table !== null) {
        detail_table.destroy();
    }
    // // $("#detail_table tbody").children().remove();
    // $("#detail_table").empty();
    // var table = document.getElementById('detail_table');
    // var thead = document.createElement('thead');
    // var heads = ['Taxi ID', 'PickUp_P', 'DropOff_P', 'PickUp_T', 'DropOff_T', 'Avg_Spd', 'Max_Spd', 'Min_Spd', 'Dist'];
    // for(var hi =0; hi < 9; hi++){
    //     var th = document.createElement('th');
    //         // td.setAttribute("class", 'filterable-cell');
    //     var text = document.createTextNode(heads[hi]);
    //     th.appendChild(text);
    //     thead.appendChild(th);
    // }
    // table.appendChild(thead);
    //
    // var tbody = document.createElement('tbody');
    // var tr = [];
    // for (var i = 0; i < table_data.length; i++){
    //     tr[i] = document.createElement('tr');
    //     for (var j = 0; j < 9; j++){
    //         var td = document.createElement('td');
    //         // td.setAttribute("class", 'filterable-cell');
    //         var text = document.createTextNode(table_data[i][j]);
    //         td.appendChild(text);
    //         tr[i].appendChild(td);
    //     }
    //     tbody.appendChild(tr[i]);
    //
    // }
    // table.appendChild(tbody);
    detail_table = $('#detail_table').DataTable({
        columns: [{title: 'Taxi ID'}, {title: 'PickUp_P'}, {title: 'DropOff_P'}, {title: 'PickUp_T'}, {title: 'DropOff_T'}, {title: 'Avg_Spd'}, {title: 'Max_Spd'}, {title: 'Min_Spd'}, {title: 'Dist'}],
        data: table_data,
        scrollY: "200px",
        scrollCollapse: true,
        searching: false,
        pagingType: 'simple'
    });
    $('#detail_table').addClass('bs-select');
    $("#detail_table_length").remove();

}
var detail_table = null;
$("#detail_table").height(window.innerHeight * 0.33);

function update_detail_by_ids(data_ids, centre) {
    $.post('/getdetailbyid/', {"id": JSON.stringify(data_ids)}, function (jsondata) {
        var data = jsondata.data;
        console.log(data);
        var start_time_span_data = data['start_time_span'];
        // var start_time_data = data['start_time'];
        var time_speed_data = data['time_speed'];
        var table_data = data['table'];
        // var sim_phrase_data = data['sim_phrase'];
        // start_time_option.series[0].data = start_time_data;
        // start_time_chart.setOption(start_time_option, true);

        start_time_span_option.series = start_time_span_data;
        start_time_span_chart.setOption(start_time_span_option, true);

        var lines_data = data['docs'];
        var ext_lines = [];
        for (var i = 0; i < lines_data.length; i++) {
            var line_data = lines_data[i];
            var coords = [];
            for (var j = 0; j < line_data.length; j++) {
                coords.push(line_data[j])
            }
            ext_lines.push({
                "coords": coords, "lineStyle": {
                    "normal": {
                        "color": "#b1b1cd", //"opacity": 0.6,
                        "width": 1
                    }
                }
            })
        }
        //$.extend(map_ext_lines, ext_lines);
        //var cur_lines = map_ext_lines.slice();
        //$.extend(cur_lines, map_lines_data);
        if(centre !== null){
            map_option.leaflet.center = centre;
        }
        // map_option.series[0].data = [map_lines_data[data_index]];
        map_option.series[1].data = ext_lines;
        mapchart.setOption(map_option, true);

        //////////////////////
        var time_speed_width = $("#time_speed_chart").parent().width();
        var seg_height = (time_speed_height - 40) / 2 / 8;
        time_speed_chart.segmentHeight(seg_height)
            .innerRadius(seg_height).margin({
            top: 20,
            right: time_speed_width / 2 - seg_height * 8,
            bottom: 20,
            left: time_speed_width / 2 - seg_height * 8
        });
        d3.select("#time_speed_chart").selectAll("svg").remove();
        d3.select("#time_speed_chart").selectAll("svg").data([time_speed_data])
            .enter()
            .append('svg').attr("height", time_speed_height).attr("width", time_speed_width)
            .call(time_speed_chart);
        /////////////////////
        create_table(table_data);
        //////////////////////
        // create_similar_sub_trajectory_view(sim_phrase_data, data_index);
        // if (!app.inNode) {
        //     // 添加百度地图插件
        //     var bmap = mapchart.getModel().getComponent('bmap').getBMap();
        //     //bmap.addControl(new BMap.MapTypeControl());
        //     //$(".anchorBL").remove();
        //     //$('.BMap_cpyCtrl').remove();
        //     // $(".anchorBL").remove();
        // }

    });
}
function update_detail(data_id, data_index, centre) {
    detail_ids.push(data_id);
    update_detail_by_ids(detail_ids, centre);
}

mapchart.on('click', function (params) {
    //console.log(params); // do whatever you want with another chart say chartTwo here
    if (params.seriesType === 'lines') {
        var data_id = params.data.id;
        var data_index = params.data.index;
        var id_name = "#"+data_id+"_"+data_index;
        //$('#sub_traj_table').parent().animate({
        //    scrollTop: 0
        //}, 200);
        //$('#sub_traj_table').parent().animate({
        //    scrollTop: $(id_name).offset().top-30
        //}, 2000);
        $('#sub_traj_table').parent().animate({
            scrollTop: 0
        }, 0);
        $('#sub_traj_table').parent().animate({
            scrollTop: $(id_name).offset().top-30
        }, 2000);
        //map_lines_data[data_index].lineStyle.normal.color = "#ffff00";
        update_detail(data_id, data_index, mapchart.getOption().leaflet[0].center);
    }
});

mapchart.on('mouseover', function(params){
    console.log(params);
    if (params.seriesType === 'lines') {
        var data_id = params.data.id;
        var data_index = params.data.index;
        var phrase_embedding_data = embedding_data;
        for(var pei=0;pei<phrase_embedding_data.length;pei++){
            phrase_embedding_data[pei][3] = 0.2;
            // map_lines_data[pei]['lineStyle']['color'] = 'rgba(128, 128, 128, 0)';
        }
        phrase_embedding_data[data_index][3] = 1.0;
        phrase_embedding_data[data_index][6] = phrase_embedding_data[data_index][6]*10;
        phrase_embedding_option.series[0].data = phrase_embedding_data;
        phrase_embedding_chart.setOption(phrase_embedding_option, true);
        phrase_embedding_data[data_index][6] = phrase_embedding_data[data_index][6]/10;
    }

});

mapchart.on('mouseout', function(params){
    //console.log(params);
    $.post('/gettopicregionbytopic/', {"topics": JSON.stringify(selected_topics)}, function (jsondata) {
        var indexes = jsondata.data.search;
        console.log(indexes);

        var phrase_embedding_data = embedding_data;
        for(var pei=0;pei<phrase_embedding_data.length;pei++){
            phrase_embedding_data[pei][3] = 0.2;
            // map_lines_data[pei]['lineStyle']['color'] = 'rgba(128, 128, 128, 0)';
        }

        for(var i=0;i<indexes.length;i++){
            phrase_embedding_data[indexes[i]][3] = 1.0;
        }

        phrase_embedding_option.series[0].data = phrase_embedding_data;
        phrase_embedding_chart.setOption(phrase_embedding_option, true);
    });
});
//)
//var sim_sub_traj_height = height * 0.36+8;
//$("#similar_sub_trajectory").height(sim_sub_traj_height);
//var sim_sub_traj_width = $("#similar_sub_trajectory").width();
//var sim_sub_traj_widget_width = sim_sub_traj_width / 3 - 6;
//var sim_sub_traj_option = {
//    leaflet: {
//        center: [104.06, 30.65],
//        zoom: 14,
//        roam: true,
//        layerControl: {
//            position: 'topright'
//        },
//        silent: true,
//        tiles: [{
//            label: 'Open Street Map',
//            urlTemplate: 'http://cache1.arcgisonline.cn/ArcGIS/rest/services/ChinaOnlineStreetGray/MapServer/tile/{z}/{y}/{x}'
//            // options: {
//            //     attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>, Tiles courtesy of <a href="http://hot.openstreetmap.org/" target="_blank">Humanitarian OpenStreetMap Team</a>'
//            // }
//        }
//
//        ]
//    },
//    series: [
//        {
//            type: 'lines',
//            coordinateSystem: 'leaflet',
//            polyline: true,
//            zlevel: 22,
//            // data: lines,
//            // large: true,
//            progressive: 400,
//            progressiveThreshold: 3000,
//            animation: false,
//            symbol: 'arrow',
//            symbolSize: 10,
//            effect: {
//                show: true,
//                period: 50,
//                trailLength: 0,
//                symbol: 'arrow',
//                symbolSize: 8
//            },
//            emphasis: {
//                lineStyle: {
//                    color: '#1f78b4'
//                    // opacity: 0.1
//                }
//            }
//        }
//    ]
//};


// function create_similar_sub_trajectory_view(sub_trajs, data_index) {
//     var sim_sub_traj_view_list = document.getElementById("similar_sub_trajectory");
//     //$("#similar_sub_trajectory").children().remove();
//     $(sim_sub_traj_view_list).children().remove();
//     var selected_line = $.extend({}, map_lines_data[data_index]);
//     selected_line["lineStyle"]['normal']['color'] = '#1f78b4';
//     for (var i = 0; i < sub_trajs.length; i++) {
//         var sub_traj_view = document.createElement('div');
//         $(sub_traj_view).height(sim_sub_traj_widget_width);
//         $(sub_traj_view).width(sim_sub_traj_widget_width);
//         //sub_traj_view.style.width = sim_sub_traj_widget_width;
//         //sub_traj_view.style.height = sim_sub_traj_widget_width;
//         sub_traj_view.id = sub_trajs[i][3] + "-" + sub_trajs[i][11];
//         sub_traj_view.style['border-color'] = 'white';
//         sub_traj_view.style['border-width'] = '1.5px';
//         sub_traj_view.style['border-style'] = 'solid';
//         sub_traj_view.addEventListener("click", function () {
//             var id_value = $(this).attr('id');
//             var field_values = id_value.split("-");
//             var centre = map_lines_data[parseInt(field_values[1])]['coords'];
//             var x_sum =0;
//             var y_sum =0;
//             for(var i=0; i< centre.length; i++){
//                 x_sum += centre[i][0];
//                 y_sum += centre[i][1];
//             }
//             var x_mean = x_sum/centre.length;
//             var y_mean = y_sum/centre.length;
//             var id_name = "#"+field_values[0]+"_"+field_values[1];
//             $('#sub_traj_table').parent().animate({
//                 scrollTop: $(id_name).offset().top-$("#control_bar").height()+253.77
//             }, 2000);
//             update_detail(parseInt(field_values[0]), parseInt(field_values[1]), [x_mean, y_mean]);
//         });
//         sim_sub_traj_view_list.appendChild(sub_traj_view);
//         var sub_traj_view_chart = echarts.init(sub_traj_view);
//         var line_data = sub_trajs[i][0];
//         var coords = [];
//         for (var j = 0; j < line_data.length; j++) {
//             coords.push(line_data[j])
//         }
//         var lines = [selected_line, {
//             "coords": coords,  "id": sub_trajs[i][3], "lineStyle": {
//                 "normal": {
//                     "color": topic_colors[sub_trajs[i][1]], //"opacity": 0.6,
//                     "width": sub_trajs[i][2] * map_line_width
//                 }
//             }}
//         ];
//         sim_sub_traj_option.leaflet.center = sub_trajs[i][10];
//         sim_sub_traj_option.series[0].data = lines;
//         sub_traj_view_chart.setOption(sim_sub_traj_option, true);
//         $(sub_traj_view).find('.leaflet-control-container').remove();
//         sub_traj_view.style.float = "left";
//         sub_traj_view.style.position = "static";
//         $(sub_traj_view).find(".leaflet-container").css("pointer-events", "none");
//     }
// }

