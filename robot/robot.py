import asyncio
import io
import getSC
import time
import os.path
from typing import Dict, List

import aiohttp
import schedule
from multiprocessing import Process
import parser_helper as prs

from multiprocessing import managers,Manager
from queue import Queue

import qqbot

from qqbot.core.util.yaml_util import YamlUtil
from qqbot.core.exception.error import ServerError
from qqbot.model.message import MessageEmbed, MessageEmbedField, MessageEmbedThumbnail, CreateDirectMessageRequest, \
    MessageArk, MessageArkKv, MessageArkObj, MessageArkObjKv
from image_sender import MessageSendRequestImage,AsyncMessageAPIImage

from utils import convert_to_seconds,format_time,datetimeFromBiliTime 
from search import SearchEngine
from screenshot import get_video_screenshot
from up_info import getUPInfo


from data_base import DataBase,ChannelInfo

TESTCMD='test1094'
class Bot:
    def __init__(self,push_enable=True,answer_enable=True,test_cmd_choices=[TESTCMD],**kwargs) -> None:
        self.test_config = YamlUtil.read(os.path.join(os.path.dirname(__file__), "robot_config.yaml"))
        self.t_token = qqbot.Token(self.test_config["token"]["appid"], self.test_config["token"]["token"])
        self.db=DataBase()
        self.opts=kwargs
        self.test_cmds=test_cmd_choices

        # MyManager.register("ChannelInfo",ChannelInfo)
        self.push_enable=push_enable
        self.answer_enable=answer_enable

        self.manager=Manager()
        
        # self.channel_info:ChannelInfo=self.manager.ChannelInfo(self.db)
        self.channel_info=ChannelInfo(self.db)
        self.videoQueue=Manager().Queue()
        self.scQueue=Manager().Queue()
        self.user_info_day=Manager().dict()
        
    async def message_handler(self,event,message: qqbot.Message):
        """
        定义事件回调的处理
        :param event: 事件类型
        :param message: 事件对象（如监听消息是Message对象）
        """
        msg_api = qqbot.AsyncMessageAPI(self.t_token, False)
        # msg_api = AsyncMessageAPIImage(self.t_token,False)
        content=message.content
        
        # subscribed_channel_ids=self.channel_info.getChannels()

        # 打印返回信息
        qqbot.logger.info("event %s" % event + ",receive message %s" % content)
        
        contents=content.split()
        if len(content)<1:
            content=''
        else:
            content=contents[1].strip()
        raw_args=contents[2:]
        channel_id=message.channel_id
        message_to_send=None
        
        if not self.answer_enable and content not in self.test_cmds:
            return

        def danmu_subscribe(danmutype='super_chat'):
            # engine=SearchEngine()
            args=prs.sc_subscribe(raw_args)

            response='ok'
            sc=self.db.sc
            if self.db.sc.inChannel(message.channel_id,args.room_id):
                if self.db.sc.hasType(channel_id,args.room_id,danmutype):
                    response='重复订阅'
                else:
                    self.db.sc.updateType(channel_id,args.room_id,danmutype,value=True)
            else:
                sc.addChannel(message.channel_id,args.room_id,danmu_type=danmutype)

            return response

        def danmu_unsubscribe(danmutype='super_chat'):
            args=prs.sc_subscribe(raw_args)

            sc=self.db.sc
            response='未订阅'

            if self.db.sc.inChannel(message.channel_id,args.room_id):
                if danmutype is None:
                    sc.removeChannel(channel_id,args.room_id)
                    response='ok'
                else:
                    if self.db.sc.hasType(channel_id,args.room_id,danmutype):
                        response='ok'
                        sc.updateType(channel_id,args.room_id,danmutype=danmutype,value=False)

                        if not self.db.sc.hasAnyType(channel_id,args.room_id):
                            sc.removeChannel(channel_id,args.room_id)

            return response

        try:
            if content=='/订阅':
                if self.channel_info.inChannels(message.channel_id):
                    response='已经订阅过了'
                else: 
                    response='收到。录入该频道'
                    self.channel_info.addChannels(message.channel_id)
                    qqbot.logger.info(f"add channel id {message.channel_id}")
                message_to_send = qqbot.MessageSendRequest(content=response, msg_id=message.id)
            elif content=='/取消订阅':
                if self.channel_info.inChannels(message.channel_id):
                    response='收到。取消录入该频道'
                    self.channel_info.removeChannels(message.channel_id)
                    qqbot.logger.info(f"remove channel id {message.channel_id}")
                else: 
                    response='还没有录入频道'
                message_to_send = qqbot.MessageSendRequest(content=response, msg_id=message.id)
            elif content=='/查数据':
                qqbot.logger.info(f"send user data to channel id {message.channel_id}")
                # engine=SearchEngine()
                info=getUPInfo(uid=387636363)
                await msg_api.post_message(channel_id, self.get_user_info_message3(info,message.id))
                return
            elif content=='/SC推送' or content=='sc':
                qqbot.logger.info(f"sc subscribe to channel id {message.channel_id}")

                response=danmu_subscribe()
            elif content=='/取消SC推送' or content=='!sc':
                qqbot.logger.info(f"cancel sc subscribe to channel id {message.channel_id}")
                response=danmu_unsubscribe()
            elif content=='/礼物推送' or content=='gift':
                qqbot.logger.info(f"gift subscribe to channel id {message.channel_id}")
                response=danmu_subscribe('gift')

            elif content=='/取消礼物推送' or content=='!gift':
                qqbot.logger.info(f"cancel gift subscribe to channel id {message.channel_id}")
                response=danmu_unsubscribe('gift')

            elif content=='查数据':
                qqbot.logger.info(f"send user data to channel id {message.channel_id}")
                engine=SearchEngine()
                # info=engine.getUPInfo(uid=387636363)
                # info=await getFansAndCaption()
                # await msg_api.post_message(channel_id, self.get_user_info_message2(info,message.id))
                return
            elif content==TESTCMD:
                qqbot.logger.info(f"send user data to channel id {message.channel_id}")
                # engine=SearchEngine()
                info=getUPInfo(uid=387636363)
                await msg_api.post_message(channel_id, self.get_user_info_message3(info,message.id))
                return
                # response='图片'
                # img=io.BytesIO(await screenshot.getscreenshot())
                # message_to_send = MessageSendRequestImage(
                #     content=response, msg_id=message.id,file_image=img)
            else:
                response='未知指令。请重试'
                message_to_send = qqbot.MessageSendRequest(
                    content=response, msg_id=message.id)
                    # image='https://i0.hdslb.com/bfs/archive/947aa5d51bfd57b811651e9b95bd39d386b40176.jpg')
                
        except Exception as e:
            print(e)
            message_to_send=None
            response='出错了'

        if message_to_send is None:
            message_to_send = qqbot.MessageSendRequest(content=response, msg_id=message.id)
        # 发送消息告知用户
        await msg_api.post_message(channel_id, message_to_send)
    
    
    def searchVideoTask(self,queue:Queue):
        # while True:
        #     queue.put({'bvid':123,'title':'hello'}) 
        #     print('send')
        #     time.sleep(10)
        engine=SearchEngine()
        db=DataBase()
        videos_recorded=set()
            
        def search():
            if db.numChannels()<=0:
                return
            # qqbot.logger.info('start searching videos...')
            last_time=db.lastestTime()
            cnt=[0]
            
            def searchKeyword(keyword:str):
                page=1
                total_page=None
                old_video_flag=False
                while not old_video_flag:
                    result=engine.searchOnce(engine.getSearchURL(keyword,page=page),engine.isLuLuVideo)
                    if result is None:
                        qqbot.logger.info('search error')
                        break
                    videos,numPage=result

                    if total_page is None:
                        total_page=numPage
                        
                    for video in videos:
                        if video['pubdate']>last_time:
                            if video['bvid'] in videos_recorded:
                                continue
                            videos_recorded.add(video['bvid'])
                            print(f"find video {video['bvid']}")
                            queue.put(video)
                            cnt[0]+=1
                        else:
                            old_video_flag=True
                        
                    page+=1
                    if page>total_page:
                        break
            keywords=['雫るる','lulu','雫露露','雫lulu']
            for keyword in keywords:
                # print(f'search keyword {keyword}')
                searchKeyword(keyword)
            # qqbot.logger.info(f'find {cnt[0]} videos')
            if cnt[0]>0:
                qqbot.logger.info(f'find {cnt[0]} videos')
                db.updateTime()
                
        schedule.every(30).seconds.do(search)
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                qqbot.logger.error(f'error {e} occured. Sleep 300 seconds to restart...')
                time.sleep(300)
            
    def set_today_info_every_day(self,info:dict):
        '''
            fans.log:
                timestamp fan

            captains.log:
                timestamp captain
        '''
        # with open('fans.log','r')as f:
        #     lines=f.readlines()
        #     latest_fans=lines[-1].split()
        #     latest_fans=int(latest_fans[1])
        #     info['fans_day']=latest_fans

        # with open('captains.log','r')as f:
        #     lines=f.readlines()
        #     latest_captains=lines[-1].split()
        #     latest_captains=int(latest_captains[1])
        #     info['captains_day']=latest_captains
        db=DataBase()
        upInfoDatabase=db.upInfo
        up_info=upInfoDatabase.getInfo(387636363)
        info['fans_day']=up_info[-1]['fans']
        info['captains_day']=up_info[-1]['captains']
        
        def set_today_info():
            engine=SearchEngine()
            info_get=engine.getUPInfo(uid=387636363)
            info['fans_day']=info_get['fans']
            info['captains_day']=info_get['captains']

            upInfoDatabase.addInfo(387636363,info['fans_day'],info['captains_day'])

            # with open('fans.log','w')as f:
            #     print(f'{int(time.time())} {info["fans_day"]}',file=f)
            # with open('captains.log','w')as f:
            #     print(f'{int(time.time())} {info["captains_day"]}',file=f)

        schedule.every().day.at("16:00").do(set_today_info)
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                qqbot.logger.error(f'error {e} occured. Sleep 300 seconds to restart...')
                time.sleep(300)

    def set_schedule_task(self,queue:Queue,send_img=True):
        channel_info=ChannelInfo(DataBase())
        def send_video():
            if channel_info.numChannels()<=0:
                return
            qqbot.logger.info('to send videos')
            loop = asyncio.get_event_loop()
            sem=asyncio.Semaphore(1)
            # qqbot.logger.info('start looping')

            # subscribed_channel_ids=channel_info.getChannels()
            # if len(subscribed_channel_ids)==0:
            #     # qqbot.logger.info('no message to send')
            #     return
            
            content = queue.get()
            failed=[False,False]
            # if send_img:
            #     send,image_bytes=self.get_video_message_image(content)
            #     print(send.msg.content)
            # else:
            #     send=self.get_video_message(content)
            #     print(send.content)

            msg_api = AsyncMessageAPIImage(self.t_token, False)
            
            async def task(id,max_try=2):
                while True:
                    try:
                        async with sem:
                            if False:
                            # if not failed[1]:
                                send,image_bytes=await self.get_video_message_image(content)
                                print(send.msg.content)
                            else:
                                send=self.get_video_message(content)
                                print(send.content)
                            qqbot.logger.info(f'send video to channel {id}...')
                            await msg_api.post_message(id, send)
                            qqbot.logger.info(f'send video to channel {id} success!')
                        return
                    except Exception as e:
                        # raise
                        failed[1]=True
                        if max_try>0:
                            max_try-=1
                            qqbot.logger.info(f'error occured: {e} Sleep 300 seconds and try again...')
                            time.sleep(300)
                        else:
                            # qqbot.logger.error(f'time out when sending video to channel {id}')
                            qqbot.logger.error(f'exception {e} when send to channel {id}')
                            failed[0]=True
                            return
            
            tasks=[]
            for id in channel_info.getChannels():
                tasks.append(task(id))
                
            if len(tasks)>0:
                loop.run_until_complete(asyncio.gather(*tasks))
                
            if failed[0]:
                queue.put(content)
            


        schedule.every(10).seconds.do(send_video)
        while True:
            schedule.run_pending()
            time.sleep(1)

    def get_video_message(self,video):
        # 构造消息发送请求数据对象
        video['pubdate']=str(datetimeFromBiliTime(video['pubdate']))
        title=str.replace(video['title'],'<em class="keyword">','')
        video['title']=str.replace(title,'</em>','')
        duration=video['duration']
        
        if type(duration)!=int:
            duration=convert_to_seconds(video['duration'])
        video['duration']=format_time(duration)

        title=video['title']
        author=video['author']
        duration=video['duration']
        bvid=video['bvid']
        pubdate=video['pubdate']
        content=f'{title}\n作者：{author}\n时长：{duration}\nBV号：{bvid}\n发布时间：{pubdate}'
        message_to_send = qqbot.MessageSendRequest(
            content=content,image='https:'+video['pic'],msg_id='10000')
        return message_to_send
        
    def get_user_info_message(self,info,msg_id):
        # 构造消息发送请求数据对象
        name=info['name']
        coins=info['coins']
        attention=info['attention']
        captains=info['captains']
        fans=info['fans']
        fans_day=self.user_info_day['fans_day']
        captains_day=self.user_info_day['captains_day']
        fans_delta='暂无' if fans_day is None else fans-fans_day
        captains_delta='暂无' if captains_day is None else captains-captains_day
        content=f'{name}\n粉丝：{fans}\n硬币：{coins}\n关注：{attention}\n舰长：{captains}\n粉丝增量：{fans_delta}\n舰长增量：{captains_delta}'
        message_to_send = qqbot.MessageSendRequest(
            content=content,msg_id=msg_id)
        return message_to_send
        
    def get_user_info_message2(self,info,msg_id):
        # 构造消息发送请求数据对象
        fans,captions=info
        name='雫るる_Official'
        content=f'{name}\n{fans}\n{captions}'
        message_to_send = qqbot.MessageSendRequest(
            content=content,msg_id=msg_id)
        return message_to_send

    def get_user_info_message3(self,info,msg_id):
        # 构造消息发送请求数据对象
        name=info['name']
        captains=info['captains']
        fans=info['fans']
        fans_day=self.user_info_day['fans_day']
        captains_day=self.user_info_day['captains_day']
        fans_delta='暂无' if fans_day is None else fans-fans_day
        captains_delta='暂无' if captains_day is None else captains-captains_day
        content=f'''\
{name}
📈涨跌粉：{fans}
粉丝增量：{fans_delta}
日：{info['f1d']} 周：{info['f7d']} 月：{info['f30d']}

🚢大航海：{captains}
实时增量：{captains_delta}
日：{info['c1d']} 周：{info['c7d']} 月：{info['c30d']}
3日内到期：{info['due3day']}
生涯平均：{info['cavg']}
粉丝团：{info['fclub']}
爬自拉普拉斯\
'''
        #content='hello'
        message_to_send = qqbot.MessageSendRequest(
            content=content,msg_id=msg_id)
        return message_to_send

    # def get_video_message_image(self,video):
    #     # 构造消息发送请求数据对象
    #     uid=video['mid']
    #     aid=str(video['aid'])
    #     bvid=video['bvid']
        
    #     dynamic_info=SearchEngine().searchVideoFromDynamics(uid,aid)
    #     loop = asyncio.get_event_loop()
    #     image_bytes=loop.run_until_complete(get_video_screenshot(dynamic_info))
    #     image_stream=io.BytesIO(image_bytes)
    #     content=f'视频投稿：{bvid}'
    #     message_to_send = MessageSendRequestImage(
    #         content=content, msg_id='10000',file_image=image_stream)
    #     return message_to_send,image_bytes
    async def get_video_message_image(self,video):
        # 构造消息发送请求数据对象
        uid=video['mid']
        aid=str(video['aid'])
        bvid=video['bvid']
        
        dynamic_info=SearchEngine().searchVideoFromDynamics(uid,aid)
        # loop = asyncio.get_event_loop()
        
        image_bytes=video.get('image_bytes',None)
        if image_bytes is None:
            image_bytes=await get_video_screenshot(dynamic_info)
        
        video['image_bytes']=image_bytes

        image_stream=io.BytesIO(image_bytes)
        content=f'视频投稿：{bvid}'
        message_to_send = MessageSendRequestImage(
            content=content, msg_id='10000',file_image=image_stream)
        return message_to_send,image_bytes

    def get_sc_message(self,msg):
        info=msg
        name=info['uname']
        price=info['price']
        message=info['message']
        content=f'''\
醒目留言
-------------------------------------
{message}
-------------------------------------
{price}￥
By {name}\
'''
        #content='hello'
        message_to_send = qqbot.MessageSendRequest(
            content=content,msg_id='10000')
        return message_to_send

    def get_gift_message(self,msg):
        info=msg
        name=info['uname']
        price=info['price']
        content=f'''\
礼物
-------------------------------------
{info['gift_name']} x {info['num']}
{price}￥
By {name}\
'''
        #content='hello'
        message_to_send = qqbot.MessageSendRequest(
            content=content,msg_id='10000')
        return message_to_send

    def get_live_end_message(self,msg):
        info=msg
        room_id=info['room_id']
        money=info['money']
        content=f'''\
下播了 (房间号：{room_id})
-------------------------------------
营收：{money}￥
'''
        #content='hello'
        message_to_send = qqbot.MessageSendRequest(
            content=content,msg_id='10000')
        return message_to_send

    async def handle_sc_msg(self,chid,msg,danmu_type):
        msg_api = AsyncMessageAPIImage(self.t_token, False)
        if danmu_type=='super_chat':
            send=self.get_sc_message(msg)
        elif danmu_type=='gift':
            send=self.get_gift_message(msg)
        elif danmu_type=='live_end':
            send=self.get_live_end_message(msg)
        else:
            qqbot.logger.error(f'unknown danmu type {danmu_type}')
            return
            # raise Exception(f'unknown danmu type {danmu_type}')

        print(send.content)
        qqbot.logger.info(f'send sc to channel {chid}')
        await msg_api.post_message(chid, send)

    def sendSC(self,params_queue:Queue):
        loop=asyncio.get_event_loop()
        while True:
            chid,params,danmu_type=params_queue.get()
            loop.run_until_complete(self.handle_sc_msg(chid,params,danmu_type))


    def run(self):
        
        if self.push_enable:
            # 定时推送主动消息
            Process(target=self.searchVideoTask,args=(self.videoQueue,)).start()
            Process(target=self.set_schedule_task,args=(self.videoQueue,)).start()
        Process(target=self.set_today_info_every_day,args=(self.user_info_day,)).start()

        if self.opts.get('pushSC'):
            Process(target=self.sendSC,args=(self.scQueue,)).start()
            Process(target=getSC.run,args=(self.scQueue,)).start()
        time.sleep(1)
        # @机器人后推送被动消息
        qqbot_handler = qqbot.Handler(
            qqbot.HandlerType.AT_MESSAGE_EVENT_HANDLER, self.message_handler
        )
        qqbot.async_listen_events(self.t_token, False, qqbot_handler)
        


# async的异步接口的使用示例
if __name__ == "__main__":
    bot=Bot(push_enable=True,answer_enable=True,pushSC=True,test_cmd_choices=['sc','!sc','gift','!gift']) 
    #bot.db.updateTime(tm=1701950937)
    bot.run()
