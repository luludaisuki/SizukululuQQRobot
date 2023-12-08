import pymongo
import pymongo.database
import time

class DataBase():
    '''
        database robot:
            Channels: {channel_id}
            UpdateTime: {time}
    '''
    def __init__(self,db_uri='mongodb://localhost:27017/') -> None:
        self.client= pymongo.MongoClient(db_uri)
        self.init_database(self.client)
        self.db=self.client.robot
        self.sc=SC_ChannelInfo(self.db)
        self.room_status=RoomStatus(self.db)
        self.upInfo=UpInfo(self.db)
        # self.user_status=UserStatus(self.db)
    
    def init_database(self,client:pymongo.MongoClient):
        robot=client.robot
        collections=robot.list_collection_names()
        if 'Channels' not in collections:
            channels=robot.Channels
            channels.create_index('channel_id',unique=True)
        if 'UpdateTime' not in collections:
            robot.UpdateTime.insert_one({'_id':0,'time':int(time.time())})

    def getChannels(self):
        return self.db.Channels.find()
    def addChannel(self,channel_id):
        self.db.Channels.insert_one({'channel_id':channel_id})
    def removeChannel(self,channel_id):
        self.db.Channels.delete_one({'channel_id':channel_id})
    def inChannel(self,channel_id):
        return self.db.Channels.count_documents({'channel_id':channel_id},limit=1)>0
    def numChannels(self):
        return self.db.Channels.count_documents({})
    def updateTime(self,tm=None):
        if tm is None:
            tm=int(time.time())
        self.db.UpdateTime.update_one({'_id':0},{'$set':{'time':tm}})
    def lastestTime(self):
        return self.db.UpdateTime.find_one({'_id':0})['time']

class ChannelInfo:
    def __init__(self,db:DataBase) -> None:
        # self.subscribed_channel_ids=set()
        self.db=db
    def getChannels(self):
        # return self.subscribed_channel_ids
        for info in self.db.getChannels():
            yield info['channel_id']
    def addChannels(self,id):
        # self.subscribed_channel_ids.add(id)
        self.db.addChannel(id)
    def removeChannels(self,id):
        # self.subscribed_channel_ids.remove(id)
        self.db.removeChannel(id)
    def inChannels(self,id)->bool:
        # return id in self.subscribed_channel_ids
        return self.db.inChannel(id)
    def numChannels(self):
        return self.db.numChannels()

class SC_ChannelInfo:
    def __init__(self,db:pymongo.database.Database) -> None:
        # self.subscribed_channel_ids=set()
        self.tb=db.SCChannel
        self.type_list=['super_chat','gift']
        self.initData()

    def initData(self):
        channels=self.tb
        channels.create_index(['channel_id','room_id'],unique=True,name='chid_roomid_index')

        for item in self.tb.find():
            for t in self.type_list:
                if t not in item:
                    default_value=False
                    if t=='super_chat':
                        default_value=True
                    self.tb.update_one({'channel_id':item['channel_id'],'room_id':item['room_id']},{'$set':{t:default_value}})
        # index=channels.list_search_indexes('chid_roomid_index')
        # if index is None:
    def listSubs(self,danmu_type=None):
        return self.tb.find()
    def listChannels(self,room_id,danmu_type=None):
        if danmu_type:
            return (item['channel_id'] for item in self.tb.find({'room_id':room_id,danmu_type:True}))
        return (item['channel_id'] for item in self.tb.find({'room_id':room_id}))
    def listChannelsWithInfo(self,room_id):
        return self.tb.find({'room_id':room_id})
    def addChannel(self,channel_id,room_id,danmu_type="super_chat"):
        data={'channel_id':channel_id,'room_id':room_id}
        for t in self.type_list:
            data[t]=False
        data[danmu_type]=True

        self.tb.insert_one(data)
    def removeChannel(self,channel_id,room_id):
        self.tb.delete_one({'channel_id':channel_id,'room_id':room_id})
    def inChannel(self,channel_id,room_id):
        return self.tb.count_documents({'channel_id':channel_id,'room_id':room_id},limit=1)>0
    def hasType(self,channel_id,room_id,danmutype:str):
        return self.tb.count_documents({'channel_id':channel_id,'room_id':room_id,danmutype:True},limit=1)>0

    def hasAnyType(self,channel_id,room_id):
        item=self.tb.find_one({'channel_id':channel_id,'room_id':room_id})

        if item is None:
            return False
        
        for t in self.type_list:
            if item[t]:
                return True
        return False

    def updateType(self,channel_id,room_id,danmutype:str,value=True):
        self.tb.update_one({'channel_id':channel_id,'room_id':room_id},{'$set':{danmutype:value}})

    def listRoomIDs(self):
        infos=self.tb.aggregate([{"$group":{"_id":"$room_id"}}])
        for info in infos:
            yield info['_id']
    
class UserStatus:
    # table: channel_id uid status
    def __init__(self,db:pymongo.database.Database) -> None:
        self.user_status=db.UserStatus
        self.initData()
        
    def initData(self):
        status=self.user_status
        index=status.list_search_indexes('chid_uid_index')
        if index is None:
            status.create_index(['channel_id','uid'],unique=True,name='chid_uid_index')

    def setStatus(self,channel_id:str,uid:str,status:str):
        # status: 'white','black','under_censor'
        assert status in ['white','black','under_censor']
        uid=str(uid)

        self.user_status.update_one({'channel_id':channel_id,'uid':uid},
                                    {'$set':{'channel_id':channel_id,'uid':uid,'status':status}},
                                    upsert=True
                                    )
    def setBlack(self,channel_id:str,uid:str):
        self.setStatus(channel_id,uid,'black')
    def setWhite(self,channel_id:str,uid:str):
        self.setStatus(channel_id,uid,'white')
    def setUncensored(self,channel_id:str,uid:str):
        self.setStatus(channel_id,uid,'under_censor')

class RoomStatus:
    # table: channel_id uid status
    def __init__(self,db:pymongo.database.Database) -> None:
        self.room_status=db.LiveRoomStatus
        self.initData()
        
    def initData(self):
        status=self.room_status
        status.create_index(['room_id'],unique=True,name='room_id_index')

    def updateRoom(self,room_id:str,status=0):
        # status: 0:not living; 1: living
        '''
            return 0: not changed, 1: live started, -1: live ended
        '''

        old_status=self.getInfo(room_id)['status']

        if old_status ==status:
            return 0
        self.room_status.update_one({'room_id':room_id},
                                    {'$set':{'room_id':room_id,'status':status}},
                                    )

        if old_status == 0:
            return 1
        else:
            return -1



    def newRoom(self,room_id:str,money=0,status=0):
        # status: 0:not living; 1: living
        init_value={'room_id':room_id,'money':money,'status':status}
        self.room_status.insert_one(init_value)
        return init_value

    def addMoney(self,room_id:str,money):
        # status: 0:not living; 1: living
        old_status=self.getInfo(room_id)['status']

        if old_status:
            self.room_status.update_one({'room_id':room_id},
                                        {'$inc':{'money':money}},
                                        )
    def getInfo(self,room_id:str):
        # status: 0:not living; 1: living
        info=self.room_status.find_one({'room_id':room_id})
        if info is None:
            info=self.newRoom(room_id) 
        return info


class UpInfo:
    # table: channel_id uid status
    def __init__(self,db:pymongo.database.Database) -> None:
        self.room_status=db.UpInfo
        self.initData()
        
    def initData(self):
        pass
    def addInfo(self,uid,fans,captains):
        self.room_status.insert_one({'uid':uid,'time':int(time.time()),'fans':fans,'captains':captains})
    def getInfo(self,uid):
        return list(self.room_status.find({'uid':uid}).sort("time",pymongo.ASCENDING))  
