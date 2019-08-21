/**
 * Created by yan on 18-5-16.
 */
var bool_scatter_move_out_event = false;
var bool_scatter_move_in_event = true;

//draw map
var height = $("#map").parent().innerHeight();
$("#map").height(height);
var wrapper_height = $(".right-column-wrapper").innerHeight();
var dom = document.getElementById("map");
var selected_topics = [];
var mapchart = echarts.init(dom);
var app = {};
var map_line_width = 4;
var map_lines_data = null;
var map_arrows_data = null;
var map_lines_data_new = null;
var embedding_data = null;
var table_data = null;
var map_id = 0;
var detail_ids = [];
var time_speed_height = height * 0.351;
var time_dist_data_bk = null;
var time_speed_data_bk = null;

// 地图上的重载按钮
var bmap_option = {
    tooltip: {},
    toolbox: {
        // showTitle: true,
        itemSize: 20,
        zlevel: 1000,
        top: 8,
        right: 6,
        feature: {
            myTool1: {
                show: true,
                title: "reset",
                icon: 'image://static/images/reset.png',
                onclick: function () {
                    map_option.series[1].data = [];
                    update_by_topics();
                    bool_scatter_move_out_event = false;
                    bool_scatter_move_in_event = true;
                    map_id = map_coords.length-1;
                    detail_ids = [];
                    drawDistAndSpeed(time_dist_data_bk, time_speed_data_bk)
                }
            }
        }
    },
    leaflet: {
        center: [104.0639, 30.6592], 
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
            urlTemplate:  'http://cache1.arcgisonline.cn/ArcGIS/rest/services/ChinaOnlineStreetGray/MapServer/tile/{z}/{y}/{x}'
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
    },
    series: [
        {
            type: 'lines',
            coordinateSystem: 'leaflet',
            polyline: true,
            zlevel: 2,
            animation: false,  
            // effect: {
            //     show: true,
            //     period: 20,
            //     trailLength: 0,
            //     symbol: 'arrow',
            //     symbolSize: 10
            // },
            emphasis: {
                lineStyle: {
                    color: '#9e0142'
                }
            }
        },
        {
            type: 'lines',
            coordinateSystem: 'leaflet',
            polyline: true,
            zlevel: 1,
            animation: false,
            symbol: 'arrow',
            symbolSize: 5,
            emphasis: {
                lineStyle: {
                    color: '#1f78b4'
                }
            }
        },
        {
            type: 'lines',
            coordinateSystem: 'leaflet',
            zlevel: 3,
            animation: false,
            symbol: ['none', 'arrow'],
            symbolSize: 10
        }
    ]
};
map_option = $.extend(map_option, bmap_option);
$("#map").dblclick(map_interactive_change, function () {
    map_option.leaflet.roam = !map_option.leaflet.roam;
    map_interactive_change();
});
function map_interactive_change() {
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

// draw topic bar
var topic_bar_height = $('#topic_bar').innerHeight;
$("#topic_bar").height(topic_bar_height);
var topic_bar_dom = document.getElementById("topic_bar");
var topic_bar_chart = echarts.init(topic_bar_dom);
var topic_bar_option = {
    tooltip : {
        trigger: 'axis',
        axisPointer : {            // 坐标轴指示器，坐标轴触发有效
            type : 'shadow'        // 默认为直线，可选为：'line' | 'shadow'
        },
        showContent: false
    },
    grid: {
        left: '1%',
        right: '2%',
        bottom: '6%',
        top: '6%',
        containLabel: true
    },
    xAxis : [
        {
            type : 'category',
            data : topics,
            axisTick: {
                alignWithLabel: true
            },
            axisLabel: {   //坐标轴文字
                rotate: -60
            },
            
        }
    ],
    yAxis : [
        {
            type : 'value',
            axisLabel: {   //坐标轴文字
                show: false
            },
            axisTick: {   //坐标轴tick
                show: true,
                inside: true
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
                    "color": topic_colors[lines_data[i][1]],
                    "width": map_line_width,
                    'opacity': lines_data[i][2]*100
                }
            }
        });
    }
    map_lines_data = lines;
    map_option.series[0].data = lines;
    var arrows = []
    for(var i=0; i<lines.length; i++){
        var max_dist = 0, index = 0
        for(var j=0; j<lines[i].coords.length-1; j++){
            var dist = getDist(lines[i].coords[j], lines[i].coords[j+1])
            if(dist > max_dist){
                max_dist = dist
                index = j
            }
        }
        var arrow = {
            'coords': [lines[i].coords[index], lines[i].coords[index+1]],       
            'id': lines[i].id, 
            'lineStyle': {
                "normal": {
                    "color": lines[i].lineStyle.normal.color,
                    "width": 0,
                    'opacity': lines[i].lineStyle.normal.opacity
                }
            }, 
            'index': lines[i].index
        }
        arrows.push(arrow) 
    }
    map_option.series[2].data = arrows;
    map_arrows_data = arrows
    mapchart.setOption(map_option, true);
}

function Rad(d){
    return d * Math.PI / 180;
}

function getDist(pre, next){
    var lat1 = pre[0], lng1 = pre[1], lat2 = next[0], lng2 = next[1];
    var a = Rad(lat1) - Rad(lat2), b = Rad(lng1) - Rad(lng2);
    var s = 2 * Math.asin(Math.sqrt(Math.pow(Math.sin(a/2),2) +                  Math.cos(Rad(lat1))*Math.cos(Rad(lat2))*Math.pow(Math.sin(b/2),2)));
    s = s*6378.137;
    s = Math.round(s * 10000) / 10000;
    return s
}

// 获取距离, 创建子路径table
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
        update_topic_region(topic_phrase_data);
        var phrase_embedding_data = jsondata.data.embedding;
        //将embedding散点图平移
        for(var i=0;i<phrase_embedding_data.length;i++){
            phrase_embedding_data[i][0] =  phrase_embedding_data[i][0]+10;
        }
        phrase_embedding_option.series[0].data = phrase_embedding_data;
        embedding_data = phrase_embedding_data;
        phrase_embedding_chart.setOption(phrase_embedding_option, true);
        create_sub_trajectory_table(topic_phrase_data, null);
        table_data = topic_phrase_data;
        //////////////////////
        var time_dist_data = jsondata.data.time_dist;
        var old_time_speed_data = jsondata.data.time_speed;
        var time_speed_data = []

        // 增加11pm到6am的speed数据
        for(var i=0; i<old_time_speed_data.length; i++){
            if(i%18 === 0){
                for(var j=0; j<6; j++)
                    time_speed_data.push(0);
            }
            time_speed_data.push(old_time_speed_data[i]);
        }
        drawDistAndSpeed(time_dist_data, time_speed_data)

        time_dist_data_bk = time_dist_data;
        time_speed_data_bk = time_speed_data;
        /////////////////////
    });
}

// 更新map上的line
function update_by_topics() {
  $.post('/gettopicregionbytopic/', {"topics": JSON.stringify(selected_topics)}, function (jsondata) {
        var indexes = jsondata.data.search;
        var phrase_embedding_data = embedding_data;
        for(var pei=0;pei<phrase_embedding_data.length;pei++){
            phrase_embedding_data[pei][3] = 0.1;
        }
        var lines_new = [];
        var table_data_new = [];
        var arrows_new = []
        for(var i=0;i<indexes.length;i++){
            phrase_embedding_data[indexes[i]][3] = 1.0;
            table_data_new.push(table_data[indexes[i]]);
            lines_new.push(map_lines_data[indexes[i]]);
            arrows_new.push(map_arrows_data[indexes[i]]);
        }
        map_option.series[0].data = lines_new;
        map_lines_data_new = lines_new;
        map_option.series[2].data = arrows_new;

        mapchart.setOption(map_option, true);

        phrase_embedding_option.series[0].data = phrase_embedding_data;
        phrase_embedding_chart.setOption(phrase_embedding_option, true);
        create_sub_trajectory_table(table_data_new, null);

        //////////
        //////////////////////
        var time_dist_data = jsondata.data.time_dist;
        var old_time_speed_data = jsondata.data.time_speed;
        var time_speed_data = []

        // 增加11pm到6am的speed数据
        for(var i=0; i<old_time_speed_data.length; i++){
            if(i%18 === 0){
                for(var j=0; j<6; j++)
                    time_speed_data.push(0);
            }
            time_speed_data.push(old_time_speed_data[i]);
        }
        drawDistAndSpeed(time_dist_data, time_speed_data)

        time_dist_data_bk = time_dist_data;
        time_speed_data_bk = time_speed_data;
        /////////////////////
        console.log("done");
    });
}

// topic bar click event
function topic_bar_click(params) {
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

function mapBrushSelected (params) {
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
}

function hexToRgb(hex) {
    var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : null;
}

// draw embedding
// data设置在函数gettopicregiondist,echarts自动获取前两位作为坐标值
var phrase_embedding_option = {
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
            return Math.sqrt(params[6])*25;
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

var phrase_embedding_height = $("#phrase_embedding").innerHeight;
$("#phrase_embedding").height(phrase_embedding_height);
var phrase_embedding_dom = document.getElementById("phrase_embedding");
var phrase_embedding_chart = echarts.init(phrase_embedding_dom);

phrase_embedding_chart.on('mouseover', function (params) {
    if (params.seriesType === 'scatter'&& bool_scatter_move_in_event === true) {
        var data_index = params.dataIndex;
        map_option.series[0].data = [map_lines_data[data_index]];
        mapchart.setOption(map_option, true);
        bool_scatter_move_out_event = true;
        bool_scatter_move_in_event = false;
    }
});
phrase_embedding_chart.on('mouseout', function (params) {
    if (params.seriesType === 'scatter' && bool_scatter_move_out_event === true) {
        map_option.series[0].data = map_lines_data_new;
        mapchart.setOption(map_option, true);
        bool_scatter_move_out_event = false;
        bool_scatter_move_in_event = true;
    }
});
phrase_embedding_chart.on('click', function (params) {
    if (params.seriesType === 'scatter') {
        var data_index = params.dataIndex;
        var data_id = map_lines_data[data_index].id;
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
        $('#sub_traj_table').parent().animate({
            scrollTop: 0
        }, 200);
        $('#sub_traj_table').parent().animate({
            scrollTop: $(id_name).offset().top-30
        }, 2000);
        update_detail(data_id, data_index, [x_mean, y_mean]);

    }
});

phrase_embedding_chart.on('brushSelected', renderBrushed);

function renderBrushed(params) {
    if(bool_scatter_move_in_event || bool_scatter_move_out_event){
        var brushComponent = params.batch[0];
        var new_brush_data = [];
        var new_arrows = [];
        var new_brush_table_index_data = [];
        for (var sIdx = 0; sIdx < brushComponent.selected.length; sIdx++) {
            var rawIndices = brushComponent.selected[sIdx].dataIndex;
            for(var j =0; j<rawIndices.length;j++){
                if(selected_topics.indexOf(embedding_data[rawIndices[j]][2]) !== -1){
                    new_brush_data.push(map_lines_data[rawIndices[j]]);
                    new_arrows.push(map_arrows_data[rawIndices[j]]);
                    new_brush_table_index_data.push(rawIndices[j]);
                }
            }
        }
        if(new_brush_data.length === 0){
            map_option.series[0].data = map_lines_data_new;
            new_brush_table_index_data = null;
        }else {
            map_option.series[0].data = new_brush_data;
            map_option.series[2].data = new_arrows;
        }
        if(new_brush_data.length !== 0){
            $.post('/getdetailbyid/', {"id": JSON.stringify(new_brush_table_index_data)}, function (jsondata) {
                var data = jsondata.data;
                var start_time_span_data = data['start_time_span'];
                var old_time_speed_data = data['time_speed'];
                var time_speed_data = []
                 // 增加11pm到6am的speed数据
                for(var i=0; i<old_time_speed_data.length; i++){
                    if(i%18 === 0){
                        for(var j=0; j<6; j++)
                            time_speed_data.push(0);
                    }
                    time_speed_data.push(old_time_speed_data[i]);
                }
                drawDistAndSpeed(start_time_span_data, time_speed_data)
            });
        }else{
            drawDistAndSpeed(time_dist_data_bk, time_speed_data_bk)
        }

        mapchart.setOption(map_option, true);
        create_sub_trajectory_table(table_data, new_brush_table_index_data);
    }

}
// var line_data = [], arrow_data = []
var sub_traj_height = wrapper_height * 0.5;
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
        if(selected_topics.indexOf(table_data[i][colum_index[1]]) === -1){
            continue
        };
        var road_name_list = document.createElement('div');

        //过滤相邻同名字段
        var temp_raod_name = table_data[i][colum_index[0]][0]
        var new_road_name_list = [temp_raod_name]
        for (var t=1; t<table_data[i][colum_index[0]].length; t++){
            if(temp_raod_name === table_data[i][colum_index[0]][t])
                continue
            temp_raod_name = table_data[i][colum_index[0]][t]
            new_road_name_list.push(temp_raod_name)
        }
        for (var j = 0; j < new_road_name_list.length; j++) {
            var road_name = document.createElement('p');
            road_name.classList.add("label");
            road_name.style['background-color'] = topic_colors[table_data[i][colum_index[1]]];
            road_name.style.color = 'white';
            road_name.style['font-size'] = '11px';
            var road_name_text = document.createTextNode(new_road_name_list[j]);
            road_name.appendChild(road_name_text);
            road_name_list.appendChild(road_name);
            if (j !== new_road_name_list.length - 1) {
                var arrow = document.createElement('span');
                arrow.classList.add("glyphicon");
                arrow.classList.add("glyphicon-arrow-right");
                road_name_list.appendChild(arrow);
            }

        }

        tr[i].appendChild(road_name_list);
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
            $(this).css({"background": "#969696"});
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
            // line_data.push(map_lines_data.filter(d => d.id === parseInt(field_values[0]))[0])
            // arrow_data.push(map_arrows_data.filter(d => d.id === parseInt(field_values[0]))[0])
            // map_option.series[0].data = line_data;
            // map_option.series[2].data = arrow_data;
        });
        table.appendChild(tr[i]);
        
    }
}

function create_table(table_data) {
    if (detail_table !== null) {
        detail_table.destroy();
    }
    detail_table = $('#detail_table').DataTable({
        columns: [{title: 'Taxi ID'}, {title: 'PickUp_P'}, {title: 'DropOff_P'}, {title: 'PickUp_T'}, {title: 'DropOff_T'}, {title: 'Avg_Spd'}, {title: 'Max_Spd'}, {title: 'Min_Spd'}, {title: 'Dist'}],
        data: table_data,
        scrollY: "150px",
        scrollCollapse: true,
        searching: false,
        pagingType: 'simple'
    });
    $('#detail_table').addClass('bs-select');
    $("#detail_table_length").remove();

}
var detail_table = null;
var detail_table_height = $("#detail_table").parent().innerHeight();
$("#detail_table").height(detail_table_height);

function update_detail_by_ids(data_ids, centre) {
    $.post('/getdetailbyid/', {"id": JSON.stringify(data_ids)}, function (jsondata) {
        var data = jsondata.data;
        var start_time_span_data = data['start_time_span'];
        var old_time_speed_data = data['time_speed']; 
        var time_speed_data = [];
         // 增加11pm到6am的speed数据
         for(var i=0; i<old_time_speed_data.length; i++){
            if(i%18 === 0){
                for(var j=0; j<6; j++)
                    time_speed_data.push(0);
            }
            time_speed_data.push(old_time_speed_data[i]);
        }
        var table_data = data['table'];
        drawDistAndSpeed(start_time_span_data, time_speed_data)

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
        if(centre !== null){
            map_option.leaflet.center = centre;
        }
        // map_option.series[1].data = ext_lines;
        mapchart.setOption(map_option, true);

        create_table(table_data);
        //////////////////////

    });
}
function update_detail(data_id, data_index, centre) {
    detail_ids.push(data_id);
    update_detail_by_ids(detail_ids, centre);
}

mapchart.on('click', function (params) {
    if (params.seriesType === 'lines') {
        var data_id = params.data.id;
        var data_index = params.data.index;
        var id_name = "#"+data_id+"_"+data_index;
        $('#sub_traj_table').parent().animate({
            scrollTop: 0
        }, 0);
        $('#sub_traj_table').parent().animate({
            scrollTop: $(id_name).offset().top-30
        }, 2000);
        update_detail(data_id, data_index, mapchart.getOption().leaflet[0].center);
    }
});

mapchart.on('mouseover', function(params){
    if (params.seriesType === 'lines') {
        var data_id = params.data.id;
        var data_index = params.data.index;
        var phrase_embedding_data = embedding_data;
        for(var pei=0;pei<phrase_embedding_data.length;pei++){
            phrase_embedding_data[pei][3] = 0.2;
        }
        phrase_embedding_data[data_index][3] = 1.0;
        phrase_embedding_data[data_index][6] = phrase_embedding_data[data_index][6]*10;
        phrase_embedding_option.series[0].data = phrase_embedding_data;
        phrase_embedding_chart.setOption(phrase_embedding_option, true);
        phrase_embedding_data[data_index][6] = phrase_embedding_data[data_index][6]/10;
    }

});

mapchart.on('mouseout', function(params){
    $.post('/gettopicregionbytopic/', {"topics": JSON.stringify(selected_topics)}, function (jsondata) {
        var indexes = jsondata.data.search;

        var phrase_embedding_data = embedding_data;
        for(var pei=0;pei<phrase_embedding_data.length;pei++){
            phrase_embedding_data[pei][3] = 0.2;
        }

        for(var i=0;i<indexes.length;i++){
            phrase_embedding_data[indexes[i]][3] = 1.0;
        }

        phrase_embedding_option.series[0].data = phrase_embedding_data;
        phrase_embedding_chart.setOption(phrase_embedding_option, true);
    })
})

function drawDistAndSpeed(dist_data, speed_data){
    var svgHeight = wrapper_height*0.55
    var svgWidth = $("#time_speed_chart").parent().width();
    d3.select("#time_speed_chart").selectAll("svg").remove();
    var chartSvg = d3.select('#time_speed_chart').append('svg')
        .attr('width', svgWidth).attr('height', svgHeight)
    var innerR = 15, outerR = 30,
        width = svgWidth/2 - 20, height = svgHeight/2;
    innerR = drawSpeedChart(speed_data, chartSvg, width, height, innerR, outerR);
    innerR = drawText(chartSvg, width, height, innerR, innerR+20);
    drawStackBar(dist_data, chartSvg, width, height, innerR);
    drawPatterns(chartSvg, width, height);
    innerR = 15, outerR = 30;
    drawMark(chartSvg, width, height, innerR, outerR);
    // drawColorBar(chartSvg);  
}

// draw circular heat map
function drawSpeedChart(speed_data, chartSvg, width, height, innerR, outerR){
    var color = d3.scaleSequential(d3.interpolateGreens);
    var max = Math.max(...speed_data)
    var arc_speed = d3.arc()
    for(var j=0; j<7; j++){
        var speedG = chartSvg.append('g').attr('transform', 
            'translate(' + width  + ',' + height +')')
        arc_speed.innerRadius(innerR).outerRadius(outerR)
        var arcs = d3.pie()(new Array(24).fill(1))
        speedG.selectAll('path')
            .data(arcs).enter().append('path')
            .style('fill', function(d, i){
                if(i>=0 && i<=5) return '#e0e0e0'
                else{
                    //范围映射到[0.1,0.9]
                    var value = 0.2 + (0.9-0.2)/max*speed_data[j*24+i]
                    return color(value)
                }
            })
            .attr('d', arc_speed)
        innerR = outerR
        outerR = outerR + 15
    }
    return innerR
}

// draw stacked bar
function drawStackBar(dist_data, chartSvg, width, height, innerR){
    // var dist = []
    // for(var i=0; i<dist_data.length; i++){
    //     for(var j=0; j<dist_data[i].data.length; j++){
    //         dist.push({
    //             id: i,
    //             name: dist_data[i].name,
    //             time: j,
    //             value: dist_data[i].data[j]
    //         })
    //     }  
    // }

    var keys = ['0-10km', '10-20km', '20-30km', '>30km'],
        stack = d3.stack().keys(keys);
    var dist = [{}, {}, {}, {}, {}, {}]
    for(var i=0; i<dist_data.length; i++){
        for(var j=0; j<dist_data[i].data.length; j++){
            dist[j][keys[i]] = dist_data[i].data[j]
        }  
    }
    let series = stack(dist)
    var barG = chartSvg.append('g').attr('transform', 
        'translate(' + width + ',' + height +')')
    var offset_group = 2*Math.PI / 24 * 3,
        offset_initial = offset_group * 2
        // offest_inner = offset_group / 4
    var color= d3.scaleSequential(d3.interpolateReds);
    // var arc_dist = d3.arc()
    //     .startAngle(function(d){ return offset_initial + d.time * offset_group + d.id*offest_inner})
    //     .endAngle(function(d){ return offset_initial + d.time * offset_group + (d.id +1)*offest_inner})
    //     .innerRadius(innerR)
    //     .outerRadius(function(d){ return innerR + Math.pow(d.value, 2/5)})
    var maxVal = d3.max(series[series.length - 1], d => d[1])
    var y = d3.scaleLinear()
    .range([innerR, innerR+40]).domain([0, maxVal])
    var arc_dist = d3.arc()
        .startAngle(function(d, i){ return offset_initial + i * offset_group})
        .endAngle(function(d, i){ return offset_initial + (i+1) * offset_group})
        .innerRadius(function(d){ return y(d[0]) })
        .outerRadius(function(d){ return y(d[1]) })

    var seriesG = barG.selectAll('g').data(series)
        .enter().append('g')
        .attr('fill', function(d, i){
            let val = d.index * 0.25 + 0.25
            if(val > 1) val = 1
            return color(val)
        })
    seriesG.selectAll('g').data(d => d).enter().append('path').attr('d', arc_dist)
}

// add text and split
function drawText(chartSvg, width, height, innerR, outerR){
    var splitG = chartSvg.append('g').attr('transform', 
        'translate(' + width + ',' + height +')')
    var arc = d3.arc()
        .innerRadius(outerR)
        .outerRadius(innerR)
    var arcs_split = d3.pie()(new Array(8).fill(1))
    splitG.selectAll('path')
            .data(arcs_split).enter().append('path')
            .style('fill', 'none')
            .attr('d', arc)
            .attr('stroke', '#d9d9d9')

    var time = ['12am','1','2','3','4','5','6','7','8','9','10','11','12pm','1','2','3','4','5','6','7','8','9','10','11']
    var textG = chartSvg.append('g').attr('transform', 
        'translate(' + width + ',' + height +')')
    var arcs_text = d3.pie()(new Array(24).fill(1))
    textG.selectAll('path')
        .data(arcs_text).enter().append('path')
        .attr('id', function(d, i){ return 'text-node-'+i})
        .attr('d', arc)
        .style('fill', 'none')
    textG.selectAll('text')
        .data(time).enter().append('text')
        .style('font-size', 12+'px')
        .attr("dy", 15)
        .attr('x', 5)
        .append('textPath')
        .attr('xlink:href', function(d, i) { return '#text-node-'+i })
        .text(function(d){ return d }) 
    return outerR
}

// add patterns
function drawPatterns(chartSvg, width, height){
    chartSvg
        .append('defs')
        .append('pattern')
        .attr('id', 'diagonalHatch')
        .attr('patternUnits', 'userSpaceOnUse')
        .attr('width', 4)
        .attr('height', 4)
        .append('path')
        .attr('d', 'M-1,1 l2,-2 M0,4 l4,-4 M3,5 l2,-2')
        .attr('stroke', '#bdbdbd')
        .attr('stroke-width', 1);
    var patternG = chartSvg.append('g').attr('transform', 
        'translate(' + width + ',' + height +')')
    var arc_pattern = d3.arc().innerRadius(15).outerRadius(15*8)
        .startAngle(0).endAngle(Math.PI/2)
    patternG.append('path')
        .attr('d', arc_pattern)
        .attr('fill', 'url(#diagonalHatch)');
}

// add the mark text
function drawMark(chartSvg, width, height, innerR, outerR){
    var mark = ['0-9', '10-19', '20-29', '30-39', '40-49', '50-59', '>60 km/h']
    for(var i=0; i<7; i++){
        var markG = chartSvg.append('g').attr('transform', 
            'translate(' + width + ',' + height +')')
        var arc_mark = d3.arc().innerRadius(innerR).outerRadius(outerR)
            .startAngle(0).endAngle(90)
        markG.append('path')
            .attr('id', 'mark-node-'+i)
            .attr('d', arc_mark)
            .attr('fill', 'none')
        markG.append('text')
            .style('font-size', 12+'px')
            .attr("dy", 15)
            .attr('x', 5)
            .append('textPath')
            .attr('xlink:href', '#mark-node-'+i)
            .text(mark[i]) 
        innerR = outerR
        outerR = outerR + 15
    } 
}

// draw color bar 
function drawColorBar(chartSvg){
    var color= d3.scaleSequential(d3.interpolateGreens);
    var speed_bar_G = chartSvg.append('g').attr('transform', 
        'translate(' + 300 + ',' + 0 +')')
    let linearGradient = chartSvg .append('defs')
        .append('linearGradient')
        .attr('id', 'bar-linear-gradient')
        .attr('gradientUnits','userSpaceOnUse')
        .attr('x1', 0)
        .attr('y1', 0)
        .attr('x2', 150)
        .attr('y2', 15)
    linearGradient.append('stop')
        .attr('offset', '0%')
        .attr('stop-color', color(0.1))
    linearGradient.append('stop')
        .attr('offset', '100%')
        .attr('stop-color', color(0.9))
    speed_bar_G.append('text')
        .text('Num')
        .attr('font-size', 12)
        .attr('dy', '1em')
        .attr('dx', '-2.5em')
    speed_bar_G.append('rect')
        .attr('width', 150)
        .attr('height', 15)
        .style('fill', 'url(#bar-linear-gradient)')
    speed_bar_G.append('text')
        .text('Less')
        .attr('font-size', 10)
        .attr('dx', '-0.3em')
        .attr('dy', '2.5em')
    speed_bar_G.append('text')
        .text('More')
        .attr('font-size', 10)
        .attr('x', 150)
        .attr('dx', '-0.3em')
        .attr('dy', '2.5em')

    color= d3.scaleSequential(d3.interpolateReds);
    var dist_bar_G = chartSvg.append('g').attr('transform', 
        'translate(' + 300 + ',' + 30 +')')
    dist_bar_G.append('rect')
        .attr('width', 150/4)
        .attr('height', 15)
        .attr('fill', color(0.25))
    dist_bar_G.append('rect')
        .attr('width', 150/4)
        .attr('height', 15)
        .attr('fill', color(0.5))
        .attr('x', 150/4)
    dist_bar_G.append('rect')
        .attr('width', 150/4)
        .attr('height', 15)
        .attr('fill', color(0.75))
        .attr('x', 150/2)
    dist_bar_G.append('rect')
        .attr('width', 150/4)
        .attr('height', 15)
        .attr('fill', color(1))
        .attr('x', 150*3/4)
    dist_bar_G.append('text')
        .text('Dist')
        .attr('font-size', 12)
        .attr('dy', '1em')
        .attr('dx', '-2.3em')
    dist_bar_G.append('text')
        .text('0km')
        .attr('font-size', 10)
        .attr('x', 0)
        .attr('dx', '-0.3em')
        .attr('dy', '2.5em')
    dist_bar_G.append('text')
        .text('10km')
        .attr('font-size', 10)
        .attr('x', 150/4)
        .attr('dx', '-0.3em')
        .attr('dy', '2.5em')
    dist_bar_G.append('text')
        .text('20km')
        .attr('font-size', 10)
        .attr('x', 150/2)
        .attr('dx', '-0.3em')
        .attr('dy', '2.5em')
    dist_bar_G.append('text')
        .text('30km')
        .attr('font-size', 10)
        .attr('x', 150*3/4)
        .attr('dx', '-0.3em')
        .attr('dy', '2.5em')
    dist_bar_G.append('text')
        .text('More')
        .attr('font-size', 10)
        .attr('x', 150)
        .attr('dx', '-0.3em')
        .attr('dy', '2.5em')
}