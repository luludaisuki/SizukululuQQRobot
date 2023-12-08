import requests
import time
import re
#from watch_coins import getUserInfo
headers = {'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
	AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}

def request_dom(url,headers=headers,cookies=None,max_try=3,params=None,use_proxy=False,timeout=None):
	'''请求url，返回dom文件'''
	if use_proxy:
		proxy=get_proxy()
	else:
		proxy=None
	try:
		response = requests.get(url,headers=headers,cookies=cookies,proxies=proxy,params=params,timeout=timeout)
		if response.status_code == 200:
			return response
		else:
			print('-'*30,'request doc error:',response.status_code)
			try:
				print(response.json())
			except Exception:
				pass
			return response
	except (requests.exceptions.ConnectionError,requests.exceptions.Timeout):
		if max_try>0:
			print(f'wait and try again...\nmax_try={max_try-1}')
			time.sleep(10)
			return request_dom(url=url,headers=headers,cookies=cookies,max_try=max_try-1)
		print('-'*30,'request doc ConnectionError')
		return None

def getUserInfo(uid):
    url=f'https://workers.meta48.live/api/bilibili/user-info/{uid}'
    response=request_dom(url)

    return response.json()

def getCaptainInfo(uid):
    url=f'https://workers.meta48.live/api/bilibili/live-guards/{uid}'
    response=request_dom(url)

    return response.json()

def getCaptainHistory(uid):
    url=f'https://workers.meta48.live/api/bilibili/live-guards-history/{uid}'
    response=request_dom(url)

    return response.json()
def getFanHistory(uid):
    url=f'https://workers.meta48.live/api/bilibili/fans-history/{uid}'
    response=request_dom(url)

    return response.json()

class SearchEngine:
    def __init__(self) -> None:
        self.headers = {'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
            AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}
        self.cookie=self.readCookie()

    def readCookie(self,filename='cookies.txt'):
        with open(filename,'r')as f:
            cookies=f.read().strip()
            # print(cookies)
        cookie = {i.split("=")[0].strip():i.split("=")[1].strip() for i in cookies.split(";")} 
        return cookie
        
    def request_dom(self,url,max_try=3,use_other_cookie=False,other_cookies=None):
        '''请求url，返回dom文件'''
        try:
            if use_other_cookie:
                cookies=other_cookies
            else:
                cookies=self.cookie
            response = requests.get(url,headers=self.headers,cookies=cookies,timeout=10)
            if response.status_code == 200:
                return response
            else:
                print('-'*30,'request doc error:',response.status_code)
                print(response)
                print(response.url)
                return None
        except requests.exceptions.ConnectionError:
            if max_try>0:
                print(f'wait and try again...\nmax_try={max_try-1}')
                time.sleep(10)
                return self.request_dom(url=url,max_try=max_try-1)
            print('-'*30,'request doc ConnectionError')
            return None

    def getSearchURL(self,keyword:str,order='pubdate',tids=0,duration=0,page=1):
        return f'https://api.bilibili.com/x/web-interface/search/type?keyword={keyword}&order={order}&tids={tids}&duration={duration}&page={page}&search_type=video'

    def isLuLuVideo(self,
                    video_info:dict,
                    mid=387636363,
                    pattern=re.compile('(雫るる)|(雫露露)|(雫lulu)'),
                    pattern_pos=re.compile('(lulu)|(天选国V)|(露露)'),
                    pattern_neg=re.compile('(雨宫)|(伊织)|(雨宮)|(伊織)|(府)|(勒夫)|(工会)'),
                    # pattern_neg=re.compile('(陆瑶)|(折原)|(艾露露)|(雨宫)|(伊织)|(雨宮)|(伊織)|(府)|(勒夫)|(工会)'),
                    pattern_area=re.compile('虚拟')
                    )->bool:
        #主播本人
        if video_info['mid']==mid:
            return True

        title,tag,description=video_info['title'],video_info.get('tag',''),video_info['description']
        
        for info in title,tag,description:
            info=info.lower()
            if re.search(pattern=pattern_neg,string=info) is not None:
                return False
            if re.search(pattern=pattern,string=info) is not None:
                return True
            
        return False

    def searchOnce(self,url,matchFunc):
        '''
            return number of pages
            return None if error
        '''
        response = self.request_dom(url=url)

        if response!=None:
            # cookie= response.cookies.get_dict()
            # print(cookie)
            response=response.json()

            if response:
                data=response['data']
                videos=data.get('result',None)
                if videos is None:
                    return None
                numPages=data['numPages']

                videos=[video for video in videos if matchFunc(video)]
                
                return videos,numPages
            else:
                print('-'*30,'404')
                return None
        else:
            print('None response')
            return None

    def getUPInfo(self,uid:int):
        info={}
        try:
            url=f'https://workers.meta48.live/api/bilibili/user-info/{uid}'
            #response1=self.request_dom(url,use_other_cookie=True)
            #response1=response1.json()['card']

            response1=getUserInfo(387636363)['card']

            info['name']=response1['name']
            info['fans']=response1['fans']
            info['coins']=response1['coins']
            info['attention']=response1['attention']
            
            url2=f'https://workers.meta48.live/api/bilibili/live-guards/{uid}'
            #response2=self.request_dom(url2,use_other_cookie=True)
            #captains=response2.json()['data']['info']['num']
            captains=getCaptainInfo(387636363)['data']['info']['num']

            info['captains']=captains

            captains_his=getCaptainHistory(387636363)

            info['captains_1d']=info['captains']-captains_his[-1]['guardNum']
        # except (KeyError,TypeError):
        except Exception:
            print(response1)
            print('unable to get up info')
            raise
        return info

    def searchVideoFromDynamics(self,uid:int,aid:str):
        '''
            return number of pages
            return None if error
        '''
        url=f'https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?host_mid={uid}'
        try:
            response = self.request_dom(url=url)
            response=response.json()

            items=response['data']['items'] 
            
            for item in items:
                comment_type=item['basic']['comment_type']
                if comment_type!=1:
                    continue
                if item['basic']['comment_id_str']==aid:
                    return item
        except (KeyError,TypeError):
            print(response)
            raise
            # print('searchVideoFromDynamics Failed')


if __name__=='__main__':
    engine=SearchEngine()
    print(engine.getUPInfo(387636363))
