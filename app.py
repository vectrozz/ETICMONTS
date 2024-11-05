from flask import Flask, render_template, url_for, redirect, request, jsonify
import psycopg2
from datetime import datetime, timezone
#from dotenv import load_dotenv    #dotenv read file .env and set variable as environment variable
#from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask import session, abort
from flask import flash


#from flask_wtf import FlaskForm
#from wtforms import StringField, PasswordField, SubmitField
#from wtforms.validators import InputRequired, Length, ValidationError


CREATE_PLAYERS_TABLE = ('''CREATE TABLE IF NOT EXISTS players4 (id SERIAL PRIMARY KEY, name VARCHAR (20), userpass VARCHAR (100),  created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, last_login_date TIMESTAMP)''')
DELETE_PLAYERS_TABLE = ('''DROP TABLE IF EXISTS players4''')
INSERT_PLAYER = ('''INSERT INTO players4 (name, userpass) VALUES (%s, %s) RETURNING id, created_date;''')
PLAYERS_LIST = ('''SELECT * FROM players4''')
SEARCH_PLAYER = ('''SELECT id FROM players4 WHERE name LIKE (%s)''')
UPDATE_LOGIN_DATE =('''UPDATE players4 SET last_login_date = %s WHERE id = %s''')
SEARCH_LAST_LOGIN = ('''SELECT last_login_date FROM players4 WHERE name LIKE (%s)''')


app = Flask(__name__)

def db_conn():
    return psycopg2.connect(database="bobdb", host="127.0.0.1", user="bob", password="bobpass", port="5432")
db = db_conn()

bcrypt = Bcrypt(app)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
#app.config['SECRET_KEY'] = 'thisisasecretkey'


app.secret_key = 'thisisasecretkey'  # Use a strong secret key in production

#login_manager = LoginManager()
#login_manager.init_app(app)
#login_manager.login_view = 'login'


#login_manager.user_loader
#def load_user(id):
#    curr = db_conn().cursor()
#    curr.execute(SEARCH_PLAYER,(id,))
#    result = curr.fetchone()
#    user_id = result[0]
#    curr.close()
#    return int(user_id)


@app.get('/id_by_name')
def id_by_name():
    name = request.get_json()["name"]
    curr = db_conn().cursor()
    curr.execute(SEARCH_PLAYER, (name,))
    result = curr.fetchone()
    curr.close()
    db_conn().close()
    if result:
        user_id = result[0]
        #return jsonify({ "id" : f"{user_id}" })  #show id between " " as string ? 
        return user_id #jsonify({"id": user_id})  #show id as integer ? or as string without " " ?
    else:
        return jsonify({"not available":"try other one"})



@app.route('/')
def home():
    return render_template('index.html')


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html') #jsonify({"error": f"player {name} does not exist"})
    
    if request.method == 'POST':   
        name = request.get_json()["name"]
        userpass = request.get_json()["userpass"]
        #This one below for the IF
        player_list = get_player_list()

        #Those only for session to store correct data type ---> to solve should work without this...
        conn = db_conn()
        curr = conn.cursor()
        curr.execute(SEARCH_PLAYER, (name,))
        result = curr.fetchone()
        curr.execute(SEARCH_LAST_LOGIN, (name,))
        result_last_login = curr.fetchone()
        curr.close()
        conn.close()
        #End of "those only for balbalbalbal "


        for row in player_list:
            if row[1] == name:
                if row[2] == userpass:
                    user_id = id_by_name()
                    #login_user(user_id, remember=False, duration=None, force=False, fresh=True)current_user.is_authenticated:
                    #flask_login.current_user.name
                    session['user_id'] = result[0]
                    session['username'] = name
                    session['last_login_date'] = result_last_login[0]
                    if result_last_login[0] == None:
                        session['last_login_date'] = "First login !"
                    
                    
                    # Mettre à jour le champ `last_login`
                    conn = db_conn()
                    curr = conn.cursor()
                    curr.execute(UPDATE_LOGIN_DATE, (datetime.now(), user_id))
                    conn.commit()
                    curr.close()
                    conn.close()
                    session['username'] = name
                    return jsonify({"success": f"player {name} login successfull" }) #redirect(url_for('dashboard')) #jsonify({"success": f"player {name} login successfull" })
                else:
                    return jsonify({"warn": "wrong password"})
        return jsonify({"error": f"player {name} does not exist"})



@app.route('/dashboard', methods=['GET','POST' ])
#@login_required
def dashboard():
    if 'username' in session:
        username = session['username']
        id = session['user_id']  # Récupère le nom de l'utilisateur de la session
        created_date = session['created_date']
        last_login_date = session['last_login_date']
        return render_template('dashboard.html', username=username, user_id=id, created_date=created_date, last_login_date=last_login_date)
    else:
        return redirect(url_for('login'))


@app.route('/logout', methods=['GET', 'POST'])
#@login_required
def logout():
    session.pop('user_id', None)  # Remove the user_id from session
    return redirect(url_for('login'))


@ app.route('/register', methods=['GET','POST'])
def register():

    if request.method == 'GET':
        # Serve the registration form page
        return render_template('register.html')  
    
    if request.method == 'POST':
        #data = request.get_json()
        #if not data:
        #    return jsonify({"error": "Invalid data"}), 400
        #else :  
        name = request.get_json()["name"]
        userpass = request.get_json()["userpass"]
        userpass1 = request.get_json()["userpass1"]
        conn=db_conn()
        curr = conn.cursor()
        curr.execute(CREATE_PLAYERS_TABLE)
        player_used = checkifexist()

        if player_used == "no":
            if ((userpass == userpass1) & (userpass != "")):
                try:
                    #curr.execute(CREATE_PLAYERS_TABLE)
                    curr.execute(INSERT_PLAYER,(name,userpass))
                    player_id, created_date = curr.fetchone()
                    conn.commit()
                    session['user_id'] = player_id
                    session['username'] = name
                    session['created_date'] = created_date 
                    
                    #flash(f"Player {name} with id  was created","Success")
                    
                    # Redirige directement vers la page de connexion
                    #return redirect(url_for('login'))
                    return jsonify({"success": f"Player {name} created at {created_date}", "id": player_id}), 200
        
                except Exception as e:
                    conn.rollback()  # Rollback in case of error
                    return jsonify({"error": str(e)}), 500
        
                finally:
                    curr.close()
                    conn.close()
            else:
                return jsonify({"warn": "Passwords mismatch"})
        
        else:
            curr.close()
            conn.close()
            return jsonify({"info": f"Player {name} already exist, please choose another one"}), 202



@ app.get("/playerslist")
def get_player_list():
    #conn = db_conn()
    curr = db_conn().cursor()
    curr.execute(PLAYERS_LIST)
    playerlist = curr.fetchall()
    db_conn().close()

    if playerlist:
        return playerlist
    else:
        None

@ app.get("/totalplayer")
def get_total_player():
    #conn = db_conn()
    curr = db_conn().cursor()
    curr.execute(PLAYERS_LIST)
    playerlist = curr.fetchall()
    totalplayers = len(playerlist)
    db_conn().close()

    if playerlist:
        return ("total players are : " + str(totalplayers))
    else:
        None

@app.post("/check")
def checkifexist():
    name = request.get_json()["name"]
    player_list = get_player_list()
    #conn = db_conn()
    #curr = conn.cursor()
    #curr.execute(SEARCH_PLAYER)
    exist = "no"
    for row in player_list:
        if row[1] == name:
            exist = "yes"
            break # sortie de boucle si on trouve le joueur
    
    if exist == "yes":
        return jsonify({f"player {name} exists":exist}), name
    else: 
        return exist


if __name__ == "__main__":
    app.run(debug=True)