/**
 * Created by yan on 18-5-16.
 */
// var topic_colors = ['#a6cee3', '#1f78b4', '#b2df8a', '#33a02c', '#fb9a99', '#e31a1c', '#fdbf6f', '#ff7f00', '#cab2d6',
//     '#6a3d9a', '#ffff99', '#b15928'];
var latExtent = [30.08, 31.43];
var lngExtent = [102.9, 104.88];
var cellCount = [200, 200];
var cellSizeCoord = [
    (lngExtent[1] - lngExtent[0]) / cellCount[0],
    (latExtent[1] - latExtent[0]) / cellCount[1]
];
var gapSize = 0;

function renderItem(params, api) {
    var context = params.context;
    var lngIndex = api.value(2);
    var latIndex = api.value(1);
    var coordLeftTop = [
        +(latExtent[0] + lngIndex * cellSizeCoord[0]).toFixed(6),
        +(lngExtent[0] + latIndex * cellSizeCoord[1]).toFixed(6)
    ];
    var pointLeftTop = getCoord(params, api, lngIndex, latIndex);
    var pointRightBottom = getCoord(params, api, lngIndex + 1, latIndex + 1);

    return {
        type: 'rect',
        shape: {
            x: pointLeftTop[0],
            y: pointLeftTop[1],
            width: pointRightBottom[0] - pointLeftTop[0],
            height: pointRightBottom[1] - pointLeftTop[1]
        },
        style: api.style({
            stroke: 'rgba(0,0,0,0.1)'
        }),
        styleEmphasis: api.styleEmphasis()
    };
}


function getCoord(params, api, lngIndex, latIndex) {
    var coords = params.context.coords || (params.context.coords = []);
    var key = lngIndex + '-' + latIndex;

    // bmap returns point in integer, which makes cell width unstable.
    // So we have to use right bottom point.
    return coords[key] || (coords[key] = api.coord([
            +(lngExtent[0] + lngIndex * cellSizeCoord[0]).toFixed(6),
            +(latExtent[0] + latIndex * cellSizeCoord[1]).toFixed(6)
        ]));
}

function globalbutton() {
    getregiondist("6");
}

function topicbutton() {
    gettopicregiondist("6");
}

var height = window.innerHeight * 0.72;
$("#map").height(height);
var dom = document.getElementById("map");
var mapchart = echarts.init(dom);
var app = {};
gettopicregiondist("0");
//getregiondist("6");

var map_option = {
    tooltip: {},
    toolbox: {
        showTitle: false,
        // show: true,
        itemSize: 60,
        zlevel: 1000,
        // left:'left' ,
        top: 10,
        feature: {
            myTool1: {
                show: true,
                title: "general",
                icon: 'image://static/images/general.png',
                onclick: globalbutton
            },
            myTool2: {
                show: true,
                title: "topic",
                icon: 'image://static/images/topic.png',
                onclick: topicbutton
            }
        }
    },
    bmap: {
        center: [104.06, 30.65],
        zoom: 11,
        roam: true,
        mapStyle: {
            styleJson: [{
                'featureType': 'water',
                'elementType': 'all',
                'stylers': {
                    'color': '#d1d1d1'
                }
            }, {
                'featureType': 'land',
                'elementType': 'all',
                'stylers': {
                    'color': '#f3f3f3'
                }
            }, {
                'featureType': 'railway',
                'elementType': 'all',
                'stylers': {
                    'visibility': 'off'
                }
            }, {
                'featureType': 'highway',
                'elementType': 'all',
                'stylers': {
                    'color': '#999999'
                }
            }, {
                'featureType': 'highway',
                'elementType': 'labels',
                'stylers': {
                    'visibility': 'off'
                }
            }, {
                'featureType': 'arterial',
                'elementType': 'geometry',
                'stylers': {
                    'color': '#fefefe'
                }
            }, {
                'featureType': 'arterial',
                'elementType': 'geometry.fill',
                'stylers': {
                    'color': '#fefefe'
                }
            }, {
                'featureType': 'poi',
                'elementType': 'all',
                'stylers': {
                    'visibility': 'off'
                }
            }, {
                'featureType': 'green',
                'elementType': 'all',
                'stylers': {
                    'visibility': 'off'
                }
            }, {
                'featureType': 'subway',
                'elementType': 'all',
                'stylers': {
                    'visibility': 'off'
                }
            }, {
                'featureType': 'manmade',
                'elementType': 'all',
                'stylers': {
                    'color': '#d1d1d1'
                }
            }, {
                'featureType': 'local',
                'elementType': 'all',
                'stylers': {
                    'color': '#d1d1d1'
                }
            }, {
                'featureType': 'arterial',
                'elementType': 'labels',
                'stylers': {
                    'visibility': 'off'
                }
            }, {
                'featureType': 'boundary',
                'elementType': 'all',
                'stylers': {
                    'color': '#fefefe'
                }
            }, {
                'featureType': 'building',
                'elementType': 'all',
                'stylers': {
                    'color': '#d1d1d1'
                }
            }, {
                'featureType': 'label',
                'elementType': 'labels.text.fill',
                'stylers': {
                    'color': 'rgba(0,0,0,0)'
                }
            }]
        }
    }
};
// app.title = '热力图与百度地图扩展';
function getregiondist(hour) {
    $.post('/getregiondist/', {"data":  hour}, function (jsondata) {
        var max_value = jsondata.data.max_value;
        var data = jsondata.data.data;
        console.log(data);
        // data = data.map(function (d) {
        //    return [d[0], d[1], d[2]];
        // });
        // console.log(data);
        var option = {
            // visualMap: {
            //     type: 'piecewise',
            //     inverse: true,
            //     top: 10,
            //     left: 10,
            //     pieces: [{
            //         value: 0, color: topic_colors[0], label: 'Topic 1'
            //     }, {
            //         value: 1, color: topic_colors[1], label: 'Topic 2'
            //     }, {
            //         value: 2, color: topic_colors[2], label: 'Topic 3'
            //     }, {
            //         value: 3, color: topic_colors[3], label: 'Topic 4'
            //     }, {
            //         value: 4, color: topic_colors[4], label: 'Topic 5'
            //     }, {
            //         value: 5, color: topic_colors[5], label: 'Topic 6'
            //     }],
            //     borderColor: '#ccc',
            //     borderWidth: 2,
            //     backgroundColor: '#eee',
            //     dimension: 0,
            //     inRange: {
            //         color: topic_colors,
            //         opacity: 0.7
            //     },
            //     categories: topics
            // },
            visualMap: {
                type: 'continuous',
                top: 10,
                left: 10,
                min: 0,
                max: max_value,
                text: ['High', 'Low'],
                dimension: 0,
                realtime: false,
                calculable: true,
                inRange: {
                    color: ['lightskyblue', 'yellow', 'orangered'],
                    opacity: 0.4
                }
            },
            series: [
                {
                    type: 'custom',
                    coordinateSystem: 'bmap',
                    renderItem: renderItem,
                    animation: false,
                    itemStyle: {
                        emphasis: {
                            color: 'yellow'
                        }
                    },
                    encode: {
                        tooltip: 0
                    },
                    data: data
                }
            ]
        };
        option = $.extend(option, map_option);
        mapchart.setOption(option);

        if (!app.inNode) {
            // 添加百度地图插件
            var bmap = mapchart.getModel().getComponent('bmap').getBMap();
            // bmap.addControl(new BMap.MapTypeControl());
            // $(".anchorBL").remove();
            // $('.BMap_cpyCtrl').remove();
        }

    });
}

function update_topic_region(data){
     var option = {
            visualMap: {
                type: 'piecewise',
                inverse: true,
                top: 10,
                left: 10,
                pieces: [{
                    value: 0, color: topic_colors[0], label: 'Topic 1'
                }, {
                    value: 1, color: topic_colors[1], label: 'Topic 2'
                }, {
                    value: 2, color: topic_colors[2], label: 'Topic 3'
                }, {
                    value: 3, color: topic_colors[3], label: 'Topic 4'
                }, {
                    value: 4, color: topic_colors[4], label: 'Topic 5'
                }, {
                    value: 5, color: topic_colors[5], label: 'Topic 6'
                },
                {
                    value: 6, color: topic_colors[6], label: 'Topic 7'
                },
                {
                    value: 7, color: topic_colors[7], label: 'Topic 8'
                },
                {
                    value: 8, color: topic_colors[8], label: 'Topic 9'
                }, {
                    value: 9, color: topic_colors[9], label: 'Topic 10'
                }, {
                    value: 10, color: topic_colors[10], label: 'Topic 11'
                }, {
                    value: 11, color: topic_colors[11], label: 'Topic 12'
                }, {
                    value: 12, color: topic_colors[12], label: 'Topic 13'
                },
                {
                    value: 13, color: topic_colors[13], label: 'Topic 14'
                },   {
                    value: 14, color: topic_colors[14], label: 'Topic 15'
                }, {
                    value: 15, color: topic_colors[15], label: 'Topic 16'
                }, {
                    value: 16, color: topic_colors[16], label: 'Topic 17'
                }, {
                    value: 17, color: topic_colors[17], label: 'Topic 18'
                }, {
                    value: 18, color: topic_colors[18], label: 'Topic 19'
                },
                {
                    value: 19, color: topic_colors[19], label: 'Topic 20'
                }
                ],
                borderColor: '#ccc',
                borderWidth: 2,
                backgroundColor: '#eee',
                dimension: 0,
                inRange: {
                    color: topic_colors,
                    opacity: 0.7
                },
                categories: topics
            },
            series: [
                {
                    type: 'custom',
                    coordinateSystem: 'bmap',
                    renderItem: renderItem,
                    animation: false,
                    itemStyle: {
                        emphasis: {
                            color: 'yellow'
                        }
                    },
                    encode: {
                        tooltip: 1
                    },
                    data: data
                }
            ]
        };
        option = $.extend(option, map_option);
        mapchart.setOption(option);
        if (!app.inNode) {
            // 添加百度地图插件
            var bmap = mapchart.getModel().getComponent('bmap').getBMap();
            //bmap.addControl(new BMap.MapTypeControl());
            //$(".anchorBL").remove();
            //$('.BMap_cpyCtrl').remove();
            // $(".anchorBL").remove();
        }
}
function gettopicregiondist(hour) {
    $.post('/gettopicregion/', {"data":  hour}, function (jsondata) {
        var data = jsondata.data.data;
        console.log(data);
        update_topic_region(data);
    });
}

// timechart.on('brushSelected', function (params) {
//     var selected_indexes = params.batch[0].selected[0].dataIndex;
//     var timerange = [];
//     for(var i=0;i<selected_indexes.length;i++){
//         timerange.push(Math.floor(selected_indexes[i]%hours.length))
//     }
//     console.log(timerange);
//     $.post('/updatetopicregion/', {"data":  JSON.stringify(timerange)}, function (data) {
//         update_topic_region(data.data.data);
//     })
// });