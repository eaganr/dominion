var playerid = 0;

var actions = {};
var actionkeys = [];
var treasures = {};
var estates = {};
var tekeys = ["Gold", "Silver", "Copper", "Province", "Duchy", "Estate"];


function drawcards(selector, cardnames, cards, hand) {
    //setup actions
    var selected = document.querySelectorAll(selector);
    for(var i=0;i<10 && i<cardnames.length;i++) {
      selected[i].className = "card " + cardnames[i].replace(' ', '-');
      var card = cards[cardnames[i]];
      var text = "<div class=\"card-name\">" + card["card_name"] + "</div>";
      var count = 0;
      if(card["plus_card"] > 0) { text += "<div>+" + card["plus_card"] + " Cards</div>"; count++ }
      if(card["plus_action"] > 0) { text += "<div>+" + card["plus_action"] + " Actions</div>"; count ++ }
      if(card["plus_buy"] > 0) { text += "<div>+" + card["plus_buy"] + " Buys</div>"; count ++ }
      if(card["coin_value"] > 0) { text += "<div>+$" + card["coin_value"] + "</div>"; count ++ }
      if(card["plus_victory_point"] > 0) { text += "<div>+" + card["plus_victory_point"] + " VP</div>"; count++ }
      if(card["victory_point_value"] > 0) { text += "<div>Worth " + card["victory_point_value"] + " VP</div>"; count++ }

      while(count < 4) {
        text += "<div>&nbsp;</div>";
        count++;
      }
      if(!hand) {
        text += "<div>Costs $"+card["cost"]+"</div>"; 
        text += "<div>"+card["num_cards"] + " remaining</div>";
      }

      selected[i].innerHTML = text;
    }

}

$.ajax({
  type : "POST",
  url : "/gamestate",
  data: {},
  success:function (data) {
    console.log(data);
    for(var card in data) {
      if(data[card]["is_treasure"]) treasures[card] = data[card];
      else if(data[card]["victory_point_value"] > 0) estates[card] = data[card];
      else actions[card] = data[card];
    }

    var hand = ["Estate", "Estate", "Copper", "Moat", "Copper"];

    //setup hand
    drawcards(".hand .card", hand, data, true);
 
    //actions
    actionkeys = Object.keys(actions).sort(function(a,b) {
      return actions[a]["cost"] > actions[b]["cost"];
    });
    drawcards(".actions .card", actionkeys, actions);

    //treasures and estates
    drawcards(".money-estates .card", tekeys, $.extend({}, treasures, estates));

  },
  error: function(err) {
    console.log("error");
    console.log(err);
  }

});

$(".player-select").change(function() {
  var val = parseInt($(this).val());
  playerid = val;
  
});

