/**
 * Created by yan on 18-6-12.
 */
// var n = 20, // number of layers
//     m = 200, // number of samples per layer
//     k = 10; // number of bumps per layer
var hours = ['6am-9am', '9am-12am', '12am-3pm', '3pm-6pm', '6pm-9pm', '9pm-12pm'];

var svg_height = window.innerHeight * 0.32;
var margin = [10, 20, 40, 30];
var svg = d3.select("#topic-flow").append("svg").attr("height", svg_height).attr("width", $("#topic-flow").width()).append("g")
                    .attr("transform", "translate("+margin[2]+"," + margin[0] + ")").attr("class", 'chart');

var width = $("#topic-flow").width()-margin[2]-margin[3];
var height = svg_height-margin[0]-margin[1];

for(var i=0;i<num_topics;i++){
    for(var j=0;j<num_topics;j++){
        var defs = svg.append("defs");
        var linearGradient = defs.append("linearGradient")
            .attr("id", "gc"+i+"_"+j)
            .attr("x1", "0%").attr("y1", "0%")
            .attr("x2", "100%").attr("y2", "0%");
        var stop1 = linearGradient.append("stop").attr("offset", "0%").attr("stop-color", topic_colors[i]);
        var stop2 = linearGradient.append("stop").attr("offset", "100%").attr("stop-color", topic_colors[j]);

    }
}
var num_topics = 8;
var flow_height = height/(num_topics);

var x = d3.scaleLinear()
    .domain([-0.01, 5.01])
    .range([0, width]);

var y = d3.scaleLinear()
    //.domain([0, d3.max(layers0, stackMax)])
    .range([0, flow_height]);

var topics_scale = d3.scaleLinear().range([0, height]).domain([0, num_topics-0.001]);


var z = d3.interpolateCool;

var area = d3.area() //.curve(d3.curveCardinalOpen)
    .x(function(d) { return x(d.x0); })
    .y0(function(d) { return d.topic*flow_height+y(d.y0); }) //+
    .y1(function(d) { return d.topic*flow_height+y(d.y0+d.height); }); //+(+)/2
area.curve(d3.curveBasis);

function stackMax(d) {
    return d3.max([d[0].y0 + d[0].height, d[4].y0 + d[4].height]);
}

svg.append("g").attr("class", "x-axis")
    .attr("transform", "translate(0," + (height) + ")").call(d3.axisBottom(x).ticks(6).tickFormat(function(d){return hours[d]}));

svg.append("g").attr("class", "y-axis") //.attr("transform", "translate(100," + "0)")
    .call(d3.axisLeft(topics_scale).ticks(7).tickFormat(function(d){return "Topic "+(d+1)}));

d3.selectAll(".y-axis text").style("transform", "translate(0px, "+(0)+"px) rotate(-60deg)");

var vertical = d3.select("#topic-flow")
        .append("div")
        .attr("class", "remove")
        .style("position", "absolute")
        .style("z-index", "19")
        .style("width", "2px")
        .style("height", (height-flow_height+9)+"px")
        .style("top",  1)
        .style("bottom", flow_height+15+"px")
        .style("left", margin[2])
        .style("background", "#000099");

var pre_hour = 0;
d3.select("#topic-flow svg").on("mousemove", function(){
         var mousex = d3.mouse(this);
         //console.log(mousex[0]);
         var x_value = Math.floor(x.invert(mousex[0]-margin[2]));
         //console.log(x_value);
         if(x_value < 0 || (mousex[0]-margin[2]) > width){
             return
         }
         if(x_value != pre_hour){
             gettopicregiondist(x_value+"");
             pre_hour = x_value;
         }

         var mousex = mousex[0];
         vertical.style("left", mousex + "px" )})
      .on("mouseover", function(){
         var mousex = d3.mouse(this);
         //console.log(mousex[0]);
         var x_value = Math.floor(x.invert(mousex[0]-margin[2]));
         if(x_value < 0 || (mousex[0]-margin[2])> width){
             return
         }
         if(x_value != pre_hour){
             gettopicregiondist(x_value+"");
             pre_hour = x_value;
         }
         //console.log(x_value);
         var mousex = mousex[0];
         vertical.style("left", mousex + "px")});


$.get('/gettopichour/', function (data) {
    data = data.data;
    y.domain([0, d3.max(data, stackMax)]);
    data.unshift([]);
    data.unshift([]);
    console.log(data);

    svg.selectAll("path")
      .data(data)
      .enter().append("path")
        .attr("d", area)
        .attr("fill", function(d) { return 'url(#'+"gc"+d[0].topic+"_"+d[4].topic+')'});
    // var colorRect = svg.append("rect")
    //             .attr("x", 0)
    //             .attr("y", 0)
    //             .attr("width", 200)
    //             .attr("height", 30)
    //             .attr("fill", "url(#gc1_2)");
});



//
//
//
//

//


//
// function stackMin(layer) {
//   return d3.min(layer, function(d) { return d[0]; });
// }
//
// function transition() {
//   var t;
//   d3.selectAll("path")
//     .data((t = layers1, layers1 = layers0, layers0 = t))
//     .transition()
//       .duration(2500)
//       .attr("d", area);
// }
//
// // Inspired by Lee Byron’s test data generator.
// function bumps(n, m) {
//   var a = [], i;
//   for (i = 0; i < n; ++i) a[i] = 0;
//   for (i = 0; i < m; ++i) bump(a, n);
//   return a;
// }
//
// function bump(a, n) {
//   var x = 1 / (0.1 + Math.random()),
//       y = 2 * Math.random() - 0.5,
//       z = 10 / (0.1 + Math.random());
//   for (var i = 0; i < n; i++) {
//     var w = (i / n - y) * z;
//     a[i] += x * Math.exp(-w * w);
//   }
// }