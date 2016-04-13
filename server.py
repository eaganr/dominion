#!/usr/bin/env python2.7

"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver

To run locally:

    python server.py

Go to http://localhost:8111 in your browser.

A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
import json
import random
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, send_from_directory

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@w4111a.eastus.cloudapp.azure.com/proj1part2
#
# For example, if you had username gravano and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://gravano:foobar@w4111a.eastus.cloudapp.azure.com/proj1part2"
#
DATABASEURI = "postgresql://rse2119:1437@w4111a.eastus.cloudapp.azure.com/proj1part2"

#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass

@app.route('/')
def index():
  context = {}
  return render_template("index.html", **context)

@app.route('/history', methods=['GET'])
def history():
  playerid = request.args.get("playerid")
  turnid = request.args.get("turnid")

  context = {}
  context["maxturn"] = g.conn.execute("SELECT MAX(turn_id) FROM decks").fetchone()[0]  

  #Get deck info
  cursor = g.conn.execute("SELECT * FROM decks WHERE player_name='Player "+playerid+"' and turn_id="+turnid)
  context["deck"] = []
  context["deck_size"] = 0
  for row in cursor:
    context["deck"].append(row)
    context["deck_size"] += row[3]

  #Get hand info
  cursor = g.conn.execute("SELECT * FROM hands WHERE player_name='Player "+playerid+"' and turn_id="+turnid)
  context["hand"] = []
  context["hand_size"] = 0
  for row in cursor:
    context["hand"].append(row)
    context["hand_size"] += row[3]

  #Get discard info
  cursor = g.conn.execute("SELECT * FROM discards WHERE player_name='Player "+playerid+"' and turn_id="+turnid)
  context["discards"] = []
  context["discards_size"] = 0
  for row in cursor:
    context["discards"].append(row)
    context["discards_size"] += row[3]

  #Get victory_points and cards info
  context["victory_cards"] = []
  #First from just victory_tokens
  num_points = g.conn.execute("SELECT num_victory_points FROM num_victory_points WHERE player_name = 'Player "+playerid+"' and turn_id="+turnid).fetchone()[0]
  context["num_victory_points"] = int(num_points)
  if num_points > 0:
    context["victory_cards"].append(["",unicode("Victory Tokens"),"",int(num_points)])

  #Then from victory cards
  cursor = g.conn.execute("SELECT * FROM all_players_cards WHERE card_name IN ('Province','Duchy','Estate') AND player_name = 'Player " +
                            playerid+"' AND turn_id="+turnid)
  card_point_map = { 'Province' : 6, 'Duchy' : 3, 'Estate' : 1 }
  for row in cursor:
    context["victory_cards"].append(row)
    context["num_victory_points"] += card_point_map[str(row[1])] * int(row[3])
  return render_template("history.html", **context)

def draw_one_card(player_name, turn_id):
  cursor = g.conn.execute("SELECT count(*) FROM decks WHERE player_name='" + player_name + "' AND turn_id ="+ str(turn_id))
  size = int(cursor.fetchone()[0])
  if size == 0: #If there are no cards in the deck
    #Flip discard into deck
    g.conn.execute("INSERT INTO decks SELECT * FROM discards WHERE player_name = '" + player_name+ "' AND turn_id ="+ str(turn_id))
    g.conn.execute("DELETE FROM discards WHERE player_name = '" + player_name +"' AND turn_id ="+ str(turn_id))

  cursor = g.conn.execute("SELECT card_name FROM (Select card_name,generate_series(1,num_cards) FROM decks WHERE player_name = '" + player_name+ "' AND turn_id =" + str(turn_id) +") AS f ORDER BY RANDOM() LIMIT 1")
  card_name = cursor.fetchone()[0]  

  g.conn.execute("UPDATE decks SET num_cards = num_cards - 1 WHERE card_name ='" + card_name +"' AND player_name = '" + player_name + "' AND turn_id ="+str(turn_id))
  g.conn.execute('DELETE FROM decks WHERE num_cards=0')
  try:
    g.conn.execute("INSERT INTO hands VALUES ('"+card_name+"',"+str(turn_id)+",'"+player_name+"',1)")
  except:
    g.conn.execute("UPDATE hands SET num_cards = num_cards + 1 WHERE card_name ='" + card_name +"' AND player_name = '" + player_name +"' AND turn_id ="+str(turn_id))
  return card_name

def drawcards(playerid, num):
  #check if hand already created
  themax = g.conn.execute("SELECT MAX(turn_id) from decks WHERE player_name='Player "+playerid+"'").fetchone()[0]
  try:
    handmax = g.conn.execute("SELECT MAX(turn_id) from hands WHERE player_name='Player "+playerid+"'").fetchone()[0]
    if handmax > themax:
      themax = handmax
  except:
    pass
  cards = []
  for i in range(0, num):
    cards.append(draw_one_card("Player "+playerid, themax))
  return cards

@app.route('/plusvictorypoints', methods=['POST'])
def plusvictorypoints():
  playerid = request.form['playerid']
  num = int( request.form['num'])
  turn_id = most_recent_turn_id()
  g.conn.execute("UPDATE TABLE num_victory_points SET num_victory_points = num_victory_points + 1 WHERE player_name='Player "+playerid+"' and turn_id=" +str(turn_id) )

@app.route('/actiondraw', methods=['POST'])
def actiondraw():
  playerid = request.form['playerid']
  num = int(request.form['num'])
  cards = drawcards(playerid, num)
  return Response(response=json.dumps(cards), status=200, mimetype="application/json")

@app.route('/endturn', methods=['POST'])
def endturn():
  playerid = request.form["playerid"]
  turn_id = g.conn.execute("SELECT MAX(turn_id) from hands WHERE player_name='Player "+playerid+"'").fetchone()[0]

  g.conn.execute('INSERT INTO decks SELECT card_name, turn_id+1, player_name, num_cards FROM decks WHERE turn_id = ' + str(turn_id))

  #Insert Hand and Buys in to discards
  g.conn.execute('INSERT INTO discards SELECT card_name, turn_id+1, player_name, num_cards FROM discards WHERE turn_id = ' + str(turn_id))
  cursor = g.conn.execute("SELECT * FROM hands where player_name='Player "+playerid+"' and turn_id=" +str(turn_id))
  for row in cursor:
    arr = row.values()
    arr[1] = arr[1]+1#increase turn_id
    val =  str(arr).replace("u'", "'").replace("[","(").replace("]",")")
    try:
      g.conn.execute("INSERT INTO discards VALUES " + val)
    except:
      num = arr[3]
      g.conn.execute("UPDATE discards SET num_cards = num_cards+"+str(num)+" WHERE player_name='Player "+str(playerid)+"' and card_name='"+arr[0]+"' and turn_id="+str(turn_id+1)) 

  #Snapshot end of turn status
  g.conn.execute("INSERT INTO cards_in_play SELECT card_name, num_cards, turn_id+1 FROM cards_in_play WHERE turn_id = " + str(turn_id))
  g.conn.execute("INSERT INTO num_victory_points SELECT player_name, turn_id+1, num_victory_points FROM num_victory_points WHERE turn_id = " + str(turn_id))

  #Next player's turn now unless game is over
  if int(g.conn.execute("SELECT COUNT(*) FROM cards_in_play where num_cards = 0 and turn_id = " + str(turn_id)).fetchone()[0] ) >= 3 or int(g.conn.execute("SELECT COUNT(*) FROM cards_in_play where card_name = 'Province' AND num_cards = 0 AND turn_id = " + str(turn_id)).fetchone()[0]) == 1:
    g.conn.execute("UPDATE players SET isyourturn = false" )
    print( "The game is over!" )
  else:
    g.conn.execute("UPDATE players SET isyourturn = false where player_name = 'Player " + str(playerid) + "'" )
    next_player_id = int(playerid) + 1
    if next_player_id == 5:
      next_player_id = 1
    g.conn.execute("UPDATE players SET isyourturn = true  where player_name = 'Player " + str(next_player_id) + "'" )

  ##TODO should update display of current game status when turn ends
  ### maybe by calling and displaying info in playersstatus()
  return Response(response=json.dumps(["Success"]), status=200, mimetype="application/json")

@app.route('/gamestate', methods=['POST'])
def gamestate():
  turn_id = g.conn.execute("SELECT MAX(turn_id) from cards_in_play").fetchone()[0]
  cursor = g.conn.execute("SELECT * FROM cards_in_play a JOIN all_cards b ON a.card_name = b.card_name and turn_id=" + str(turn_id))
  board = {}
  columns = cursor.keys()
  for row in cursor:
    data = {}
    for i in range(1, len(row)):
      data[columns[i]] = row[i]
    board[row[0]] = data
  cursor.close()

  result = {}
  result["board"] = board
  if request.form['playerid'] == "0":
    result["hand"] = []
  else:
    isyourturn = g.conn.execute("SELECT isyourturn FROM players where id="+request.form['playerid']).fetchone()[0]
    #Only draw hand if it is your turn    
    if isyourturn == True:
      result["hand"] = drawcards(request.form['playerid'], 5)
    else:
      result["hand"] = []
    result["isyourturn"] = isyourturn


  result["turnid"] = turn_id
  result["gamestatus"] = []
  for i in range(1,5):
    num_cards = g.conn.execute("Select Sum(num_cards) FROM all_players_cards WHERE player_name = 'Player " +
                                  str(i) + "' AND turn_id =" + str(turn_id) ).fetchone()[0]

    v_points = g.conn.execute("Select SUM(a.victory_point_value * b.num_cards) AS card_v_points" + 
                              " FROM all_players_cards b JOIN all_cards a ON a.card_name=b.card_name" + 
                              " WHERE player_name = 'Player " + str(i) + "' AND turn_id =" + str(turn_id) + 
                              " GROUP BY player_name;" ).fetchone()[0]
    v_points += g.conn.execute("SELECT num_victory_points FROM num_victory_points WHERE player_name = 'Player " + 
                                  str(i) + "' AND turn_id =" + str(turn_id) ).fetchone()[0]

    result["gamestatus"].append(["Player " + str(i), int(num_cards), int(v_points)])

  return Response(response=json.dumps(result), status=200, mimetype="application/json")

@app.route('/reset', methods=['POST'])
def reset():
  #delete everything
  cursor = g.conn.execute("DELETE FROM hands")
  cursor = g.conn.execute("DELETE FROM decks")
  cursor = g.conn.execute("DELETE FROM discards")
  cursor = g.conn.execute("DELETE FROM num_victory_points")
  g.conn.execute("DELETE FROM cards_in_play")
  #Set Player 1 to go first
  cursor = g.conn.execute("UPDATE players SET isyourturn = true WHERE player_name = 'Player 1'")
  cursor = g.conn.execute("UPDATE players SET isyourturn = false WHERE NOT player_name = 'Player 1'")

  #add everything back
  cursor = g.conn.execute("INSERT INTO decks VALUES ('Estate', 0, 'Player 1', 3)")
  cursor = g.conn.execute("INSERT INTO decks VALUES ('Estate', 0, 'Player 2', 3)")
  cursor = g.conn.execute("INSERT INTO decks VALUES ('Estate', 0, 'Player 3', 3)")
  cursor = g.conn.execute("INSERT INTO decks VALUES ('Estate', 0, 'Player 4', 3)")
  cursor = g.conn.execute("INSERT INTO decks VALUES ('Copper', 0, 'Player 1', 7)")
  cursor = g.conn.execute("INSERT INTO decks VALUES ('Copper', 0, 'Player 2', 7)")
  cursor = g.conn.execute("INSERT INTO decks VALUES ('Copper', 0, 'Player 3', 7)")
  cursor = g.conn.execute("INSERT INTO decks VALUES ('Copper', 0, 'Player 4', 7)")
  
  #Give everyone initially no victory points
  cursor = g.conn.execute("INSERT INTO num_victory_points VALUES ('Player 1', 0, 0)")
  cursor = g.conn.execute("INSERT INTO num_victory_points VALUES ('Player 2', 0, 0)")
  cursor = g.conn.execute("INSERT INTO num_victory_points VALUES ('Player 3', 0, 0)")
  cursor = g.conn.execute("INSERT INTO num_victory_points VALUES ('Player 4', 0, 0)")

  #Clear cards in play out  
  g.conn.execute("INSERT INTO cards_in_play SELECT card_name, 10 as num_cards, 0 as turn_id FROM all_cards WHERE card_name in ('Copper','Silver','Gold','Estate','Duchy','Province');" )

  g.conn.execute("INSERT INTO cards_in_play SELECT card_name, 10 AS num_cards, 0 AS turn_id FROM all_cards WHERE card_name NOT IN  ('Copper','Silver','Gold','Estate','Duchy','Province') ORDER BY RANDOM() LIMIT 10;" )

  return Response(response=json.dumps(["success"]), status=200, mimetype="application/json") 
 
@app.route('/playersstatus',methods=['POST'])
def playersstatus():
  turn_id = g.conn.execute("SELECT MAX(turn_id) from hands WHERE player_name='Player "+playerid+"'").fetchone()[0]
  ret = []
  player_ids = [1,2,3,4]
  for player_id in player_ids:
    player_info = [ "Player " + str(player_id)]
    #Get deck,discards,hand size
    player_info.append(g.conn.execute("SELECT COUNT(*) FROM decks where player_name = 'Player "+str(player_id)+"' AND turn_id = " + str(turn_id) ).fetchone()[0])
    player_info.append(g.conn.execute("SELECT COUNT(*) FROM discards where player_name = 'Player "+str(player_id)+"' AND turn_id = " + str(turn_id) ).fetchone()[0])


    #Get victory point value
    v_points = g.conn.execute("Select SUM(a.victory_point_value * b.num_cards) as card_v_points FROM all_players_cards b join all_cards a on a.card_name=b.card_name where player_name = 'Player " + str(player_id) + "' AND turn_id =" + str(turn_id) + " group by player_name;" ).fetchone()[0]
    v_points += g.conn.execute("SELECT num_victory_points from num_victory_points where player_name = 'Player " + str(player_id) + "' AND turn_id =" + str(turn_id) ).fetchone()[0]
    player_info.append(v_points)
    ret.append(player_info)
  #Ret is a matrix of the form
  # Player Name, Num in Deck, Num in discard, Num total victory points
  # Player 1, ##, ##, ##
  # Player 2, ##, ##, ## etc.
  return( ret )

@app.route('/historicalview', methods=['POST'])
def historicalview(player_id,turn_id):
  '''Given a player_name and a turn id will execute sql to return the status of that players deck,hand, and discard at that time.'''
  g.conn.execute( "SELECT card_name, num_cards FROM decks WHERE player_name = 'Player " + str(player_id) + "' AND turn_id =" + str(turn_id) )
  g.conn.execute( "SELECT card_name, num_cards FROM discards WHERE player_name = 'Player " + str(player_id) + "' AND turn_id =" + str(turn_id) )
  g.conn.execute( "SELECT card_name, num_cards FROM hands_hist WHERE player_name = 'Player " + str(player_id) + "' AND turn_id =" + str(turn_id) )

@app.route('/buy', methods=['POST'])
def buy():
  card = request.form['card']
  playerid = request.form['playerid']
  turn_id = g.conn.execute("SELECT MAX(turn_id) FROM hands WHERE player_name='Player "+str(playerid)+"'").fetchone()[0]  

  try:
    g.conn.execute("INSERT INTO discards VALUES ('"+card+"',"+str(turn_id)+", 'Player "+playerid+"', 1)")
  except:
    g.conn.execute("UPDATE discards SET num_cards=num_cards + 1 WHERE player_name='Player "+str(playerid)+"' and card_name='"+card+"' and turn_id="+str(turn_id))

  #decrement cards in play
  g.conn.execute("UPDATE cards_in_play SET num_cards = num_cards - 1 WHERE turn_id="+str(turn_id)+" and card_name='"+card+"'")
    
  return Response(response=json.dumps(["success"]), status=200, mimetype="application/json") 


@app.route('/js/<path:path>')
def js(path):
  return send_from_directory('templates/js', path)


@app.route('/img/<path:path>')
def img(path):
  return send_from_directory('templates/img', path)


@app.route('/css/<path:path>')
def css(path):
  return send_from_directory('templates/css', path)

#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#
@app.route('/another')
def another():
  return render_template("another.html")


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  g.conn.execute('INSERT INTO test VALUES (NULL, ?)', name)
  return redirect('/')


@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
