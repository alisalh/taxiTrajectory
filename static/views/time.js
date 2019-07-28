/**
 * Created by yan on 18-6-10.
 */

// var height = window.innerHeight * 0.32;
// $("#time").height(height);
//
// var dom = document.getElementById("time");
// var timelinechart = echarts.init(dom);
// //
// $("#general_time_span").height(height);
// var time_span_dom = document.getElementById("general_time_span");
// var general_time_span_chart = echarts.init(time_span_dom);
//
//
//
// $.get("/gethourdist/", function (data) {
//     data = data.data;
//     console.log(data);
//     var option = {
//         title: {
//             text: 'General Taxi Time Distribution',
//             textStyle:{
//                 fontSize: 12
//             }
//         },
//         // tooltip: {
//         //     trigger: 'axis'
//         //     // position: function (pt) {
//         //     //     return [pt[0], 130];
//         //     // }
//         // },
//         grid: {
//             left: 0,
//             top: 30,
//             right: 0,
//             bottom: 30,
//             containLabel: true
//         },
//         xAxis: {
//             type: 'category',
//             data: hours
//             // axisPointer: {
//             //     type: 'line',
//             //     show: true,
//             //     value: 0,
//             //     // snap: true,
//             //     lineStyle: {
//             //         color: '#000099',
//             //         opacity: 0.5,
//             //         width: 2
//             //     },
//             //     status: 'show',
//             //     label: {
//             //         show: false,
//             //         // formatter: function (params) {
//             //         //     // var hour = params.value.slice(0, -2);
//             //         //     getregiondist(hour);
//             //         //     return "";
//             //         // },
//             //         backgroundColor: '#FFFFFF'
//             //     }
//             //     // // handle: {
//             //     // //     show: true,
//             //     // //     color: '#FFFFFF',
//             //     // //     size: 0
//             //     // // }
//             // }
//         },
//         yAxis: {
//             type: 'value'
//         },
//         series: [{
//             data: data,
//             type: 'line',
//             smooth: true
//         }]
//     };
//     timelinechart.setOption(option);
//     // timelinechart.on("click", function (params) {
//     //    console.log(params);
//     // });
// });
//
// $.get('/gettimespandist/', function (data) {
//     data = data.data;
//     console.log(data);
//     var option = {
//         title: {
//             text: 'General Taxi Time Interval Distribution',
//             textStyle:{
//                 fontSize: 12
//             }
//         },
//         // tooltip: {
//         //     trigger: 'axis'
//         //     // position: function (pt) {
//         //     //     return [pt[0], 130];
//         //     // }
//         // },
//         grid: {
//             left: 0,
//             top: 30,
//             right: 0,
//             bottom: 30,
//             containLabel: true
//         },
//         xAxis: {
//             type: 'category',
//             data: ['10min', '20min', '30min', '40min', '50min', '60min', '70min', '80min', '90min', '100min', '110min', '120min', '>120min']
//         },
//         yAxis: {
//             type: 'value'
//         },
//         series: [{
//             data: data,
//             type: 'line',
//             smooth: true
//         }]
//     };
//     general_time_span_chart.setOption(option);
// });
//
