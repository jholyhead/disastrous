var AMBULANCE = "Ambulance";
var FIREFIGHTER = "Firefighter";
var OFFICER = "Police";
var INJURY = "Injury";
var FIRE = "Fire";
var CRIME = "Crime";

var map;
var ajaxRequest;
var plotlist;
var plotlayers = [];

var host = "localhost";
var leaderboardHost = "192.168.1.3";

var simId;
var userId;
var markers = {};
var selectedResponder = null;
var selectedIncident = null;
var glHandle = null; //Game Loop Handler

var score = 0;
var agent = false

function initagent(){
    agent = true;
    initmap();
}

function initmap() {
	// set up the map
	map = new L.Map('gamemap',{zoomControl: false});

	// create the tile layer with correct attribution
	//var osmUrl = 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
	var osmUrl = 'http://192.168.1.3/osm_tiles/{z}/{x}/{y}.png';
	var osmAttrib = 'Map data � <a href="http://152.78.65.25">OpeStreetMap</a> contributors';
	var osm = new L.TileLayer(osmUrl, { minZoom: 1, maxZoom: 18, attribution: osmAttrib });

	// start the map in bham
	map.setView(new L.LatLng(52.44288024412103, -1.9408866197262975), 14);
	map.addLayer(osm);
	// disable drag and zoom functionality
	map.dragging.disable();
	map.touchZoom.disable();
	map.doubleClickZoom.disable();
	map.scrollWheelZoom.disable();
	if (map.tap) map.tap.disable();
	
	//get the scoreboard
	getScoreboard();
	
	$( "#gameStartDialog" ).dialog({
		resizable: false,
		height:500,
		width:750,
		modal: true					  
	});
	$("#gameEndDialog").hide();
	
	$("#btnStart").click(function() {
        $( "#gameStartDialog" ).dialog( "close" );
        createSimulation(false);
    });
    $("#btnStartAgent").click(function() {
        $( "#gameStartDialog" ).dialog( "close" );
        
        
        createSimulation();
    });
}

function getAvailableSimulations() {
	$.ajax({
		url: "http://" + host + ":1234/availableSimulations",
		dataType: "jsonp",
		data: {},
		success: function (response) {
			var simIdSelect = $('#simIdSelect')
			$.each(response, function(val, text) {
				simIdSelect.append($('<option></option>').val(val).html(text));
			});
		},
		error: function (jqXHR, textStatus, errorThrown) { console.log(textStatus, errorThrown); }
	});
}

function createSimulation() {
	
	bounds = map.getBounds();
	var margin = 0.003;
	$.ajax({
		url: "http://" + host + ":1234/createSimulation",
		dataType:"jsonp",
		data: { seed: 4, timespan: 150, maxChildren: 1, minLat: bounds.getNorth()-margin, minLong: bounds.getWest()+margin, maxLat: bounds.getSouth()+margin, maxLong: bounds.getEast()-margin, fireFighters: 2, officers: 2, ambulances: 2, initialFires: 2, initialInjuries: 3, initialLooters: 3 },
		success: function(response) {
			simId = response;
			console.log("Simulation "+ simId + " created");
			connectUser();
		},
		error: function (jqXHR, textStatus, errorThrown) { console.log(textStatus, errorThrown); }
	});

}

function connectUser() {
	//connect and start
	var url = "http://" + host + ":1234/" + simId + "/connectUser";
	if(agent){
	   url = "http://" + host + ":1234/" + simId + "/addAgent";
	}
	
	$.ajax({
		url: url,
		dataType: "jsonp",
		data: {},
		success: function (response) {
			userId = response;
			console.log("User " + userId + " connected");
			$(function() {
				startGame();
			});
		},
		error: function (jqXHR, textStatus, errorThrown) { console.log(textStatus, errorThrown); }
	});
	
}

function startGame(){//start simulation
	$.ajax({
		url: "http://" + host + ":1234/" + simId + "/start",
		dataType: "jsonp",
		data: { },
		success: function (response) {
			console.log("simulation started");
			startGameLoop();
		},
		error: function (jqXHR, textStatus, errorThrown) { console.log(textStatus, errorThrown); }
	});

}

function startGameLoop() {
	//first initialize our simulation
	getResponders();
	getIncidents();

	
	glHandle = setInterval(gameLoop, 1000);
		
	
}

function gameLoop() {
	getIncidents();
	getResponders();
	getScore();
}

function getScore() {
	$.ajax({
		url: "http://" + host + ":1234/" + simId + "/" + userId + "/score",
		dataType: "jsonp",
		data: {},
		success: function (response) {
			score = parseInt(response);
			$("#gamescore").text(score);
		},
		error: function (jqXHR, textStatus, errorThrown) { console.log(textStatus, errorThrown); }
	});
}

function getResponders() {

	$.ajax({
		url: "http://" + host + ":1234/" + simId + "/" + userId + "/responders",
		dataType: "jsonp",
		data: {},
		success: function (response) {
			//loop through responders and create markers
			//ambulance
			for (responder in response.ambulances) {
				resObj = response.ambulances[responder];
				pos = {lat:resObj.route[0][0], lon:resObj.route[0][1]};
				path = resObj.route;
				speed = resObj.speed;
				obj = { id: responder, pos: pos, path: path, speed:speed };
				createOrEditMarker(AMBULANCE, obj);
			}
			//firefighters
			for (responder in response.fireFighters) {
				resObj = response.fireFighters[responder];
				pos = {lat:resObj.route[0][0], lon:resObj.route[0][1]};
				path = resObj.route;
				speed = resObj.speed;
				obj = { id: responder, pos: pos, path: path, speed:speed };
				createOrEditMarker(FIREFIGHTER, obj);
			}
			//officers
			for (responder in response.officers) {
				resObj = response.officers[responder];
				pos = {lat:resObj.route[0][0], lon:resObj.route[0][1]};
				path = resObj.route;
				speed = resObj.speed;
				obj = { id: responder, pos: pos, path: path, speed:speed };
				createOrEditMarker(OFFICER, obj);
			}
		},
		error: function (jqXHR, textStatus, errorThrown) { console.log(textStatus, errorThrown); }
	});
}


function getIncidents() {

	$.ajax({
		url: "http://" + host + ":1234/" + simId + "/" + userId + "/incidents",
		dataType: "jsonp",
		data: {},
		success: function (response) {
			//loop through incidents and create markers
			//injury
			ids = [];

			if (response.injury == undefined) { //if no incidents
				simulationEnded();
			} else{			
				for (incident in response.injury) {
					obj = { id: incident, pos: response.injury[incident] };
					createOrEditMarker(INJURY, obj);
					ids.push(obj.id);
				}
				//fires
				for (incident in response.fire) {
					obj = { id: incident, pos: response.fire[incident] };
					createOrEditMarker(FIRE, obj);
					ids.push(obj.id);
				}
				//crimes
				for (incident in response.looters) {
					obj = { id: incident, pos: response.looters[incident] };
					createOrEditMarker(CRIME, obj);
					ids.push(obj.id);
				}
				//remove old incidents
				removeOldIncidents(ids);
			}
		},
		error: function (jqXHR, textStatus, errorThrown) { console.log(textStatus, errorThrown); }
	});

}

function simulationEnded(){
	//stop the game loop
	clearInterval(glHandle);
	
	//stop the responder animations
	for (m in markers) {
		markers[m].stop();
	}
	//gray out the screen
	$("#gamecontainer img").css("-webkit-filter", "grayscale(100%)");
	
	//display dialog
	$("#gameEndDialog").dialog({
		resizable: false,
		height:300,
		width:750,
		modal: true,
		closeOnEscape: false,
		title: "Submit your Score - " + score
	});	
	getHighScore();
	$("#btnSubmit").click(function() {
		$("#gameEndDialog" ).dialog( "close" ); 		
		submitToLeaderBoard();
		location.reload();
	});
	
	
}

function getHighScore(){
	$.ajax({
		url: "http://" + leaderboardHost + ":1234/scoreboard",
		dataType: "jsonp",
		data: {},
		success: function (response) {
			response.push(score);
			response.sort(sortNumber);
			
			var position = response.indexOf(score) + 1;
			
			$("#highScore").text(parseInt(response[0]));
			if (position >= 1) {
				$("#scorePosition").text("You came "+position+nth(position));
			}
		},
		error: function (jqXHR, textStatus, errorThrown) { console.log(textStatus, errorThrown); }
	});
}

function sortNumber(a,b) {
    return b - a;
}

function getScoreboard(){
	$.ajax({
		url: "http://" + leaderboardHost + ":1234/scoreboard",
		dataType: "jsonp",
		data: {},
		success: function (response) {
			for (index in response) {
				if (index > 20) {
					break;
				}
				var colorclass = index % 2 ? "scbdEven" : "scbdOdd";
				$("#scoreboard").append(
					$("<li></li>")
						.addClass(colorclass)
						.html("<span class='scbdPos'>"+(1+parseInt(index))+"</span>"+response[index])
				);
			}
		},
		error: function (jqXHR, textStatus, errorThrown) { console.log(textStatus, errorThrown); }
	});
}

function nth(d) {
  if(d>3 && d<21) return 'th';
  switch (d % 10) {
        case 1:  return "st";
        case 2:  return "nd";
        case 3:  return "rd";
        default: return "th";
    }
} 

function submitToLeaderBoard(fname, sname, school){
	console.log("Submiting to leader board: " + fname + " " + sname + " " + school);
	$.ajax({
		url: "http://" + leaderboardHost + ":1234/postScore",
		dataType: "jsonp",
		data: {firstname:fname, surname:sname, school:school, score:score},
		success: function (response) {
			console.log("Successfully Submitted Score");
			
		},
		error: function (jqXHR, textStatus, errorThrown) { console.log(textStatus, errorThrown); }
	});
}

function removeOldIncidents(incidents) {
	for (m in markers) {
		
		if (incidents.indexOf(m) == -1 && !(isResponder(markers[m].type))) {
			map.removeLayer(markers[m]);
			
			//add a completed tick marker
			var pos = markers[m].getLatLng()
			var icon = L.icon({
				iconUrl: "images/task_complete.png",
				iconSize: [40,40],
				iconAnchor: [20,20]
			});
			completed = L.marker([pos.lat, pos.lng], {icon: icon, clickable:false});
			map.addLayer(completed);
			$(completed._icon).css("pointer-events","none");
			$(completed._icon).fadeOut({
				duration:10000,
				complete:function() {
					map.removeLayer(completed);
				}
			});
			
			delete markers[m];
		} else {
		}
	}
}

function isResponder(type) {
	return type == AMBULANCE || type == FIREFIGHTER || type == OFFICER;
}

function getResponderIncident(type) {
	if (!(isResponder(type))) {
		return "NONE";
	}
	switch(type) {
		case AMBULANCE:
			return INJURY;
			break;
		case FIREFIGHTER:
			return FIRE;
			break;
		case OFFICER:
			return CRIME;
			break;
	}
}

function canResponderHandle(responder, incident) {
	return getResponderIncident(responder) == incident;
	//return ((responder == AMBULANCE && incident == INJURY) || (responder == FIREFIGHTER && incident == FIRE) || (responder == OFFICER && incident == CRIME));
}

function createOrEditMarker(type, responder) {
	if (!(responder.id in markers)) {
		//create

		iconurl = "default";
		iconsize = [32, 32];
		iconanchor = [16, 16];
		shadowurl = "images/icon_selection_responder.png";
		shadowsize = [40, 40];
		shadowanchor = [20, 20];
		switch (type) {
			case AMBULANCE:
				iconurl = "images/icon_ambulance_big.png";
				iconsize = [48, 48];
				iconanchor = [24, 48];
				shadowsize = [53, 60];
				shadowanchor = [27, 54];
				break;
			case FIREFIGHTER:
				iconurl = "images/icon_fireguard_big.png";
				iconsize = [48, 48];
				iconanchor = [24, 48];
				shadowsize = [53, 60];
				shadowanchor = [27, 54];
				break;
			case OFFICER:
				iconurl = "images/icon_police_big.png";
				iconsize = [48, 48];
				iconanchor = [24, 48];
				shadowsize = [53, 60];
				shadowanchor = [27, 54];
				break;
			case INJURY:
				iconurl = "images/icon_red_cross.png";
				shadowurl = "images/icon_selection_red_cross.png";
				break;
			case FIRE:
				iconurl = "images/icon_fire.png";
				shadowurl = "images/icon_selection_fire.png";
				break;
			case CRIME:
				iconurl = "images/icon_burglary.png";
				shadowurl = "images/icon_selection_burglary.png";
				break;
		}
		var icon = L.icon({
			iconUrl: iconurl,
			iconSize: iconsize,
			iconAnchor: iconanchor,
			shadowUrl: shadowurl,
			shadowSize: shadowsize,
			shadowAnchor: shadowanchor
	 
		});
		//                var popup = L.popup();
		var marker = L.animatedMarker([[responder.pos.lat, responder.pos.lon]], { title:type, icon: icon, autoStart: false, clickable: true, distance:110, interval: 1000 });
		marker.id = responder.id;
		marker.type = type;
		marker.riseOnHover = true;
		//marker.addTo(map);
		map.addLayer(marker);
		marker._shadow.style.opacity = 0.0;

		marker.on('click', function (e) {
			map.closePopup();
			if (isResponder(this.type)) {
				//Is a responder
				selectedResponder = this;

				//highlight this marker
				unhighlightAll();
				selectedResponder._shadow.style.opacity = 1.0;
				bringResponderIncidentsToFront(selectedResponder.type);

				console.log('Marker: ' + marker.id + " selected");
			} else {
				//Is an incident
				if (selectedResponder != null) {
					selectedIncident = this;

					//highlight the incident
					selectedIncident._shadow.style.opacity = 1.0;
					//unhighlight incident
					setTimeout(unhighlightAll, 500);

					console.log('Responder: ' + marker.id + " selected");
					
					//check that this responder can handle this task
					var resIncType = getResponderIncident(selectedResponder.type);
					if (resIncType == selectedIncident.type) {
						route = getRoute(selectedResponder.id, selectedIncident.id);
					} else {
						var output = selectedResponder.type + " can only solve " + resIncType + "s.";
						var popup = L.popup({autoPan:false, closeButton:false})
							.setLatLng(selectedIncident.getLatLng())
							.setContent("<p>"+selectedResponder.type + " can only solve " + resIncType + "s.</p>")
							.openOn(map);
					}
					selectedResponder = null;
					selectedIncident = null;
				} else {
				}
			}
		});
		markers[responder.id] = marker;
	} else {
		//edit
		//if its a responder, we want to update its animation
		if(isResponder(type) && responder.path.length > 1) {
			//stop anim
			markers[responder.id].stop();

			//move to new position
			var newLatLng = new L.LatLng(responder.pos.lat, responder.pos.lon);
			markers[responder.id].setLatLng(newLatLng);
			
			//restart anim
			line = L.polyline(responder.path);
			line_latlngs = line.getLatLngs();
			markers[responder.id].setLine(line_latlngs);
			markers[responder.id].options.distance = responder.speed;
			markers[responder.id].update();
			markers[responder.id].start();
		}
	}
	
}

function unhighlightAll() {
	for (m in markers) {
		markers[m]._shadow.style.opacity = 0.0;
	}
}
function bringResponderIncidentsToFront(responderType) {
	for (m in markers) {
		if (canResponderHandle(responderType, markers[m].type)) {
			markers[m]._icon.style.zIndex = "1000";
		} else {
			markers[m]._icon.style.zIndex = "0";
		}
	}
}

function getRoute(responderId, incidentId) {
	$.ajax({
		url: "http://" + host + ":1234/" + simId + "/" + userId + "/assignToIncident",
		dataType: "jsonp",
		data: { "responderId": responderId, "incidentId": incidentId },
		success: function (response) {
			markers[responderId].stop();
			
			var color = "#000";
			switch(markers[responderId].type){
			case FIREFIGHTER:
				color="#FC0201";
				break;
			case AMBULANCE:
				color="#185900";
				break;
			case OFFICER:
				color="#1111D4";
				break;
			}

			var line = L.polyline(response.route.coordinates, {color:color});
			
			line_latlngs = line.getLatLngs();
			markers[responderId].setLine(line_latlngs);
			markers[responderId].options.distance = response.speed;
			markers[responderId].update();
			map.addLayer(line);
			$(line._container).fadeOut({
				duration:2000,
				complete:function() {
					map.removeLayer(line);
				}
			});
			//markers[responderId].start();
		},
		error: function (jqXHR, textStatus, errorThrown) { console.log(textStatus, errorThrown); }
	});
	
}
/*
	function initializeIncidents(stuff) {
		//initialize responders
		var responder = L.marker([51.5, -0.09], 'zIndexOffset', 0).on('click', responder_onClick);
		var incident = L.marker([51.7, -0.13], 'zIndexOffset', 0).on('click', incident_onClick);

		responder.addTo(map);
		incident.addTo(map);

		function responder_onClick(e) {
			selectedResponder = responder;
		}

		var popup = L.popup();

	}

		function incident_onClick(e) {
			if (selectedResponder != null) {
				selectedIncident = incident;
				popup.setLatLng(e.latlng).setContent("Let's get a route").openOn(map);
				route = getRoute(selectedResponder, selectedIncident);
				selectedResponder = null;
				selectedIncident = null;
			} else {
				popup.setLatLng(e.latlng).setContent("Select a responder first").openOn(map);
			}
		}
}*/

