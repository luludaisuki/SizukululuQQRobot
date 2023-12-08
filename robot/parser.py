from typing import List,Dict
import argparse
from image_sender import MessageSendRequestImage,AsyncMessageAPIImage

import qqbot

from qqbot.core.util.yaml_util import YamlUtil
from qqbot.core.exception.error import ServerError
from qqbot.model.message import MessageEmbed, MessageEmbedField, MessageEmbedThumbnail, CreateDirectMessageRequest, \
    MessageArk, MessageArkKv, MessageArkObj, MessageArkObjKv
from image_sender import MessageSendRequestImage,AsyncMessageAPIImage

from utils import convert_to_seconds,format_time,datetimeFromBiliTime 
from search import SearchEngine
from screenshot import get_video_screenshot

from data_base import DataBase,ChannelInfo
import argparse

def getArgs(cmd:List[str]):
    parser=argparse.ArgumentParser(prog='@机器人',add_help=False,description='雫露露相关推送q频机器人。')
    # parser.add_argument('--foo', action='store_true', help='foo help')
    subparsers = parser.add_subparsers(help='指令说明')

    # create the parser for the "a" command
    parser_sub = subparsers.add_parser('/订阅', help='在该子频道订阅推送',add_help=False)
    parser_sub.set_defaults(func=subscribe,unsub=False)
    parser_sub.add_argument('-o','--订阅类型',type=str,dest='sub_obj',default='视频',metavar='订阅类型',choices=['视频','待审核作品'])

    parser_un_sub = subparsers.add_parser('/取消订阅', help='在该子频道取消订阅推送',add_help=False)
    parser_un_sub.set_defaults(func=subscribe,unsub=True)
    parser_un_sub.add_argument('-o','--订阅类型',type=str,dest='sub_obj',default='视频',metavar='订阅类型',choices=['视频','待审核作品'])

    parser_white = subparsers.add_parser('/加入白名单', help='将指定作者加入白名单。总是推送其作品。',add_help=False)
    parser_white.set_defaults(func=setStatus,status='white')
    parser_white.add_argument('uid',metavar='UID',nargs='+')

    parser_under_censor = subparsers.add_parser(
        '/设为待审核', help='将指定作者加入待审核列表（既不在白名单也不在黑名单）。若频道订阅了推送待审核作品，将把其作品进行推送',add_help=False)
    parser_under_censor.set_defaults(func=setStatus,status='under_censor')
    parser_under_censor.add_argument('uid',metavar='UID',nargs='+')

    parser_black = subparsers.add_parser('/加入黑名单', help='将指定作者加入黑名单。总是不推送其作品。',add_help=False)
    parser_black.set_defaults(func=setStatus,status='black')
    parser_black.add_argument('uid',metavar='UID',nargs='+')

    parser_help = subparsers.add_parser('/帮助', help='显示帮助。/帮助后加指令可查看更详细帮助',add_help=False)
    parser_dict={'订阅':parser_sub,'取消订阅':parser_un_sub,
                 '加入白名单':parser_white,'设为待审核':parser_under_censor,'加入黑名单':parser_black,
                 '帮助':parser_help
                 }
    parser_help.add_argument('help_cmd',type=str,default='',
                             help='针对特定的指令进行说明',
                             metavar='指令',
                             nargs='?',
                             choices=parser_dict.keys())
    parser_dict['']=parser
    parser_help.set_defaults(parser_dict=parser_dict)
    
    return parser.parse_args(cmd)

async def subscribe(args,message:qqbot.Message,db:DataBase):
    unsub=args.unsub
    channel_id=message.channel_id
    in_channel=db.inChannel(channel_id)

    if unsub:
        if in_channel:
        # if self.channel_info.inChannels(message.channel_id):
            response='已经订阅过了'
        else: 
            response='收到。录入该频道'
            db.addChannel(channel_id)
            qqbot.logger.info(f"add channel id {channel_id}")

    else:
        if in_channel:
            response='收到。取消录入该频道'
            db.removeChannel(channel_id)
            qqbot.logger.info(f"remove channel id {channel_id}")
        else: 
            response='还没有录入频道'

    message_to_send = qqbot.MessageSendRequest(content=response, msg_id=message.id)
    
    
    return message_to_send

async def setStatus(args,message:qqbot.Message,db:DataBase):
    status=args.status
    channel_id=message.channel_id

    response='收到'
    qqbot.logger.info(f"set user status {status}")

    db.user_status.setStatus(channel_id,args.uid,status)

    message_to_send = qqbot.MessageSendRequest(content=response, msg_id=message.id)
    
    return message_to_send

async def help(args,message:qqbot.Message,db:DataBase):
    help_cmd=args['命令']
    parser_dict:Dict['str',argparse.ArgumentParser]=args.parser_dict
    response=parser_dict[help_cmd].format_help()
    qqbot.logger.info(f"help")

    message_to_send = qqbot.MessageSendRequest(content=response, msg_id=message.id)
    
    return message_to_send

if __name__=='__main__':
    args=getArgs(['/帮助'])
    help_cmd=args.help_cmd
    parser_dict:Dict['str',argparse.ArgumentParser]=args.parser_dict
    response=parser_dict[help_cmd].format_help()
    response=response.replace('usage','用法')
    response=response.replace('positional arguments','位置参数')
    
    print(response)