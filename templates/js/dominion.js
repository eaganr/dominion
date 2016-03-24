var actions = {};
var treasures = {};
var estates = {};


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
    var handcards = document.querySelectorAll(".hand .card");
    for(var i=0;i<5 && i<hand.length;i++) {
      handcards[i].className = "card " + hand[i];
    }

    //setup actions
    var ac = Object.keys(actions);
    var actioncards = document.querySelectorAll(".actions .card");
    for(var i=0;i<10 && i<ac.length;i++) {
      actioncards[i].className = "card " + ac[i].replace(' ', '-');
    }
  


  },
  error: function(err) {
    console.log("error");
    console.log(err);
  }

});

