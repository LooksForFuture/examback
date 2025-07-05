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
active_users dictionary:
    key -> user_id
    value -> websocket channels
"""
active_users = {}

class ChatConsumer(JsonWebsocketConsumer):
    #utility function for removing self connection from active_users
    def remove_from_active(self) -> bool:
        if self.scope["user_id"]:
            user_id = self.scope["user_id"]
            active_user = active_users[user_id]
            for i in range(len(active_user)):
                if active_user[i] == self.channel_name:
                    del active_users[user_id][i]
                    if len(active_users[user_id]) == 0:
                        del active_users[user_id]
                        #inform everyone about the exit of user
                        async_to_sync(self.channel_layer.group_send)(
                            "authed",
                            {
                                'type':'active_users',
                                'message':[get_user_data(user_id) for user_id in active_users.keys()]
                            }
                        )
                    return True
        
        return False

    def connect(self):
        self.scope["user_id"] = None #jwt token
        self.accept()
    
    def disconnect(self, close_code):
        if self.scope["user_id"] != None:
            #remove from authed group
            async_to_sync(self.channel_layer.group_discard)(
                "authed",
                self.channel_name
            )
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

            if self.scope["user_id"]:
                if self.scope["user_id"] == user_id:
                    return

                #user has changed profile
                self.remove_from_active()
                self.scope["user_id"] = user_id

            else:
                #channel had not been authenticated
                self.scope["user_id"] = user_id
            
            #add user to the authed users
            async_to_sync(self.channel_layer.group_add)(
                "authed",
                self.channel_name
            )

            #check if this user is authed by another channel
            found = False
            for user, channels in active_users.items():
                if user == user_id:
                    found = True
                    active_users[user_id].append(self.channel_name) #associate channel with user
                    self.send_json({
                        "type":"active_users",
                        "message":[get_user_data(user_id) for user_id in active_users.keys()]
                    })
                    return

            if not found:
                active_users[user_id] = []
                active_users[user_id].append(self.channel_name) #add user to the active ones
                #inform everyone about the enterance of new user
                async_to_sync(self.channel_layer.group_send)(
                    "authed",
                    {
                        'type':'active_users',
                        'message':[get_user_data(user_id) for user_id in active_users.keys()]
                    }
                )
        
        #client wants information
        elif message_type == "query":
            #client wants to know the authed users
            if message == "get_active_users":
                if self.scope["user_id"]:
                    self.send_json({
                        "type":"active_users",
                        "message":[get_user_data(user_id) for user_id in active_users.keys()]
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
            self.send_json({
                "type":"error",
                "message":"La Li Lu Le Lo"
            })

    def active_users(self, event):
        message = event['message']
        self.send_json({
            "type":"active_users",
            "message":message
        })
    
    def question_started(self, event):
        message = event["message"]
        self.send_json({
            "type":"question_started",
            "message":message
        })