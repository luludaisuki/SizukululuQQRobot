# 导入datetime模块和pytz模块
from typing import List
import datetime
import pytz
import requests
import time
from copy import deepcopy

# 定义一个函数，接受一个时间戳参数，返回一个字符串
def timestamp_to_beijing_time(timestamp):
    # 将时间戳转化为datetime对象，注意需要除以1000，因为Python的时间戳是以秒为单位的
    dt = datetime.datetime.fromtimestamp(float(timestamp) / 1000)
    # 将datetime对象转化为北京时间
    dt = dt.astimezone(pytz.timezone("Asia/Shanghai"))
    # 将datetime对象格式化为字符串，格式为"yy:mm:dd"
    return dt.strftime("%y/%m/%d")

def convert_time(time_string):
    # Parse the time string as a datetime object with timezone information
    tz_time = datetime.datetime.fromisoformat(time_string)
    # Convert the timezone time to UTC time by subtracting the timezone offset
    utc_time = tz_time - tz_time.utcoffset()
    # Convert the UTC time to Beijing time by adding 8 hours
    beijing_time = utc_time + datetime.timedelta(hours=8)
    # Format the Beijing time as YY-MM-DD
    return beijing_time.strftime("%y/%m/%d")

def convert_to_beijing_date(time_string):
  # 把时间字符串分割成日期部分和时间部分，以及时差部分
  date_part, time_part_delta_part = time_string.split("T")

  time_part=time_part_delta_part[:-6]
  delta_part=time_part_delta_part[-5:]
  sign=time_part_delta_part[-6]
  # 把日期部分分割成年、月、日
  year, month, day = date_part.split("-")
  # 把时间部分分割成时、分、秒和毫秒
  hour, minute, second_ = time_part.split(":")
  # 把秒和毫秒分割开
  try:
    second, millisecond = second_.split(".")
  except ValueError:
      second=second_
      millisecond=0
  # 把时差部分分割成符号和小时
  delta_hour = delta_part[:2]
  # 把所有的字符串转换为整数
  year = int(year)
  month = int(month)
  day = int(day)
  hour = int(hour)
  minute = int(minute)
  second = int(second)
  millisecond = int(millisecond)
  delta_hour = int(delta_hour,base=10)
  # 根据时差的符号，把时间部分的小时数加上或减去时差的小时数
  if sign == "+":
    hour -= delta_hour
  elif sign == "-":
    hour += delta_hour

  hour=(hour+24)%24
  # 创建一个 datetime 对象，表示 UTC 时间
  utc_time = datetime.datetime(year, month, day, hour, minute, second, millisecond)
  # 创建一个 timedelta 对象，表示北京时间与 UTC 时间的时差，即 +08:00
  beijing_delta = datetime.timedelta(hours=8)
  # 把 UTC 时间加上时差，得到北京时间
  beijing_time = utc_time + beijing_delta
  # 把北京时间转换为年月日格式的字符串，如 "2019-09-17"
  beijing_date = beijing_time.strftime("%Y/%m/%d")
  # 返回北京时间的年月日字符串
  return beijing_date

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

def getFansClub(uid):
    url=f'https://workers.meta48.live/api/bilibili/live-fans-members/{uid}'
    response=request_dom(url)

    return response.json()['data']['num']

def getNewHis(his,keyName):
    his_with_time=[]

    for item in his:
        new_item={k:v for k,v in item.items()}
        new_item['created_at']=timestamp_to_beijing_time(item['time'])

        his_with_time.append(new_item)

    new_his:List[dict]=[]

    for item in his_with_time:
        try:
            n=[i['created_at'] for i in new_his].index(item['created_at'])
            new_his[n][keyName]=item[keyName]
        except ValueError:
            new_his.append(item)

    for i,item in enumerate(new_his):
        if i==0:
            item['rate1']=0

        else:
            item['rate1']=item[keyName]-new_his[i-1][keyName]

    return new_his

def getNewHis2(his,keyName):
    his_with_time=[]

    for item in his:
        new_item={k:v for k,v in item.items()}
        new_item['created_at']=convert_to_beijing_date(item['created_at'])

        his_with_time.append(new_item)

    new_his:List[dict]=[]

    for item in his_with_time:
        try:
            n=[i['created_at'] for i in new_his].index(item['created_at'])
            new_his[n][keyName]=item[keyName]
        except ValueError:
            new_his.append(item)

    for i,item in enumerate(new_his):
        if i==0:
            item['rate1']=0

        else:
            item['rate1']=item[keyName]-new_his[i-1][keyName]

    return new_his

def getDue3DayCaptains(his):
    now=time.time()
    due_time=now-2332800 # 27 days
    due_days=[]

    t=len(his)-1
    while(True):
        if t<0:
            break
        item=his[t]
        if item['time']/1000<=due_time:
            due_days.append(item)
            if len(due_days)>=3:
                break

        t-=1

    num=sum(day['rate1'] for day in due_days if day['rate1']>0)

    return num

def getUPInfo(uid:int):
    info={}
    try:
        response1=getUserInfo(uid)['card']
        info['name']=response1['name']
        info['fans']=response1['fans']
        info['coins']=response1['coins']
        info['attention']=response1['attention']
        
        captains=getCaptainInfo(uid)['data']['info']['num']
        info['captains']=captains

        fans_club=getFansClub(uid)
        info['fclub']=fans_club

        captains_his:List[dict]=getCaptainHistory(uid)
        new_captain_his=getNewHis(captains_his,"guardNum")
        captain_avg=sum([item['guardNum']for item in new_captain_his])/len(new_captain_his)
        captain_in_3_days=getDue3DayCaptains(new_captain_his)
        info['c1d']=new_captain_his[-1]['guardNum']-new_captain_his[-2]['guardNum']
        info['c7d']=new_captain_his[-1]['guardNum']-new_captain_his[-8]['guardNum']
        info['c30d']=new_captain_his[-1]['guardNum']-new_captain_his[-31]['guardNum']
        info['due3day']=captain_in_3_days
        info['cavg']=round(captain_avg)

        fan_his:List[dict]=getFanHistory(uid)
        new_fan_his=getNewHis2(fan_his,"fans")
        info['f1d']=new_fan_his[-1]['rate1']
        info['f7d']=new_fan_his[-1]['fans']-new_fan_his[-8]['fans']
        info['f30d']=new_fan_his[-1]['fans']-new_fan_his[-31]['fans']

    except Exception:
        # print(response1)
        print('unable to get up info')
        raise
    return info

if __name__=='__main__':
    # fan_his:List[dict]=getFanHistory(387636363)
    # new_fan_his=getNewHis2(fan_his,"fans")
    # print(new_fan_his[-100:])
    # for i in range(-100,0):
    #     print(new_fan_his[i])
    print(getUPInfo(387636363)) #


