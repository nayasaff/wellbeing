import json
from channels.generic.websocket import AsyncWebsocketConsumer
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecsWellbeing.settings')
django.setup()
from supportgroups.models import Messages, Groups, Reactions
from asgiref.sync import sync_to_async
from supportgroups.decorators import has_permission


class MessageStream(AsyncWebsocketConsumer):
    #write the functions for the consumer
    async def connect(self):
        self.id = self.scope['url_route']['kwargs']['id']
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = f'chat_{self.id}'

        # Join room group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    @has_permission('send_message')
    async def receive(self, text_data):
        #receive a message
        data = json.loads(text_data)
        print(text_data)
        if data['type'] == 'text' :
            if "reply" in data and data['reply'] is not None:
                message = await sync_to_async(Messages.objects.create)(text=data['text'], username = data['username'], type = data['type'],  reply = data['reply'])
            else :  
                message = await sync_to_async(Messages.objects.create)(text=data['text'], username = data['username'], type = data['type'])
        elif data['type'] == 'image':
            if "reply" in data and data['reply'] is not None:
                message = await sync_to_async(Messages.objects.create)(text=data['text'], username = data['username'], type = data['type'], reply = data['reply'], url = data['url'],)
            else :
                message = await sync_to_async(Messages.objects.create)(text=data['text'], username = data['username'], type = data['type'], url = data['url'],)
        else:
            if "reply" in data and data['reply'] is not None:
                message = await sync_to_async(Messages.objects.create)(text=data['text'], username = data['username'], type = data['type'], reply = data['reply'], size=data['size'], url = data['url'],)
            else :
                message = await sync_to_async(Messages.objects.create)(text=data['text'], username = data['username'], type = data['type'], size=data['size'], url = data['url'],)
        self.id = self.scope['url_route']['kwargs']["id"]
        group = await sync_to_async(Groups.objects.get)(id = self.id)
        await sync_to_async(group.messages.add)(message)
        serialized_message = {
            'id': message.id,
            'text': message.text,
            'username': message.username,
            'type': message.type,
            'group_id' : self.id,
            'date' : message.date.isoformat(),
            "url" : message.url,
            "reply" : message.reply,
            "size" : message.size
        }
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat_message',
                'message': serialized_message
            }
        )
 
    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

class ReactionsStream(AsyncWebsocketConsumer):

    async def connect(self):
        self.group_name = f'reaction'

        # Join room group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        print(text_data)
        message = await sync_to_async(Messages.objects.get)(id = data['message'])
        try:
            reaction = await sync_to_async(Reactions.objects.get)(emoji=data['emoji'], message = message)
            if(data["users"] not in reaction.users) :
                reaction.count += 1
                reaction.users.append(data['users'])
            else :
                reaction.count -= 1
                reaction.users.remove(data['users'])
                if reaction.count == 0 :
                    await sync_to_async(reaction.delete)()
                    return
        except Reactions.DoesNotExist:
            reaction = await sync_to_async(Reactions.objects.create)(emoji=data['emoji'], message = message, users = [data['users']])
        await sync_to_async(reaction.save)()

        serialized_reaction = {
            'id': reaction.id,
            'emoji': reaction.emoji,
            'message': message.id,
            'users': reaction.users,
            'count': reaction.count
        }


        await self.channel_layer.group_send(
            self.group_name,
            {
                "type" : 'reaction_message',
                'reaction': serialized_reaction
            }
        )

    #function name is same as type
    async def reaction_message(self, event):
        reaction = event['reaction']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'reaction': reaction
        }))