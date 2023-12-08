# from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright,Page,expect
import json
import asyncio
import os.path


def loadDataFromDict(data:dict,soup:BeautifulSoup=None,save_path='htmls/out.html'):
    if soup is None:
        with open('htmls/mydynamic2.html','r') as f:
            markup=f.read()
        soup=BeautifulSoup(markup,'lxml')
        
    avatar_img=soup.select('#app > div > div > div > div > div.bili-dyn-item__avatar > div > div > div > div > div > div > picture > img')[0]

    name=soup.select('#app > div > div > div > div > div.bili-dyn-item__header > div.bili-dyn-title > span')[0]

    desc=soup.select('#app > div > div > div > div > div.bili-dyn-item__header > div.bili-dyn-item__desc > div')[0]

    # video_dyn_desc=soup.select('#app > div > div > div > div > div.bili-dyn-item__body > div > div > div.bili-dyn-content__orig__desc > div > div > span')[0]

    video_img=soup.select('#app > div > div > div > div > div.bili-dyn-item__body > div > div > div.bili-dyn-content__orig__major.suit-video-card.gap > a > div.bili-dyn-card-video__header > div > div.b-img > picture > img')[0]

    duration=soup.select('#app > div > div > div > div > div.bili-dyn-item__body > div > div > div.bili-dyn-content__orig__major.suit-video-card.gap > a > div.bili-dyn-card-video__header > div > div.bili-dyn-card-video__cover-shadow > div')[0]

    title=soup.select('#app > div > div > div > div > div.bili-dyn-item__body > div > div > div.bili-dyn-content__orig__major.suit-video-card.gap > a > div.bili-dyn-card-video__body > div.bili-dyn-card-video__title.bili-ellipsis.fs-medium')[0]

    video_desc=soup.select('#app > div > div > div > div > div.bili-dyn-item__body > div > div > div.bili-dyn-content__orig__major.suit-video-card.gap > a > div.bili-dyn-card-video__body > div.bili-dyn-card-video__desc.bili-ellipsis.fs-small')[0]

    play=soup.select('#app > div > div > div > div > div.bili-dyn-item__body > div > div > div.bili-dyn-content__orig__major.suit-video-card.gap > a > div.bili-dyn-card-video__body > div.bili-dyn-card-video__stat.fs-small > div:nth-child(1) > span')[0]

    danmaku=soup.select('#app > div > div > div > div > div.bili-dyn-item__body > div > div > div.bili-dyn-content__orig__major.suit-video-card.gap > a > div.bili-dyn-card-video__body > div.bili-dyn-card-video__stat.fs-small > div.bili-dyn-card-video__stat__item.danmaku > span')[0]
    
    author_name=data['modules']['module_author']['name']
    avatar=data['modules']['module_author']['avatar']['fallback_layers']['layers'][0]['resource']['res_image']['image_src']['remote']['url']

    try:
        dyn_desc=data['modules']['module_dynamic']['desc']['text']
    except TypeError:
        dyn_desc=''
    cover=data['modules']['module_dynamic']['major']['archive']['cover']
    video_desc_=data['modules']['module_dynamic']['major']['archive']['desc']
    video_title=data['modules']['module_dynamic']['major']['archive']['title']
    duration_text=data['modules']['module_dynamic']['major']['archive']['duration_text']
    
    play_text=data['modules']['module_dynamic']['major']['archive']['stat']['play']
    danmaku_text=data['modules']['module_dynamic']['major']['archive']['stat']['danmaku']
    
    avatar_img.attrs['src']=avatar
    pubtime=data['modules']['module_author']['pub_time']
    
    # print(author_name)
    # print(avatar)
    # print(cover)
    # print(video_desc_)
    # print(video_title)
    # print(duration_text)
    # print(play_text)
    # print(danmaku_text)
    # print(pubtime)

    name.string=author_name
    desc.string=pubtime
    # video_dyn_desc.string=dyn_desc
    video_img.attrs['src']=cover
    duration.string=duration_text
    title.string=video_title
    video_desc.string=video_desc_
    play.string=play_text
    danmaku.string=danmaku_text
    
    with open(save_path,'w') as f:
        f.write(str(soup))
        
async def getFansAndCaption():
    async with async_playwright() as p:
        browser = await p.webkit.launch()
        page = await browser.new_page()
        await page.goto("https://laplace.live/user/387636363",wait_until='networkidle')
        locator=page.get_by_text('涨跌粉')
        fans=await locator.inner_text()
        
        locator2=page.get_by_text('大航海')
        captions=await locator2.inner_text()
        # await locator.screenshot(path="example.png")
        # await page.screenshot(path="example.png")
        await browser.close()

    return fans,captions

async def get_video_screenshot(dynamic_info:dict):
    loadDataFromDict(dynamic_info)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context=await browser.new_context(device_scale_factor=2)
        with open('robot/bili_cookie.json') as f:
            cookies=json.load(f)
        used_cookies=[]
        for cookie in cookies:
            cookie:dict

            if cookie['secure'] is True:
                continue

            unused_keys=[]
            for key,value in cookie.items():
                if value is None:
                    unused_keys.append(key)
            for key in unused_keys:
                cookie.pop(key)
            
            used_cookies.append(cookie)
                
        await context.add_cookies(used_cookies)
        page = await context.new_page()

        html_path=os.path.realpath('htmls/out.html')
        result=await get_dynamic_screenshot_pc(f'file://{html_path}',page)

        await context.close()
        await browser.close()
    return result

async def get_dynamic_screenshot_pc(url,page: Page,path=None):
    """电脑端动态截图"""
    # await page.set_viewport_size({"width": 2000, "height": 720})
    print(page.viewport_size)
    await page.goto(url, wait_until="networkidle")

    # card = await page.query_selector("#app > div > div > div > div")
    # assert card
    # clip = await card.bounding_box()
    # assert clip
    # print(clip)
    # # return page, clip
    # clip["height"] = min(clip["height"], 32766)

    # return await page.screenshot(clip=clip, full_page=True, type="jpeg", quality=98,path=path)
    
    return await page.locator('#app > div > div > div > div').screenshot(type='jpeg',path=path,quality=98,scale='device')

async def testscreenshot():
    # with sync_playwright() as p:
    #     browser = p.webkit.launch()
    #     page = browser.new_page()
    #     page.goto("https://playwright.dev/")
    #     result=page.screenshot(path="example.png")
    #     browser.close() 
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        await page.goto('https://laplace.live/user/387636363')

        await asyncio.sleep(3)
        
        locator=await page.locator('#__next > div > div:nth-child(8) > main > div.jsx-1561ee057cab7771.Home_scrollableContent__dsn1c.Home_xl__S_3ZI > details:nth-child(3) > summary > span:nth-child(1)')

        await expect(locator).to_have_text()
        print(locator.inner_text()) 

        # print(await context.cookies('https://www.bilibili.com'))
        await browser.close()

    # image=Image.open(io.BytesIO(result))
    # image.save('out.png')
    # return result

async def testGetCaptains():
    # with sync_playwright() as p:
    #     browser = p.webkit.launch()
    #     page = browser.new_page()
    #     page.goto("https://playwright.dev/")
    #     result=page.screenshot(path="example.png")
    #     browser.close() 
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context=await browser.new_context(device_scale_factor=2)
        with open('robot/bili_cookie.json') as f:
            cookies=json.load(f)
            
        used_cookies=[]
        for cookie in cookies:
            cookie:dict

            if cookie['secure'] is True:
                continue

            unused_keys=[]
            for key,value in cookie.items():
                if value is None:
                    unused_keys.append(key)
            for key in unused_keys:
                cookie.pop(key)
            
            used_cookies.append(cookie)
                
                    
        await context.add_cookies(used_cookies)
        page = await browser.new_page()
        # await page.goto("https://www.bilibili.com")
        # result=await page.screenshot(path="screenshot.png", full_page=True)

        # print(await context.cookies('https://www.bilibili.com'))
        await context.close()
        await browser.close()

    # image=Image.open(io.BytesIO(result))
    # image.save('out.png')
    # return result

if __name__=='__main__':
    asyncio.run(testscreenshot())
    # with open('robot/bili_cookie.json') as f:
    #     cookie=json.load(f)
    # print(cookie)
