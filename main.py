from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config['SECRET_KEY'] = "grgsrkftw"
socketio = SocketIO(app)

rooms = {}

def generate_unique_code(length):
    while True:
        code = ""
        for _ in range (length):
            code += random.choice(ascii_uppercase)

        if code not in rooms:
            break
    return code

@app.route("/", methods=["POST", 'GET'])    
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False) # False boolean value by default, Inactive
        create = request.form.get("create", False)

        if not name:
            return render_template("home.html", error="Please enter a name", code=code, name=name)
        if join != False and not code:
            return render_template("home.html", error="Please enter a code", code=code, name=name)
        
        room=code
        if create != False:
            room = generate_unique_code(4) # generate a 4-lettter uppercase word
            rooms[room]= {"members": 0, "messages": []}
        elif code not in rooms:
            return render_template("home.html", error="Room does not exist", code=code, room=room)
        
        session["room"] = room
        session["name"] = name

        return redirect(url_for("room"))
    
    return render_template("home.html")

@app.route("/room") # directing url route to room.html in /templates/room.html
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))
    
    return render_template("room.html", code=room, messages=rooms[room]["messages"])

@socketio.on("message")
def message(data):
    room = session.get("room")

    if room not in rooms:
        return
    content = {
        "name": session.get("name"),
        "message": data["data"]
        }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(auth)
        return
    
    join_room(room)
    send({"name": name, "message": "has entered the room"}, to=room) # {} inside these braces we are accessing the message been sent to user
    rooms[room]["members"] += 1
    print(F"{name} joined room {room}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if rooms in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]

    send({"name": name, "message": "has left the room"}, to=room)    
    print(f"{name} left {room}") 


if __name__ == "__main__":
    socketio.run(app, debug=True)