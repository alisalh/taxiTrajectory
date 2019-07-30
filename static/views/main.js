/**
 * Created by yan on 18-7-20.
 */
var num_topics = 8;

var topic_colors = ['#1f78b4', '#33a02c', '#fb9a99', '#e31a1c', '#cab2d6',
   '#6a3d9a',  '#ff7f00', '#b15928']; 
var hours = ['6am', '7am', '8am', '9am', '10am', '11am',
    '12pm', '1pm', '2pm', '3pm', '4pm', '5pm',
    '6pm', '7pm', '8pm', '9pm', '10pm', '11pm'];
// topic id
var topics = Array.apply(null, Array(num_topics)).map(function (_, i) {
    return 'Topic ' + (i + 1);
});


// the value of input changes as the slider 
$("#min_support").slider().on("slide", function(){
    $("#min_support_input").val($("#min_support").slider('getValue'))});
$("#min_confidence").slider().on("slide", function(){
    $("#min_confidence_input").val($("#min_confidence").slider('getValue'))});
$("#min_trajectory_length").slider().on("slide", function(){
    $("#min_trajectory_length_input").val($("#min_trajectory_length").slider('getValue'))});
$("#topic_threshold").slider().on("slide", function(){
    $("#topic_threshold_input").val($("#topic_threshold").slider('getValue'))});

function sortchange(event) {
    var x = $(this).text()+" <span class='caret'></span>"; //span is the arrow
    $(".dropdown button").html(x);  // show the selected text
     $.post('/sortphrase/', {"method": $(this).text()}, function (jsondata) {
        create_sub_trajectory_table(table_data, jsondata.data.data);
     });
}
$(".dropdown-menu li a").on('click', sortchange);

$("#searchbtn").on('click', function () {
   var search_content = $("#search_content").val();
   if(search_content !== ""){
        $.post('/searchphrase/', {"content": search_content}, function (jsondata) {
            create_sub_trajectory_table(table_data, jsondata.data.data);
         });
   }
});

// search only by name
$("#search_content").on('change', function () {
    if($(this).val()===''){
         $.post('/sortphrase/', {"method": 'name'}, function (jsondata) {
             create_sub_trajectory_table(table_data, jsondata.data.data);
         });
    }
});

var map_coords = [];