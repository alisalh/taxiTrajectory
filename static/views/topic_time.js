/**
 * Created by yan on 18-5-16.
 */
// var colors = ['#8dd3c7', '#ffffb3', '#bebada', '#fb8072', '#80b1d3', '#fdb462', '#b3de69', '#fccde5', '#d9d9d9',
//     '#bc80bd', '#ccebc5', '#ffed6f'];

var height = window.innerHeight * 0.3;
var row_height = 32;
// $("#topic-time").parent().height(height);
$("#topic-time").height(height);

var dom = document.getElementById("topic-time");
var timechart = echarts.init(dom);

function componentToHex(c) {
    var hex = c.toString(16);
    return hex.length == 1 ? "0" + hex : hex;
}

var selected_topics = [];

function hexToRgb(hex) {
    var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : null;
}

var topic_time_option = {
    title: {
        text: 'Temporal Matrix Scatter Plot',
         textStyle:{
            fontSize: 12
        }
    },
    // legend: {
    //     data: ['Punch Card'],
    //     left: 'right'
    // }
    toolbox: {
        showTitle: true,
        // show: true,
        itemSize: 20,
        zlevel: 1000,
        // left:'left' ,
        top: 8,
        right: 6,
        // bottom: 5,
        feature: {
            myTool1: {
                show: true,
                title: "reset",
                icon: 'image://static/images/reset.png',
                onclick: function () {
                    selected_topics = [];
                    data_set_by_topic();
                }
            }
        }
    },
    tooltip: {
        // position: 'top',
        trigger: 'axis',
        showContent: false
        // formatter: function (params) {
        //     console.log(params);
        //     return params.value[2] + ' commits in ' + hours[params.value[0]] + ' of ' + topics[params.value[1]];
        // }
    },
    grid: {
        left: 2,
        top: 35,
        right: 15,
        containLabel: true
    },
    xAxis: {
        type: 'category',
        data: hours,
        boundaryGap: false,
        splitLine: {
            show: true,
            lineStyle: {
                color: '#999',
                type: 'dashed'
            }
        },
        axisLine: {
            show: false
        },
        position: 'top',
        axisPointer: {
            show: false
        }
    },
    yAxis: {
        type: 'category',
        data: topics,
        boundaryGap: false,
        splitLine: {
            show: true,
            lineStyle: {
                color: '#999',
                type: 'dashed'
            }
        },
        axisLine: {
            show: false
        },
        axisLabel: {
            textStyle: {
                color: function (val, idx) {
                    return topic_colors[idx];
                }
            }
        },
        inverse: true,
        axisPointer: {
            type: 'line',
            show: true,
            value: 0,
            // snap: true,
            lineStyle: {
                color: '#000099',
                opacity: 0.5,
                width: 2
            },
            status: 'show',
            label: {
                show: false,
                // formatter: function (params) {
                //     // var hour = params.value.slice(0, -2);
                //     getregiondist(hour);
                //     return "";
                // },
                backgroundColor: '#FFFFFF'
            }
        }
    },
    // brush: {
    //     xAxisIndex: 'all',
    //     brushLink: 'all',
    //     outOfBrush: {
    //         colorAlpha: 0.4
    //     },
    //     throttleType:'debounce',
    //     throttleDelay: 300
    // },
    series: [{
        name: 'Temporal Matrix Scatter Plot',
        type: 'scatter',
        symbolSize: function (val) {
            return val[2];
        },
        // data: data,
        hoverAnimation: false,
        // animationDelay: function (idx) {
        //     return idx * 5;
        // },
        // itemStyle: {
        //     normal: {
        //         color: function (val) {
        //             console.log(val);
        //             var rgb_color = hexToRgb(topic_colors[val.data[1]]);
        //             // console.log(rbga_color);
        //             // console.log(topic_colors[val.data[1]]);
        //             return 'rgba('+rgb_color.r+","+rgb_color.g+","+rgb_color.b+","+val.data[3]*255+")"
        //         },
        //         opacity: function (val) {
        //             console.log(val);
        //             return val.data[3];
        //         }
        //     }
        // }
    }]
};

$.get('/gettopichour/', function (data) {
    data = data.data;
    data = data.map(function (item) {
        return {value: [item[1], item[0], item[2]*num_topics*15], label: {}, itemStyle:{ normal: {color: topic_colors[item[0]], opacity: 1.0}}};
    });

    topic_time_option.series[0].data = data;
    // console.log(option);
    timechart.setOption(topic_time_option, true);
});


timechart.off('click');
function data_set_by_topic(){
    var data = topic_time_option.series[0].data;
    data = data.map(function (item) {
        if(selected_topics.length > 0){
            var index = selected_topics.indexOf(item.value[1]);
            if(index >-1){
                item.itemStyle.normal.opacity = 1.0;
                return item;
            }else {
                item.itemStyle.normal.opacity = 0.3;
                return item;
            }
        }else {
            item.itemStyle.normal.opacity = 1.0;
            return item;
        }
    });
    topic_time_option.series[0].data = data;
    // console.log(option);
    timechart.setOption(topic_time_option, true);
    filter_topic_region_by_topics(selected_topics);
}

timechart.on('click', function (params) {
    console.log(params); // do whatever you want with another chart say chartTwo here
    var row = params.data.value[1];
    var index = selected_topics.indexOf(row);
    if (index > -1) {
        selected_topics.splice(index, 1);
    }else {
        selected_topics.push(row);
    }
    data_set_by_topic();
});

