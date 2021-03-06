﻿function updateChoices() {
    deleteMarkers();
    deleteHeatmap();
    deleteGraphs();

    var startdate = $("#targetdate :input[name=startdate]").val();
    var enddate = $("#targetdate :input[name=enddate]").val();
    var coords = rectangle.getBounds().getNorthEast().lat() + "," + rectangle.getBounds().getNorthEast().lng() + "," + rectangle.getBounds().getSouthWest().lat() + "," + rectangle.getBounds().getSouthWest().lng();
    if (!rectangle.getMap()) {
        coords = null;
    }
    var unitsarray = []
    $("#unitholder :input[name='unitpicker[]']:checked").each(function ()
    {
        unitsarray.push(this.value);
    });
    var typesarray = []
    $("#typeholder :input[name='typepicker[]']:checked").each(function ()
    {
        typesarray.push(this.value);
    });
    loadData({coords:coords, startdate:startdate, enddate:enddate, units:unitsarray, types:typesarray});
}
</script>

<script>
var map;
var rectangle;
var markers = [];
var heatmapdata = [];
var heatmap = null;
var loadRequest = null;
var markerCluster = null;

function deleteMarkers() {
    for (var i = 0; i < markers.length; i++) {
        markers[i].setMap(null);
    }
    markers = [];

    if (markerCluster) {
        markerCluster.clearMarkers();
    }
}

function deleteHeatmap() {
    if (heatmap) {
        heatmap.setMap(null);
    }
    heatmapdata = [];
}

$("#clearEventTypes").click(function(e){
    $("#typeholder").find("input").prop('checked',false);
    e.preventDefault();
});
$("#clearUnits").click(function(e){
    $("#unitholder").find("input").prop('checked',false);
    e.preventDefault();
});

$("#regionOn").click(function(e){
    rectangle.setMap(map);
    $("#regionDropdown").find("li").removeClass("active");
    $(this).parent().addClass('active');
    e.preventDefault();
});
$("#regionOff").click(function(e){
    rectangle.setMap(null);
    $("#regionDropdown").find("li").removeClass("active");
    $(this).parent().addClass('active');
    e.preventDefault();
});

function deleteGraphs() {
    d3.selectAll("svg").html("");
}

function loadData(options={}) {
          var units = options.units || [];
var types = options.types || [];
var coords = options.coords || null;
var startdate = options.startdate || null;
var enddate = options.enddate || null;
var params = [];
if (coords) {
    params.push({name:"region", value:coords});
}
for (var i in units) {
    params.push({name:"unit", value:units[i]});
}
for (var i in types) {
    params.push({name:"type", value:types[i]});
}
if (startdate) {
    params.push({name:"startdate", value:startdate});
}
if (enddate) {
    params.push({name:"enddate", value:enddate});
}

$('#loading').modal('show');

function getAllEventsContent(items) {
    output = '';
    console.log(items);

    for (i in items) {
        output = output + getEventContent(items[i]);
    }
    return output;
}
function getEventContent(item) {
    var output = '<p>';
    output = output + 'Date: ' + item.datetime + '<br/>';
    output = output + 'Place: ' + item.rawlocation + '<br/>';
    output = output + 'Type: ' + item.type + '<br/>';
    var sep = 'Units: ';
    for (var i = 0, len = item.unit.length; i < len; i++) {
        output = output + sep + item.unit[i];
        sep = ', ';
    }
    /*
    can't use tweets - SeattleFire deletes too many
    if (item.tweet && item.tweet.length > 0) {
        var sep = '<br/>Tweets: ';

        for (var i = 0, len = item.tweet.length; i < len; i++) {
//  item.tweet[i]
            output = output + sep + '<a href="https://twitter.com/SeattleFire/status/' + item.tweet[i] +'">tweet</a>';
            sep = ', ';
        }
    }
    */
    output = output + '</p>';
    return output;
}
      
if (loadRequest) {
    loadRequest.abort();
}

loadRequest = $.ajax({
    url: "/query?"+ $.param(params)
}).done(function(data) {
    loadRequest = null;

    $('#loading').modal('hide');

    if ($.isEmptyObject(data['incident'])) {
        $('#messageBody').html('No incidents match your search criteria.');
        $('#message').modal('show');
        return;
    }

    var maptype = data.display;
    for (var key in data['incident']) {
        var item = data.incident[key];
        var latLng = new google.maps.LatLng(item.location[0],item.location[1]);
        if (maptype == "all") {
            var marker = new google.maps.Marker({
                position: latLng,
                map: map,
                number: data.incident[key].number
            });
            marker.addListener('click', function() {
                var thisMarker = this;
                var contentString = "loading details...";
                if (thisMarker.detail) {
                    contentString = getAllEventsContent(thisMarker.detail);
                }
                thisMarker.infowindow = new google.maps.InfoWindow({
                    content: contentString
                });
                if (!thisMarker.infowindow.isOpen()) {
                    thisMarker.infowindow.open(map, thisMarker);
                }
                if (!thisMarker.detail) {
                    loadRequest = $.ajax({
                        url: "/detail?number=" + this.number
                    }).done(function(data) {
                        thisMarker.detail = data;
                        thisMarker.infowindow.close();
                        thisMarker.infowindow = new google.maps.InfoWindow({
                            content: getAllEventsContent(data)
                        });
                        thisMarker.infowindow.open(map, thisMarker);
                    })
                }
            });
            markers.push(marker);
        } else if (maptype == "heatmap") {
            heatmapdata.push(latLng);
        }
    }

    markerCluster = new MarkerClusterer(map, markers,
        {
            imagePath: 'https://developers.google.com/maps/documentation/javascript/examples/markerclusterer/m',
            zoomOnClick: false
        });
    if (maptype == "heatmap") {
        heatmap = new google.maps.visualization.HeatmapLayer({
            data: heatmapdata,
            radius: 50
        });
        heatmap.setMap(map);
    }

    google.maps.event.addListener(markerCluster, 'click', function(cluster) {
        console.log("click");
        var thisMarkerCluster = cluster;
        if (!thisMarkerCluster.infowindow) {
            if (thisMarkerCluster.getSize() <= 10) {
                var contentString = "loading details...";
                if (thisMarkerCluster.detail) {
                    contentString = getAllEventsContent(thisMarkerCluster.detail);
                }
                thisMarkerCluster.infowindow = new google.maps.InfoWindow({
                    content: contentString
                });
            } else {
                thisMarkerCluster.infowindow = new google.maps.InfoWindow({
                    content: "Too many incidents to show details"
                });
                thisMarkerCluster.detail = true;
            }
        }
        if (!thisMarkerCluster.infowindow.isOpen()) {
            thisMarkerCluster.infowindow.setPosition(thisMarkerCluster.getCenter())
            thisMarkerCluster.infowindow.open(map);

        }
        if (!thisMarkerCluster.detail) {
            args = '';
            for (i in thisMarkerCluster.getMarkers()) {
                args = args + '&number=' + thisMarkerCluster.getMarkers()[i].number
            }
            loadRequest = $.ajax({
                url: "/detail?" + args
            }).done(function(data) {
                thisMarkerCluster.detail = data;
                thisMarkerCluster.infowindow.close();
                console.log("cat");
                thisMarkerCluster.infowindow = new google.maps.InfoWindow({
                    content: getAllEventsContent(data)
                });
                thisMarkerCluster.infowindow.setPosition(thisMarkerCluster.getCenter())
                thisMarkerCluster.infowindow.open(map);
            })
        }
    });

    var weekdaygraphdata = data['totals']['weekday'];
            
    setgraph(weekdaygraphdata, ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], "#weekdaychart");

    var monthdgraphdata = data['totals']['month'];
    monthdgraphdata.shift();
            
    setgraph(monthdgraphdata, ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], "#monthchart");

    var hourgraphdata = data['totals']['hour'];
    function hourname(num) {
        if (num == 0) return ('12:00 AM');
        if (num > 12) return ((num - 12) + ':00 PM');
        return num + ':00 AM';
    }
    setgraph(hourgraphdata, (function() {var a = []; var start = 0; var stop = 24; while(start < stop){ a.push(hourname(start++));}; return a; })(), "#hourchart"); // should add a.m./p.m.

    var yeargraphdata = $.map(data['totals']['year'], function(value, key) { return value });
            
    setgraph(yeargraphdata, $.map(data['totals']['year'], function(value, key) { return key }), "#yearchart");

    var unitgraphdata = data['totals']['unit'];
    var largest = [0];
    for (var key in unitgraphdata){
        if (unitgraphdata[key] > Math.min(...largest)) {
            largest.push(unitgraphdata[key]);
            largest.sort(function(a, b){return a-b});
            if (largest.length > 10) {
                largest.shift();
            }
        }
    }
    for (var key in unitgraphdata){
        if (unitgraphdata[key] < Math.min(...largest)) {
            delete unitgraphdata[key];
        }
    }
          
    setgraph($.map(unitgraphdata, function(value, key) { return value }), $.map(unitgraphdata, function(value, key) { return key }), "#unitchart");

    var typegraphdata = data['totals']['type'];
    largest = [0];
    for (var key in typegraphdata){
        if (typegraphdata[key] > Math.min(...largest)) {
            largest.push(typegraphdata[key]);
            largest.sort(function(a, b){return a-b});
            if (largest.length > 10) {
                largest.shift();
            }
        }
    }
    for (var key in typegraphdata){
        if (typegraphdata[key] < Math.min(...largest)) {
            delete typegraphdata[key];
        }
    }
          
    setgraph($.map(typegraphdata, function(value, key) { return value }), $.map(typegraphdata, function(value, key) { return key }), "#typechart");
    $('#data').modal('show');
}).fail(function(data) {
    loadRequest = null;

    $('#loading').modal('hide');
    $('#messageBody').html('Data load failed.');
    $('#message').modal('show');
});
}
        
function updateRect() {
    updateChoices();
}

function initMap() {
    google.maps.InfoWindow.prototype.isOpen = function(){
        var map = this.getMap();
        return (map !== null && typeof map !== "undefined");
    }

    $('#about').modal('show');

    map = new google.maps.Map(document.getElementById('map'), {
        zoom: 11,
        center: new google.maps.LatLng(47.65,-122.28),
        mapTypeId: 'terrain'
    });
    rectangle = new google.maps.Rectangle({
        strokeColor: '#FF0000',
        strokeOpacity: 0.8,
        strokeWeight: 2,
        fillColor: '#FF0000',
        fillOpacity: 0.15,
        editable: true,
        bounds: {
            north: 47.73548,
            south: 47.500876,
            east: -122.24447,
            west: -122.44
        }
    });
    google.maps.event.addListener(map, 'zoom_changed', function () {
        //          heatmap.setOptions({radius:getNewRadius()});
        // {radius:Math.floor(desiredRadiusPerPointInMeters*pixelsPerMeter)}
    });
};

$(document).ready(function(e) {
    $.ajax({
        url: "/units"
    }).done(function(data) {
        var unitContent = $("<div class='row-fluid'></div>");
        for (item in data) {
            unitContent.append('<div class="col-md-3"><input type="checkbox" name="unitpicker[]" value="' + item + '"><a class="u" href="#" data-toggle="tooltip" title="' + data[item].type + '&#10;' + data[item].location + '">' + item + '</a></div>');

        }
        $("#unitholder").append($("<div class='container-fluid'></div>").append(unitContent));
    });
    $.ajax({
        url: "/types"
    }).done(function(data) {
        var dataCats = {};
        for (var item in data) {
            for (var cat in data[item]) {
                if (dataCats.hasOwnProperty(data[item][cat])) {
                    dataCats[data[item][cat]].push(item);
                } else {
                    dataCats[data[item][cat]] = [item];
                }
            }
        }

        var typeContent = $("#typeholder");
        var panelContent = $('<div class="panel-group"></div>')
        for (var property in dataCats) {
            if (dataCats.hasOwnProperty(property)) {
                var groupContent = $("<div class='row-fluid'></div>");
                for (var item in dataCats[property]){
                    groupContent.append('<div class="col-md-6"><input type="checkbox" name="typepicker[]" value="' + dataCats[property][item] + '">' + dataCats[property][item] + '</div>');
                }

                var groupHeader = '<div class="panel-heading"><h4 class="panel-title"><a data-toggle="collapse" href="#collapse' + property + '">' + property + '</a></h4></div>';
                panelContent.append(groupHeader);
                panelContent.append($('<div id="collapse' + property + '" class="panel-collapse collapse"></div>').append($('<div class="panel-body"></div>').append(groupContent)));
                typeContent.append(panelContent);
            }
        }
    });

});
        
function setgraph(data, labels, graphname) {
    var width = 150,
        barHeight = 20;

    var x = d3.scaleLinear()
        .domain([0, d3.max(data)])
        .range([0, width]);

    var chart = d3.select(graphname)
        .attr("width", width * 2)
        .attr("height", barHeight * data.length);

    var bar = chart.selectAll("g")
        .data(data)
        .enter().append("g")
        .attr("transform", function(d, i) { return "translate(0," + i * barHeight + ")"; });

    bar.append("rect")
        .attr("width", x)
        .attr("height", barHeight - 1);

    bar.append("text")
        .attr("x", function(d) { return x(d) + 3; })
        .attr("y", barHeight / 2)
        .attr("dy", ".35em")
        .text(function(d, i) { return labels[i] + " (" + d + ")"; });

    bar.append("svg:title")
            .text(function(d, i) { return labels[i] + ' (' + data[i] + ')'; })
};