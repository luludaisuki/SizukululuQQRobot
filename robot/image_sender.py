import json
from qqbot.model.token import Token
from qqbot import AsyncMessageAPI
from qqbot import MessageSendRequest
from qqbot import Message
from qqbot import MessageEmbed,MessageArk,MessageReference,MessageMarkdown

from qqbot.core.network.url import get_url, APIConstant
from qqbot.core.util.json_util import JsonUtil
from qqbot.model.message import (
    MessageSendRequest,
    Message,
    MessageKeyboard,
)
from qqbot.model.token import Token

import aiohttp

from qqbot.core.util import logging

logger = logging.getLogger()

from qqbot.core.network.async_http import _handle_response

class AsyncHttpImage:
    def __init__(self, time_out, token, type):
        self.timeout = time_out
        self.token = token
        self.scheme = type

    async def post(self, api_url, request=None, params=None,data=None):
        headers = {
            "Authorization": self.scheme + " " + self.token,
            "User-Agent": "BotPythonSDK/v0.5.4",
        }
        logger.debug(
            "[HTTP] post headers: %s, api_url: %s, request: %s"
            % (headers, api_url, request)
        )
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=api_url,
                params=params,
                json=request,
                timeout=self.timeout,
                headers=headers,
                data=data
            ) as resp:
                content = await resp.text()
                _handle_response(api_url, resp, content)
                return content

class MessageSendRequestImage:
    def __init__(
        self,
        content: str = "",
        msg_id: str = None,
        embed: MessageEmbed = None,
        ark: MessageArk = None,
        image: str = "",
        message_reference: MessageReference = None,
        markdown: MessageMarkdown = None,
        keyboard: MessageKeyboard = None,
        file_image=None
    ):
        """
        机器人发送消息时所传的数据对象

        :param content: 消息内容，文本内容，支持内嵌格式
        :param msg_id: 要回复的消息id(Message.id), 在 AT_CREATE_MESSAGE 事件中获取。带了 msg_id 视为被动回复消息，否则视为主动推送消息
        :param embed: embed 消息，一种特殊的 ark
        :param ark: ark 消息
        :param image: 图片url地址
        :param message_reference: 引用消息
        :param markdown: markdown 消息
        :param keyboard: markdown 消息内的按钮
        """

        self.msg=MessageSendRequest(content,msg_id,embed,ark,image,message_reference,markdown,keyboard)
        self.msg.__setattr__('file_image',file_image)

class AsyncMessageAPIImage:
    def __init__(self, token: Token, is_sandbox: bool, timeout: int = 3):
        self.msgApi=AsyncMessageAPI(token,is_sandbox,timeout)
        self.http_async = AsyncHttpImage(timeout, token.get_string(), token.get_type())
        
    async def post_message(self, channel_id: str, message_send: MessageSendRequest,form_data=None) -> Message:
        """
        发送消息

        要求操作人在该子频道具有发送消息的权限。
        发送成功之后，会触发一个创建消息的事件。
        被动回复消息有效期为 5 分钟
        主动推送消息每日每个子频道限 2 条
        发送消息接口要求机器人接口需要链接到websocket gateway 上保持在线状态

        :param channel_id: 子频道ID
        :param message_send: MessageSendRequest对象
        :return: Message对象
        """

        url = get_url(APIConstant.messagesURI, self.msgApi.is_sandbox).format(channel_id=channel_id)

        if type(message_send)==MessageSendRequestImage:
            message_send:MessageSendRequestImage
            data={key:value for key,value in message_send.msg.__dict__.items() if value}
            response = await self.http_async.post(url,data=data)
        else:
            request_json = JsonUtil.obj2json_serialize(message_send)
            response = await self.http_async.post(url, request_json)
        return json.loads(response, object_hook=Message)
    
if __name__=='__main__':
    msg=MessageSendRequestImage(content='hello')

    data={key:value for key,value in msg.msg.__dict__.items() if value}
    
    print(data)