from flask import Flask,request
from flask_socketio import SocketIO, emit,join_room,leave_room
from flask_cors import CORS


app=Flask(__name__)
CORS(app,resources={r"/*":{"origins":"*"}})
socketio=SocketIO(app,cors_allowed_origins="*")

rooms=[]
curr_player_ind=0


def check_id_in_users(id,index):
    for user in rooms[index]["users"]:
        if user["socketid"]==id:
            return user
    return None  

def check_room_exists(room):
    for i, item in enumerate(rooms):
        if str(item["roomName"]) == str(room):
            return i
    return -1  



@app.route('/')
def index():
    return "Flask backend with SOcketIO"
@app.route('/allplayers')
def get_all_players():
    ind=check_room_exists(request.args.get('roomName'))
    print(ind)
    print(rooms)
    if ind!=-1:
        return rooms[ind]["users"]
    else:
        return []
@socketio.on('join')
def handle_join_room(username,room):
    join_room(room=room)
    res=check_room_exists(room)
    target_socket_id=request.sid
    target_namespace=request.namespace
    print("socket id is : ",target_socket_id, target_namespace)
    
    emit('getmysocketDetail',target_socket_id,to=target_socket_id)
    if res==-1:
        temp={}
        temp["roomName"] = room
        temp["users"] = []
        temp["currPlayerInd"] = 0
        temp_user = {}
        temp_user["name"] = username
        temp_user["socketid"] = target_socket_id
        temp_user["namespace"]=target_namespace
        temp["users"].append(temp_user)
        rooms.append(temp)
    else:
        temp = rooms[res]
        if check_id_in_users(target_socket_id, res)!=True :
            temp_user = {}
            temp_user["name"] = username
            temp_user["socketid"] = target_socket_id
            temp["users"].append(temp_user)
            rooms[res] = temp
            emit(
        "join",
        rooms[res]["users"][len(rooms[res]["users"]) - 1]["name"]
       )
    print(rooms)
    emit("new_player",to=target_socket_id)
@socketio.on("start_game")
def start_game(room):
    emit("started",to=room)
    room_ind=check_room_exists(room)
    rooms[room_ind]["currPlayerInd"] = 0
    curr_player_ind = rooms[room_ind]["currPlayerInd"]
    curr_player = rooms[room_ind]["users"][curr_player_ind]["socketid"]
    print("Current turn is ",curr_player)
    print(request.sid)
    if curr_player==request.sid:
        emit("play",to=request.sid)
    else:
        emit("play",to=curr_player)

@socketio.on("restart")
def restart(room):
    emit("restartclicked",to=room)

@socketio.on("played")
def afterPlayed(num,room,socketid):
    room_ind=check_room_exists(room)
    curr_player_ind = rooms[room_ind]["currPlayerInd"]
    emit("playednum", { "num": num, "socketid": request.sid},broadcast=True,include_self=True)
    if curr_player_ind == len(rooms[room_ind]["users"]) - 1 :
      curr_player_ind = 0
      rooms[room_ind]["currPlayerInd"] = 0
    else:
      rooms[room_ind]["currPlayerInd"] = rooms[room_ind]["currPlayerInd"] + 1
      curr_player_ind = rooms[room_ind]["currPlayerInd"]
    
    
    emit("play",to=rooms[room_ind]["users"][curr_player_ind]["socketid"])

@socketio.on("won")
def won(winner,room):
    emit("lost",winner,broadcast=True,include_self=False,to=room)
@socketio.on('disconnect')
def on_disconnect():
    for k in range(len(rooms)):
      for j in range( len( rooms[k]["users"])):
        if (rooms[k]["users"][j]["socketid"] == request.sid) :
          tmp = rooms[k]["users"]
          print(rooms)
          new_user_arr = tmp[0: j]+tmp[j + 1:len(tmp)]
          rooms[k]["users"] = new_user_arr[:]
    
      





if __name__ == '__main__':
    socketio.run(app, debug=True,port=3001)