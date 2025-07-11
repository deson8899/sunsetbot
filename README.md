## 这是一个python写的朝霞晚霞预警脚本程序
用户可根据config.yaml文件配置每天查询火烧云的时间和预期质量，最后通过service酱推送到微信
由sunsetbot.top提供接口


## 消息推送
使用server酱推送到微信

注册server酱账号： https://sct.ftqq.com/

注册成功之后获取 sendKey，填入配置文件

免费账号有五次推送机会，对我们来说足够了


## 配置
```yaml
# Server酱微信推送
push:
  enable: true
  sckey: "" #"你的Server酱SCKEY"

schedule:
  city: "广东省-广州"
  send_wechat_test_on_start: false # 是否在启动的时候推送测试通知
  push_error: false # 请求错误是否推送到微信
  # 朝霞
  morning:  
    enable: true
    quality: 0.5 # 质量
    time: ["18:00","23:00"] # 多个时间用英文逗号隔开
    model: ["GFS","EC"] #"GFS","EC"  多个模式用英文逗号隔开
  
  # 晚霞
  evening: 
    enable: true
    quality: 0.5
    time: ["11:00", "16:00"]
    model: ["GFS","EC"] 
```

如果使用docker，请映射config.yaml ```docker-compose.yaml```仅供参考

### Docker命令
打包镜像：
docker build -f .\Dockerfile.txt -t sunsetbot .

查看镜像：
docker image ls

导出镜像：（不要通过镜像id导出，不然导入后看不到导入的镜像）
docker save -o sunsetbot.tar sunsetbot
