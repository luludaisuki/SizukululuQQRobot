from data_base import DataBase
import asyncio
import http.cookies
import aiohttp
from danmuji.src.blivedm import (
    BaseHandler, BLiveClient, HeartbeatMessage, DanmakuMessage, GiftMessage, GuardBuyMessage, SuperChatMessage,
    SuperChatDeleteMessage
)
from danmuji.src.libs import get_live_info, get_live_status, get_user_info, get_user_icon, get_user_name
from typing import Optional,Dict,Any
from queue import Queue
# import logging
# logger: logging.Logger = logging.getLogger()
import qqbot
logger=qqbot.logger
# logger.setLevel(logging.DEBUG)


SESSDATA = ''

def init_session():
    cookies = http.cookies.SimpleCookie()
    cookies['SESSDATA'] = SESSDATA
    cookies['SESSDATA']['domain'] = 'bilibili.com'

    session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=0))
    session.cookie_jar.update_cookies(cookies)

    return session

class SCHandlerFactory:
    def __init__(self,db:DataBase,queue:Queue) -> None:
        self.sc=db.sc
        self.room_info=db.room_status
        self.q=queue

    def getSCHandler(self,roomid):
        async def handler(msg:dict):
            channel_lst=self.sc.listChannels(roomid)
            for ch in channel_lst:
                self.q.put((ch,msg))
            # await asyncio.gather(*[self.msg_fn(ch,msg) for ch in channel_lst])
        return handler

    def getSCHandler2(self,roomid):
        async def handler(msg:dict,danmutype:str):
            channel_lst=self.sc.listChannelsWithInfo(roomid)
            for ch_info in channel_lst:
                if ch_info[danmutype]:
                    ch=ch_info['channel_id']
                    self.q.put((ch,msg,danmutype))
            # await asyncio.gather(*[self.msg_fn(ch,msg) for ch in channel_lst])
        return handler

    def getSCHandler3(self,roomid):
        async def handler(msg:dict,danmutype:str):
            func_name=danmutype
            if danmutype=='heartbeat':
                new_status=await get_live_status(roomid)
                logger.info(f'\n---- 收到心跳包（{roomid}） ----\n' + f'直播状态:{new_status}')
                if(self.room_info.updateRoom(roomid,new_status))==-1:
                    # live ended
                    info=self.room_info.getInfo(roomid)
                    msg={'room_id':roomid,'money':info['money']}
                    danmutype='gift'
                    func_name='live_end'
                else:
                    return
            else:
                self.room_info.addMoney(roomid,msg['price'])
                if msg['price']<10:
                    return

            channel_lst=self.sc.listChannelsWithInfo(roomid)
            for ch_info in channel_lst:
                if ch_info[danmutype]:
                    ch=ch_info['channel_id']
                    self.q.put((ch,msg,func_name))
            # await asyncio.gather(*[self.msg_fn(ch,msg) for ch in channel_lst])
        return handler

class MyHandler(BaseHandler):
    def __init__(self,inner_handler) -> None:
        super().__init__()
        self.handler=inner_handler

    async def _on_heartbeat(self, client: BLiveClient, message: HeartbeatMessage, opts: Optional[Dict[str, Any]]):
        """
        收到心跳包（人气值）
        """
        params: Dict[str, Any] = vars(message)
        return await self.handler(params,'heartbeat')

    async def _on_super_chat(self, client: BLiveClient, message: SuperChatMessage, opts: Optional[Dict[str, Any]]):
        """
        醒目留言
        """
        params: Dict[str, Any] = vars(message)
        logger.info('\n---- 醒目留言 ----\n' + ''.join([f'{key}: \t{params[key]}\n' for key in params]))
        return await self.handler(params,'super_chat')

    async def _on_gift(self, client: BLiveClient, message: GiftMessage, opts: Optional[Dict[str, Any]]):
        """
        收到礼物
        """
        params: Dict[str, Any] = vars(message)
        logger.info('\n---- 收到礼物 ----\n' + ''.join([f'{key}: \t{params[key]}\n' for key in params]))
        params['price']=params['price']/1000
        return await self.handler(params,'gift')

    # async def _on_danmaku(self, client: BLiveClient, message: DanmakuMessage, opts: Optional[Dict[str, Any]]):
    #     """
    #     收到弹幕
    #     """
    #     params: Dict[str, Any] = vars(message)
    #     logger.info('\n---- 收到弹幕 ----\n' + ''.join([f'{key}: \t{params[key]}\n' for key in ['msg']]))

    async def _on_buy_guard(self, client: BLiveClient, message: GuardBuyMessage, opts: Optional[Dict[str, Any]]):
        """
        有人上舰
        """
        params: Dict[str, Any] = vars(message)
        logger.debug('\n---- 有人上舰 ----\n' + ''.join([f'{key}: \t{params[key]}\n' for key in params]))
        return await self.handler(params,'gift')

def run(queue):
    db=DataBase()

    scHandlerFactory=SCHandlerFactory(db,queue)
    async def run_():
        room_dict={}
        session=init_session()
        try:
            while True:
                new_dict={}
                for room_id in db.sc.listRoomIDs():
                    item=room_dict.get(room_id,None)
                    if item is not None:
                        item:BLiveClient
                        if not item.is_running:
                            item.start()
                        new_dict[room_id]=item
                        room_dict.pop(room_id)
                    else:
                        new_client=BLiveClient(room_id,session=session)
                        new_client.add_handler(MyHandler(scHandlerFactory.getSCHandler3(room_id)))
                        new_client.start()
                        new_dict[room_id]=new_client
                        
                # clients that should be removed
                for v in room_dict.values():
                    v:BLiveClient
                    await v.stop_and_close()

                room_dict=new_dict

                await asyncio.sleep(10)
        finally:
            for v in room_dict.values():
                v:BLiveClient
                await v.stop_and_close()

    asyncio.run(run_())


def getLiveInfo(room_id):
    loop=asyncio.get_event_loop()
    info=loop.run_until_complete(get_live_info(room_id))
    return info
