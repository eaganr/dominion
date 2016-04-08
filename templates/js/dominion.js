var playerid = 0;
var turnid = 0;

var board = {};
var actions = {};
var actionkeys = [];
var treasures = {};
var estates = {};
var tekeys = ["Gold", "Silver", "Copper", "Province", "Duchy", "Estate"];
var hand = [];
var handvalues = {};
var handindex = 0;


function drawcards(selector, cardnames, hand) {
    //setup actions
    var selected = document.querySelectorAll(selector);
    for(var i=0;i<10 && i<cardnames.length;i++) {
      if(cardnames[i] === "") {
        selected[i].className = "card";
        var text = "<div class=\"card-name\">&nbsp;</div><div>&nbsp;</div><div>&nbsp;</div><div>&nbsp;</div><div>&nbsp;</div><div>&nbsp;</div>";
        selected[i].innerHTML = text;
        continue;
      }
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
      if(hand && handvalues["actions"] > 0) {
        if(cardnames[i] in actions) {
          text += "<div class=\"play-btn\" onclick=\"playaction(this, "+i+")\">Play</div>";
          count++;
        }
        else text += "<div>&nbsp;</div>";
      }

      selected[i].innerHTML = text;
    }

}

function getgamestate() {
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
      hand[4] = "Moat";
      hand[0] = "Moat";
    
      //setup hand
      addhand();
      drawcards(".hand .card", hand, true);
   
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
getgamestate();

$(".player-select").change(function() {
  var val = parseInt($(this).val());
  playerid = val;
  //show reset button for admin
  if(val !== 0) $(".reset-btn").hide();
  else $(".reset-btn").show();
  getgamestate();
});

function addhand(newcards) {
  if(!newcards) {
    handvalues["coin"] = 0;
    handvalues["actions"] = 1;
    handvalues["buys"] = 1;
    for(var i=0;i<hand.length;i++) {
      if(board[hand[i]]["is_treasure"]) {
        handvalues["coin"] += board[hand[i]]["coin_value"];
      }
    }
  }
  else {
    for(var i=0;i<newcards.length;i++) {
      if(board[newcards[i]]["is_treasure"]) {
        handvalues["coin"] += board[newcards[i]]["coin_value"];
      }
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

function playaction(btn, cardid) {
  var card = hand[cardid];
  if(handvalues["actions"] > 0) {
    //VP need to be added
    //more cards drawn
    if(board[card]["plus_card"] > 0) {
      $.ajax({
        type : "POST",
        url : "/actiondraw",
        data : {"playerid": playerid, "num": board[card]["plus_card"]},
        success:function(data) {
          console.log("New cards: " + data);
          hand.splice(cardid, 1); 
          while(hand.indexOf("") > -1) {
            hand.splice(hand.indexOf(""), 1);
          }
          hand = hand.concat(data);
          handindex = hand.length - 5;
          drawcards(".hand .card", hand.slice(handindex), true);
          addhand(data);
        }
      });
    }

    handvalues["coin"] += board[card]["coin_value"];
    handvalues["actions"] += board[card]["plus_action"] - 1;
    handvalues["buys"] += board[card]["plus_buy"];
    
    drawhandvalues();
    if(handvalues["actions"] == 0) {
      var btns;
      while((btns = document.getElementsByClassName("play-btn")).length > 0) {
        btns[0].innerHTML = "&nbsp;";
        btns[0].onclick= "";
        btns[0].className = "";
      }
    }
    if(board[card]["plus_card"] <= 0) {
      hand.splice(cardid, 1); 
      if(hand.length < 5) hand.push("");
      console.log(hand);
      drawcards(".hand .card", hand.slice(handindex), true);
    }
  }
  else {
    alert("No Actions!");
  }
}

function changehandindex(n) {
  handindex += n;
  if(handindex < 0) handindex = 0;
  if(handindex > hand.length - 5) handindex = hand.length - 5;
  drawcards(".hand .card", hand.slice(handindex), true);
}

function buycard(card) {
  var remaining = parseInt($(".board").find("."+card).find("div")[6].innerHTML.split(" ")[0])-1;
  $(".board").find("."+card).find("div")[6].innerHTML = remaining + " remaining";
  $(".action ."+card).
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

function endturn() {
  $.ajax({
    type: "POST",
    url: "/endturn",
    data: {"playerid":playerid},
    success:function() {
      console.log("Turn ended");
    }
   });
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

