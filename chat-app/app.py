from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, send
import random
from string import ascii_uppercase

# def get_local_ip():
# 	try:
# 		with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
# 			s.connect(("8.8.8.8", 80))
# 			return s.getsockname()[0]
# 	except Exception as e:
# 		return "127.0.0.1"

app = Flask(__name__)
app.config["SECRET_KEY"] = "hhhh"
io = SocketIO(app)

rooms = {}

def generate_code(Length:int) -> str:
	while True:
		code = ""
		for _ in range(Length):
			code += random.choice(ascii_uppercase)
		if code not in rooms:
			break
	return code

@app.route("/",methods=["POST","GET"])
def lobby() -> str:
	session.clear()
	if request.method == "POST":
		name:str = request.form.get("name")
		code:str = request.form.get("code")
		join:str = request.form.get("join", False)
		create:str = request.form.get("create", False)

		if not name:
			return render_template("lobby.html", error="Please enter a name.",code=code, name=name)

		if join != False and not code:
			return render_template("lobby.html", error="Please enter a room code.",code=code, name=name)

		room:str = code
		if create != False:
			room = generate_code(4)
			rooms[room] = {"members": 0, "messages":[]}
		elif code not in rooms:
			return render_template("lobby.html",error="Room does not exist.")

		session["room"] = room
		session["name"] = name
		return redirect(url_for("room"))

	return render_template("lobby.html")

@app.route("/room")
def room():
	room = session.get("room")
	if room is None or session.get("name") is None or room not in rooms:
		return redirect(url_for("lobby"))

	return render_template("chat.html",code=room,messages=rooms[room]["messages"])

@io.on("connect")
def connect(auth) -> None:
	room = session.get("room")
	name = session.get("name")
	if not room or not name:
		return
	if room not in rooms:
		leave_room(room)
		return
	join_room(room)
	send({"name": name, "message": "has entered the room!"},to=room)
	rooms[room]["members"] += 1

	#Just for Debug
	#print(f"{name} joined room {room}")

@io.on("disconnect")
def disconnect() -> None:
	room = session.get("room")
	name = session.get("name")
	leave_room(room)

	if room in rooms:
		rooms[room]["members"] -= 1
		if rooms[room]["members"] <= 0:
			del rooms[room]

	send({"name":name, "message": "has left the room"},to=room)

	#Just for Debug
	#print(f"{name} has left the room {room}")

@io.on("message")
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
	#Just for Debug
	#print(f"{session.get('name')} said: {data['data']}")

if __name__ == "__main__":
	io.run(app, debug=False)
