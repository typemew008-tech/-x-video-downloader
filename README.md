# X Video Downloader

一个简洁的开源 X（Twitter）公开视频提取网页。

## 功能

- 粘贴 X / Twitter 帖子链接
- 自动解析公开视频
- 视频预览
- 多清晰度选择
- MP4 下载
- 手机 Safari / iPhone 适配
- Docker 一键部署

## 本地运行

需要 Python 3.12+、ffmpeg。

```bash
pip install -r requirements.txt
python app.py
```

然后访问：

http://127.0.0.1:8080

## Docker

```bash
docker compose up -d --build
```

然后访问：

http://localhost:8080

如果部署到公网，建议再使用 HTTPS 反向代理（例如 Caddy / Nginx）。

## Safari

手机 Safari 直接访问部署后的 HTTPS 地址即可。iOS 的“下载”行为可能由系统版本决定；浏览器通常会把文件交给下载管理器。

## 注意事项

本项目面向公开内容。请只下载你有权访问和保存的内容，并遵守 X 的服务条款、版权和当地法律。

解析能力依赖 yt-dlp 对 X 当前页面/接口的支持。X 改动其网站后，可能需要更新 yt-dlp：

```bash
pip install -U yt-dlp
```
