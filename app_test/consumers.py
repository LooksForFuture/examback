from json import loads, dumps

from channels.generic.websocket import WebsocketConsumer
from rest_framework_simplejwt.tokens import AccessToken
from asgiref.sync import async_to_sync

from django.contrib.auth import get_user_model

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

#active users are stored based on their user_id
active_users = []

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.scope["user_id"] = None #jwt token
        self.accept()
    
    def disconnect(self, close_code):
        if self.scope["user_id"] != None:
            for i in range(len(active_users)):
                if active_users[i] == self.scope["user_id"]:
                    del active_users[i]
                    break

            #remove from authed group
            async_to_sync(self.channel_layer.group_discard)(
                "authed",
                self.channel_name
            )
            #inform everyone about the exit of user
            async_to_sync(self.channel_layer.group_send)(
                "authed",
                {
                    'type':'active_users',
                    'message':[get_user_data(user_id) for user_id in active_users]
                }
            )

    def receive(self, text_data):
        text_data_json = loads(text_data)

        #trying to authenticate -> need a jwt token
        if text_data_json["type"] == "auth":
            try:
                token = AccessToken(text_data_json["message"])
            except:
                #token is invalid
                self.send(dumps({
                    "type":"error",
                    "message":"auth"
                }))
                return

            self.scope["user_id"] = token["user_id"]
            #add user to the authed users
            async_to_sync(self.channel_layer.group_add)(
                "authed",
                self.channel_name
            )

            found = False
            for user in active_users:
                if user == token["user_id"]:
                    found = True
                    return

            if not found:
                active_users.append(token["user_id"]) #add user to the active ones
                #inform everyone about the enterance of new user
                async_to_sync(self.channel_layer.group_send)(
                    "authed",
                    {
                        'type':'active_users',
                        'message':[get_user_data(user_id) for user_id in active_users]
                    }
                )
        
        #client wants information
        elif text_data_json["type"] == "query":
            #client wants to know the authed users
            if text_data_json["message"] == "get_active_users":
                if self.scope["token"]:
                    self.send(dumps({
                        "type":"active_users",
                        "message":[get_user_data(user_id) for user_id in active_users]
                    }))
                else:
                    #client has not been authenticated
                    self.send(dumps({
                        "type":"error",
                        "message":"auth"
                    }))
            
            #client wants to know if they are connected
            elif text_data_json["message"] == "auth":
                if self.scope["token"]:
                    self.send(dumps({
                        "type":"auth",
                        "message":True
                    }))
                
                else:
                    self.send(dumps({
                        "type":"auth",
                        "message":False
                    }))

            #client message is not recognized
            else:
                self.send(dumps({
                    "type":"error",
                    "message":"La Li Lu Le Lo"
                }))

        #client message is not recognized
        else:
            self.send(dumps({
                "type":"error",
                "message":"La Li Lu Le Lo"
            }))

    def active_users(self, event):
        message = event['message']
        self.send(text_data=dumps({
            "type":"active_users",
            "message":message
        }))
    
    def question_started(self, event):
        message = event["message"]
        self.send(text_data=dumps({
            "type":"question_started",
            "message":message
        }))