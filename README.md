### Docker命令
打包镜像：
docker build -f .\Dockerfile.txt -t sunsetbot .

查看镜像：
docker image ls

导出镜像：（不要通过镜像id导出，不然导入后看不到导入的镜像）
docker save -o sunsetbot.tar sunsetbot
