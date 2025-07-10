import json
import requests
import schedule
import time
import datetime
import urllib.parse
import yaml
import os
import random
import re


EVENT_MAP = {
    'TODAY_MORNING': 'rise_1',
    'TOMORROW_MORNING': 'rise_2',
    'TODAY_EVENING': 'set_1',
    'TOMORROW_EVENING': 'set_2',
}

# 预测模型
PREDICT_MODEL_MAP = {
    'GFS' : 'GFS',
    'EC' : 'EC'
}


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

CONFIG = load_config()

def build_url(event, model):
    base_url = CONFIG["request"]["base_url"]
    # params = CONFIG["request"]["params"]
    # params_encoded = {k: v if v is not None else '' for k, v in params.items()}
    params_encoded = {}
    params_encoded["query_id"] = randomNum()
    params_encoded["event"] = event
    # params_encoded["model"] = PREDICT_MODEL_MAP.get("GFS")
    params_encoded["model"] = model
    params_encoded["query_city"] = CONFIG["schedule"]["city"]
    params_encoded["intend"] = "select_city"
    params_encoded["event_date"] = "None"
    params_encoded["times"] = "None"
    print(f"params: {params_encoded}")
    query_string = urllib.parse.urlencode(params_encoded)
    return f"{base_url}?{query_string}"

def fetch_data(is_morning):
    target_quality = ""
    urls = {} # url -> model
    
    if is_morning:
        models = CONFIG["schedule"]["morning"]["model"]
        if models is None or len(models) < 1:
            models = [PREDICT_MODEL_MAP.get("GFS")]
        
        for model in list(models):
            # 当前时间小于6点，当天朝霞也请求
            if datetime.datetime.now().hour < 6:
                url1 = build_url(EVENT_MAP.get("TODAY_MORNING"), model)
                # urls.append(url1)
                urls[url1] = model
        
            url2 = build_url(EVENT_MAP['TOMORROW_MORNING'], model)
            # urls.append(url2)
            urls[url2] = model
        target_quality = CONFIG["schedule"]["morning"]["quality"]
        
    else:
        models = CONFIG["schedule"]["evening"]["model"]
        if models is None or len(models) < 1:
            models = [PREDICT_MODEL_MAP.get("GFS")]
        for model in list(models):  
            url1 = build_url(EVENT_MAP['TODAY_EVENING'], model)
            urls[url1] = model

            url2 = build_url(EVENT_MAP['TOMORROW_EVENING'], model) 
            urls[url2] = model
        target_quality = CONFIG["schedule"]["evening"]["quality"]
    
    eventStr = ''
    if is_morning:
        eventStr += "[朝霞]\n"
    else:
        eventStr += "[晚霞]\n"

    pushStr = ""
    allUrl = urls.keys()
    for url in allUrl:
        value = requestUrl(url, target_quality)
        if len(value) > 0:
            if is_morning:
                pushStr += eventStr
            else:
                pushStr += eventStr
            pushStr += value
            pushStr += f"模式：{urls[url]}\n\n"


    print(f"[{datetime.datetime.now()}] 请求地址: {url}")
    if len(pushStr) > 0:
        send_wechat_notification(eventStr, pushStr)

def requestUrl(url, target_quality):
    # print(f"[{datetime.datetime.now()}] 请求地址: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        content = response.text
        json_content = json.loads(content)
        
        print(f"请求地址: {url}\n[成功] 获取数据: {content}")
      
      
        numberPattern = r'\d+\.\d+'
        quality = json_content['tb_quality'] # 概率(质量)
        
        qualityNum = re.findall(numberPattern,  str(quality))[0]
  
        pushStr = ""
        if float(qualityNum) >= float(target_quality):
            pushStr += f"鲜艳度：{quality}\n"
            pushStr += f"气溶胶：{json_content['tb_aod']}\n"
            time = json_content['tb_event_time']
            
            day = ""
            if len(time) > 0:
                todayStr = datetime.date.today()
                if str(time)[:10] == todayStr:
                    day = '(今天)'
                else:
                    day = '(明天)'
            pushStr += f"时间{day}：{json_content['tb_event_time']}\n"
            print(f"pushStr: {pushStr}")
            # send_wechat_notification("数据请求成功", content[:3000])

        print(f"数据组装成功: {pushStr}")
        return pushStr
    except Exception as e:
        print(f"请求地址: {url}\n[失败] 请求异常: {e}")
        return "[失败] 请求地址: {url}\n"
        # send_wechat_notification("数据请求失败", str(e))




# 通过service酱推送到微信
def send_wechat_notification(title, content):
    push_enable = CONFIG["push"]["enable"]

    if push_enable == False:
        print(f"[推送已关闭]")
        return

    print(f"[推送] title: {title}  内容：{content}")
    sckey = CONFIG["push"]["sckey"]
    api = f"https://sctapi.ftqq.com/{sckey}.send"
    data = {
        "title": title,
        "desp": content
    }
    try:
        res = requests.post(api, data=data)
        res.raise_for_status()
        print(f"[推送成功] 微信通知已发送")
    except Exception as e:
        print(f"[推送失败] {e}")


# 生产6位随机数
def randomNum():
    str = ""
    for i in range(6):
        ch = chr(random.randrange(ord('0'), ord('9') + 1))
        str += ch
    return str

def main():

    print(f"[启动] {datetime.datetime.now()}")
   
    push_enable = CONFIG["push"]["enable"]

    send_wechat_test_on_start = CONFIG["schedule"]["send_wechat_test_on_start"]
    morning_task_enable = CONFIG["schedule"]["morning"]["enable"]
    morning_run_time = CONFIG["schedule"]["morning"]["time"]
    
    
    # 早霞任务
    if morning_task_enable and len(morning_run_time) > 0:
        for run_time in list(morning_run_time):
            print(f"[启动] 朝霞任务将每天 {run_time} 执行")
            schedule.every().day.at(str(run_time).strip()).do(fetch_data, True)
    
    # 晚霞任务
    evening_task_enable = CONFIG["schedule"]["evening"]["enable"]
    evening_run_time = CONFIG["schedule"]["evening"]["time"]
    if evening_task_enable and len(evening_run_time) > 0:
        for run_time in list(evening_run_time):
            print(f"[启动] 晚霞任务将每天 {run_time} 执行")
            schedule.every().day.at(str(run_time).strip()).do(fetch_data, False)

    print(f"[启动] 朝霞任务：{morning_task_enable} 晚霞任务：{evening_task_enable}  微信通知: {push_enable}")

    # 发送测试微信推送
    if send_wechat_test_on_start:
        send_wechat_notification("Test", "服务启动，这是一条测试消息")


    while True:
        schedule.run_pending()
        time.sleep(1)

    # fetch_data(True)

if __name__ == "__main__":
    main()
