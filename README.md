# 蓝色大肥鱼桌宠 · Blue Whale Desktop Pet

一个会在桌面右侧散步、讨一口白米饭，并陪你庆祝 SCI 的小桌宠。

![桌宠预览](docs/preview.png)

## 能做什么

- 小范围来回散步，脚交替抬起、落地，到边界转身。
- 每完成五次完整往返，原地转一圈，再继续走。
- 鼠标悬停：停下、转正、眨眼，显示 **“好棒主人，我们一起又中了一篇SCI。”**
- 鼠标移开后恢复散步，保留往返计数。
- 键鼠闲置 10 分钟后，坐地哭哭讨饭。
- 点击喂一口虚拟白米饭，随后戴墨镜得意 15 秒。不会消耗模型 token。
- 右键可喂饭、预览讨饭、开关散步、调整大小或退出。
- 透明背景、高分屏原生像素绘制。当前版本已移除跳舞和龙女追逐。

## 运行环境

桌面程序面向 Windows。开发验证环境为 Windows 11、Python 3.13、200% 屏幕缩放。
程序不需要 API key，不连接模型服务；闲置检测只读取最后一次键鼠输入距今的时间。

## 从源码运行

在项目目录打开 PowerShell，执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m blue_whale_pet
```

也可以在已安装依赖的环境运行 `blue-whale-pet`。

## 打包成 EXE

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean blue_whale_pet.spec
```

生成文件：`dist/BlueWhalePet.exe`。双击即可运行，无需另外安装 Python。
首次运行会解压打包资源，可能稍有等待。重复启动会复用单实例限制，避免出现多只桌宠。
仓库只提交源码和必要素材；EXE 可作为 GitHub Release 附件提供。

## 检查

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

检查涵盖脚步支撑、五次往返转圈、悬停转身、眨眼、喂饭计时和高分屏像素命中。
GitHub Actions 在 Windows 上运行检查并打包可下载的 EXE artifact。

## 项目结构

```text
src/blue_whale_pet/
  app.py          窗口、鼠标交互和主循环
  logic.py        讨饭与喂饭计时
  patrol.py       脚步、转向和往返计数
  hover.py        悬停转正与眨眼
  render.py       分层表情绘制
  walk_render.py  方向素材与腿部关节绘制
  assets/         运行所需的透明图片
tests/            行为与显示回归检查
blue_whale_pet.spec  Windows 打包配置
```

## 小提示

默认身高 150 个物理像素。活动区是屏幕工作区最右侧约 22%，且宽度最多 540 像素；这是固定区域，不会识别其他软件的按钮。可在 `logic.py` 的 `lane_bounds` 中调整。
支持悬停祝贺的是正常散步状态；喂饭和戴墨镜期间会先完成当前互动。

## 素材与许可

角色和图片生成说明见 [docs/artwork.md](docs/artwork.md)。这是非官方同人项目。
目前尚未指定开源许可证。公开分享仓库前，作者可以自行选择代码许可，并单独注明素材的使用条件。
