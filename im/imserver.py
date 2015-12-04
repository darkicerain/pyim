#!/usr/bin/env python

import asyncio
import json
import time
import os,sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,parentdir)
import websockets


class room:
    users = []

    def __init__(self, name,id=time.time()):
        self.name = name
        self.id=id
        self.run()
    def run(self):
        pass

    def add(self, user):
        self.users.append(user)

        yield from self.message(user,'{} come in the room!'.format(user['name']),True)



    def remove(self, user):
        self.users.remove(user)

        yield from self.message(user,"{} leave the room!".format(user['name']),True)



    def get_users(self):
        return self.users

    def message(self, user, msg ,action=None):
        send = {
            "msg": msg,
            "u_id": user["id"],
            "u_name":user["name"],
            "room_id": self.id,
            "users":[]
        }
        if action is not None:
            for u in self.users:
                send["users"].append({'u_id':u['id'],'u_name':u['name']})
        for u in self.users:

            if u["socket"].open is True:
                yield from u['socket'].send(json.dumps(send))




class IMserver:
    users = []
    rooms = []

    def __init__(self, host=None, port=None):
        self.host = host
        self.port = port
        print(u"im started...")
        self.run()

    def run(self):
        self.rooms.append(room("default",0))
        # print(self.rooms)
        start_server = websockets.serve(self.handler, self.host, self.port)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()


    @asyncio.coroutine
    def handler(self, websocket, path):
        while True:
            remote_address = websocket.remote_address
            user = {"ip": remote_address[0], "port": remote_address[1], "socket": websocket}
            self.users.append(user)
            message = yield from websocket.recv()
            if message is not None:

                yield from self.event(message, user)

            for r in self.rooms:
                yield from self.heart(r)

    def event(self, message, user):

        message = json.loads(message)

        if message['u_id'] is None:
            user['id'] = ''.join([user['ip'], str(user['port'])])
            user['name'] = user['id']
        else:
            user['id'] = message['u_id']

        if message['event'] == 'in':
            yield from self.on_event_in(user, message['msg'])
        if message['event'] == 'room_msg':

            yield from self.on_event_room_msg(user, message['room_id'], message['msg'])

    def on_event_room_msg(self, user, room_id, msg):


        for r in self.rooms:
            if str(r.id) == str(room_id):
                yield from r.message(user, msg)

    def on_event_user_msg(self, user, user_id, msg):

        pass

    def on_event_in(self, user, msg):

        yield from self.rooms[0].add(user)


    def heart(self,room):
        for u in room.users:
            if u["socket"].open is not True:
                yield from room.remove(u)


if __name__ == '__main__':
    im=IMserver('127.0.0.1', 1234)
