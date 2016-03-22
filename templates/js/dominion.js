var hand = ["Estate", "Estate", "Copper", "Estate", "Copper"];
var actions = {"Market":10, "Village":10, "Woodcutter":10, "Festival":10, "Moat":10};

//setup hand
for(var i=0;i<5 && i<hand.length;i++) {
	$(".hand .card")[i].className = "card " + hand[i];
}

//setup actions
var ac = Object.keys(actions);
for(var i=0;i<10 && i<ac.length;i++) {
	$(".actions .card")[i].className = "card " + ac[i];
}
