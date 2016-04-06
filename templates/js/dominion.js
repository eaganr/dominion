var playerid = 0;

var board = {};
var actions = {};
var actionkeys = [];
var treasures = {};
var estates = {};
var tekeys = ["Gold", "Silver", "Copper", "Province", "Duchy", "Estate"];
var hand = [];
var handvalues = {};


function drawcards(selector, cardnames, hand) {
    //setup actions
    var selected = document.querySelectorAll(selector);
    for(var i=0;i<10 && i<cardnames.length;i++) {
      selected[i].className = "card " + cardnames[i].replace(' ', '-');
      var card = board[cardnames[i]];
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
        text += "<div class=\"buy-btn\" price="+card["cost"]+" onclick=\"buycard('"+cardnames[i]+"')\">Buy: $"+card["cost"]+"</div>"; 
        text += "<div>"+card["num_cards"] + " remaining</div>";
      }
      if(hand) {
        if(cardnames[i] in actions) {
          text += "<div class=\"play-btn\" onclick=\"playaction(this, '"+cardnames[i]+"')\">Play</div>";
          count++;
        }
        else text += "<div>&nbsp;</div>";
      }

      selected[i].innerHTML = text;
    }

}

function newturn() {
  $.ajax({
    type : "POST",
    url : "/gamestate",
    data: {"playerid": playerid},
    success:function (data) {
      console.log(data);
      board = data["board"];
      for(var card in board) {
        if(board[card]["is_treasure"]) treasures[card] = board[card];
        else if(board[card]["victory_point_value"] > 0) estates[card] = board[card];
        else actions[card] = board[card];
      }
      hand = data["hand"];
      hand[2] = "Monument";
      hand[0] = "Village";
      hand[1] = "Festival";
    
      //setup hand
      drawcards(".hand .card", hand, true);
      addhand();
   
      //actions
      actionkeys = Object.keys(actions).sort(function(a,b) {
        return actions[a]["cost"] > actions[b]["cost"];
      });
      drawcards(".actions .card", actionkeys);

      //treasures and estates
      drawcards(".money-estates .card", tekeys);

    },
    error: function(err) {
      console.log("error");
      console.log(err);
    }
  });
}
//display board cards
newturn();

$(".player-select").change(function() {
  var val = parseInt($(this).val());
  playerid = val;
  //show reset button for admin
  if(val !== 0) $(".reset-btn").hide();
  else $(".reset-btn").show();
  newturn();
});

function addhand() {
  handvalues["coin"] = 0;
  handvalues["actions"] = 1;
  handvalues["buys"] = 1;
  for(var i=0;i<hand.length;i++) {
    if(board[hand[i]]["is_treasure"]) {
      handvalues["coin"] += board[hand[i]]["coin_value"];
    }
  }
  //display, ontimeout to allow buy btns to draw first, then delete
  setTimeout(function() {drawhandvalues();}, 500);
}

function drawhandvalues() {
  var txt = "Actions: " + handvalues["actions"] + ", Buys: " + handvalues["buys"] + ", Coin: " + handvalues["coin"];
  document.getElementsByClassName("hand-values")[0].innerHTML = txt;

  //check if can buy
  var btns = Array.prototype.slice.call(document.getElementsByClassName("buy-btn"));
  for(var i=0;i<btns.length;i++) {
    var btn = btns[i];
    if(handvalues["buys"] === 0 || parseInt(btn.getAttribute("price")) > handvalues["coin"]) {
      btn.innerHTML = btn.innerHTML.replace("Buy:", "Costs");
      btn.onclick = "";
      if(btn.className.indexOf("buy-disabled") === -1) btn.className += " buy-disabled";
    }
    else {
      btn.innerHTML = btn.innerHTML.replace("Costs", "Buy:");
      btn.onclick = function() {
        var card = this.parentNode.className.split(" ")[1];
        buycard(card);
      };
      btn.className = btn.className.replace(" buy-disabled", "");
    }
  }

}

function playaction(btn, card) {
  if(handvalues["actions"] > 0) {
    //VP need to be added
    //more cards drawn
    handvalues["coin"] += board[card]["coin_value"];
    handvalues["actions"] += board[card]["plus_action"] - 1;
    handvalues["buys"] += board[card]["plus_buy"];
    
    btn.innerHTML = "Played";
    btn.className = "";
    btn.onclick = "";

    drawhandvalues();
    if(handvalues["actions"] == 0) {
      var btns;
      while((btns = document.getElementsByClassName("play-btn")).length > 0) {
        btns[0].innerHTML = "&nbsp;";
        btns[0].onclick= "";
        btns[0].className = "";
      }
    }
  }
  else {
    alert("No Actions!");
  }
}

function buycard(card) {
  card = card.replace("-", " ");
  $.ajax({
    type : "POST",
    url : "/buy",
    data : {"playerid": playerid, "card": card},
    success:function() {
      console.log("Bought " + card);
    }
  });
  handvalues["buys"] = handvalues["buys"] - 1;
  handvalues["coin"] = handvalues["coin"] - board[card]["cost"];
  drawhandvalues();
}


function reset() {
  $.ajax({
    type : "POST",
    url : "/reset",
    success:function() {
      location.reload();
    }
  });
}

