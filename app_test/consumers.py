from json import loads, dumps

from channels.generic.websocket import WebsocketConsumer
from channels.generic.websocket import JsonWebsocketConsumer
from rest_framework_simplejwt.tokens import AccessToken
from asgiref.sync import async_to_sync

from django.contrib.auth import get_user_model
from competition.settings import DEBUG

User = get_user_model()

#return username from databse based on the passed user_id
def get_username(user_id):
    try:
        user = User.objects.get(id=user_id)
        return user.username
    
    except:
        return None

def get_user_data(user_id):
    try:
        user = User.objects.get(id=user_id)
        return {
            "first_name":user.first_name,
            "last_name":user.last_name,
            "username":user.username,
            "is_online":True,
            "active_test_score":100,
        }
    
    except:
        return None

"""
active_rooms = {
    room_id: {user_id: connection_count}
}
"""
active_rooms = {}

class CompetitionConsumer(JsonWebsocketConsumer):
    #utility function for removing self connection from active_users
    def remove_from_active(self) -> None:
        if self.scope["room"]:
            room = active_rooms[self.scope["room"]]
            user_id = self.scope["user_id"]
            room[user_id]-=1
            if (room[user_id] == 0):
                del room[user_id]
            
            async_to_sync(self.channel_layer.group_send)(
                self.scope["room"],
                {
                    'type':'active_users',
                }
            )

    def connect(self):
        self.scope["user_id"] = None #jwt token
        self.scope["room"] = None #Test model id
        self.accept()
    
    def disconnect(self, close_code):
        if self.scope["user_id"] != None:
            self.remove_from_active()

    def receive_json(self, json_data):
        """
        All messages must have two arguments
            -> type:str
            -> message:any
        """
        message_type:str = ""
        message = None
        try:
            message_type = json_data["type"]
            message = json_data["message"]
        except:
            if DEBUG: print("incorrect message:", json_data)

        #trying to authenticate -> need a jwt token
        if message_type == "auth":
            token = None #jwt token
            user_id = None
            try:
                token = AccessToken(message)
                user_id = token["user_id"]
            except:
                #token is invalid
                self.send_json({
                    "type":"error",
                    "message":"auth"
                })
                return

            if self.scope["user_id"] == user_id:
                return

            #user has changed profile
            self.scope["user_id"] = user_id
            if self.scope["room"] != None:
                room = self.scope["room"]
                self.remove_from_active()
                if user_id in active_rooms[room]:
                    active_rooms[room][user_id] += 1
                else:
                    active_rooms[room][user_id] = 1
                
                async_to_sync(self.channel_layer.group_send)(
                    self.scope["room"],
                    {
                        'type':'active_users',
                    }
                )
        
        elif message_type == "goto_room":
            if not self.scope["user_id"]:
                return

            room_id:str = None
            try:
                room_id = str(int(message))
            except:
                self.send_json({
                    "type":"error",
                    "message":"invalid_room"
                })
                return

            user_id = self.scope["user_id"]
            self.remove_from_active()

            if not room_id in active_rooms:
                active_rooms[room_id] = {}

            if user_id in active_rooms[room_id]:
                active_rooms[room_id][user_id] += 1
            else:
                active_rooms[room_id][user_id] = 1

            self.scope["room"] = room_id
            #add user to the exam room
            async_to_sync(self.channel_layer.group_add)(
                room_id,
                self.channel_name
            )
            async_to_sync(self.channel_layer.group_send)(
                room_id,
                {
                    'type':'active_users',
                }
            )
        
        #client wants information
        elif message_type == "query":
            #client wants to know the authed users
            if message == "get_active_users":
                if self.scope["user_id"]:
                    if not self.scope["room"]:
                        self.send_json({
                            "type":"error",
                            "message":"not_in_room"
                        })
                        return
                    room = self.scope["room"]
                    self.send_json({
                        "type":"active_users",
                        "message": [get_user_data(user_id) for user_id in active_rooms[room].keys()]
                    })
                else:
                    #client has not been authenticated
                    self.send_json({
                        "type":"error",
                        "message":"auth"
                    })
            
            #client wants to know if they are connected
            elif message == "auth":
                if self.scope["user_id"]:
                    self.send_json({
                        "type":"auth",
                        "message":True
                    })
                
                else:
                    self.send_json({
                        "type":"auth",
                        "message":False
                    })

            #client message is not recognized
            else:
                self.send_json({
                    "type":"error",
                    "message":"La Li Lu Le Lo"
                })

        #client message is not recognized
        else:
            if DEBUG: print("undefined message -", json_data)
            self.send_json({
                "type":"error",
                "message":"La Li Lu Le Lo"
            })

    def active_users(self, event):
        if not self.scope["room"]:
            return
        
        room = self.scope["room"]
        user_id = self.scope["user_id"]
        self.send_json({
            "type":"active_users",
            "message":[get_user_data(user_id) for user_id in active_rooms[room].keys()]
        })
    
    def question_started(self, event):
        message = event["message"]
        self.send_json({
            "type":"question_started",
            "message":message
        })