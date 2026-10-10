---
name: takelemon-site-deploy
description: 摘柠檬官网（www.takelemon.com，纯静态站，源码在 D:\跨境电商项目\06-官网建设\02-网站源代码）的图片/页面改版上线标准流程。当需要给该站换图、更新页面、上传服务器、核验线上一致性时使用。包含宝塔面板 Edge CDP 接管、批量上传清单、缓存指纹同步、线上 md5 核验、以及删除服务器文件的正确做法与全部已知坑。
agent_created: true
---

# 摘柠檬官网改版上线流程

## 一、铁律（每次都必须做）
1. **改完必须报版本号**（vX.Y.Z + 括弧内 1-2 个重点）。
2. **改完立刻交付页面卡片**（present_files 给本地预览 URL），并在正文里写出本地预览地址文本。
3. 本地预览：`cd 02-网站源代码 && python -m http.server 8018 --bind 127.0.0.1`（后台任务，**每轮对话结束易被沙箱回收**，交付前先探测，down 就重启）。
4. 换图后**必须同步更新 HTML 里该图片引用的 `?v=YYYYMMDD` 缓存指纹**，否则浏览器永远拿旧图。
5. 上传后**必须做线上 md5 逐一核验**，别只信上传脚本的「上传成功」。
6. 凭据红线：`tools/baidu_token.txt`、`04-服务器部署/服务器部署记录-*.md` **严禁**放进 `02-网站源代码/`（整站上传公网）。

## 二、环境事实
- 服务器 `101.34.251.44`，宝塔面板 `https://101.34.251.44:8888`（安全入口 `/54522ef3`），站点根 `/www/wwwroot/takelemon.com`。
  ⚠️ 面板端口 2026-09-16 由 **38702 改为 8888**；`start_edge_9223.py` 里的 URL 必须同步写 8888，否则重启后落在死端口上（脚本已更正，2026-09-17）。
- 页面真实图片路径 = **`/assets/img/{hero,people,cases,news,team,logo}/`**（务必以 HTML 里的引用为准）。
- 操作服务器唯一通道 = **Edge CDP 接管**（面板公网直连会被安全入口拦截）。
- ⚠️ **`tools/_edge_bt_ui/`（约 500 MB）是宝塔面板登录会话所在的 Edge profile，任何清理都不得删除**——删了下次操作服务器要重新过验证码登录。虽大但保留。
- `tools/` 目录**只应保留 8 个文件**：`start_edge_9223.py`、`bt_eval_8888.js`、`bt_batch_upload_8888.js`、`baidu_push.py`、`baidu_pushed.txt`、`baidu_token.txt`、`diag_baidu_verify.py`、一份 `upload_manifest_*.json` 格式样例（+ `_edge_bt_ui/`）。多出来的基本都是调试残留，可清。
- 清理时**不要碰** `04-服务器部署/服务器部署记录-*.md`、`02-网站源代码-历史版本/`；浏览器 profile 里只有 `_edge_bt_ui` 有用，其余同名的 `edge-automation`、`_edge_cdp*` 都是死 profile（本次已删约 1.68 GB）。

## 三、操作通道（Edge CDP）
```bash
# 1. 启动（必须以「后台任务」方式跑，脚本会 sleep 保活）
cd 04-服务器部署/tools && python start_edge_9223.py   # run_in_background=true
# 2. 等就绪（约 5-10s）
python -c "import urllib.request,json;op=urllib.request.build_opener(urllib.request.ProxyHandler({}));print(json.load(op.open('http://127.0.0.1:9223/json/version',timeout=5)))"
```
- **批量上传**：`bt_batch_upload_8888.js <manifest.json>`
  ```bash
  cd 04-服务器部署/tools && NODE_PATH="C:/Users/book/.workbuddy/binaries/node/workspace/node_modules" \
    NO_PROXY="127.0.0.1,localhost" "C:/Users/book/.workbuddy/binaries/node/versions/22.22.2-3/node.exe" \
    bt_batch_upload_8888.js upload_manifest_xxx.json
  ```
  ⚠️ 必须带 `NODE_PATH`（puppeteer-core）和 `NO_PROXY`（否则被系统代理劫持成 502）。
- **通用面板 API 执行**：`bt_eval_8888.js <片段.js>`，片段里可直接用 `window.__api(url, opts)`（自动带 x-http-token）。片段**不能用 require/fs**（浏览器环境），末尾用 `return` 返回结果。
- CDP 掉线是常态（窗口被回收）→ 重新 `start_edge_9223.py` 后台拉起即可，profile 里已登录面板。

## 四、上传 manifest 格式（按目录分组，每组一份）
```json
{
  "panelOrigin": "https://101.34.251.44:8888",
  "remoteDir": "/www/wwwroot/takelemon.com/assets/img/people",
  "siteBase": "https://www.takelemon.com",
  "files": [{"local": "D:\\...\\02-网站源代码\\assets\\img\\people\\x.jpg", "name": "x.jpg"}],
  "verify": ["https://www.takelemon.com/assets/img/people/x.jpg"]
}
```
- `remoteDir` 是**目标目录绝对路径**；所有文件都落到这一个目录 → 跨目录必须拆多份清单。
- 生成 manifest 用 Python 脚本（写成 .py 文件跑，别塞进 `python -c`，Windows 下反斜杠转义会被 shell 吃掉）。
- `name` 用 `f.rsplit('/', 1)[-1]` 取，`[-1]` 而非 `[1]`——否则根目录文件（无 `/`）报 IndexError。

## 五、换图标准六步
1. **候选生成**：ImageGen，`quality: medium/low` 出候选（省积分），尺寸尽量 `2048x1152`（留水印裁剪余量）；prompt 必带「宽幅横幅构图，主体正中偏上，四周留裁剪余量」+ 风格锚定词（真实摄影·手机随手拍·自然光·轻微噪点·纪实·无文字无水印）。成品交付给用户挑选时压缩到 ≤300KB 放同一文件夹。
2. **精修**：用户选定后，用选中原图做图生图 `input_fidelity: high`、`quality: high`，prompt「保持画面内容、构图、人物完全不变，仅提升质感」。
3. **配对**（重要）：并行 ImageGen 返回的文件名是提示词前缀+时间戳，**不带图位信息**，且**同一秒完成会同名互相覆盖**（丢图）。→ 用 dHash 全排列最优匹配精修图与候选原图的对应关系（脚本见参考），匹配后立即重命名为 `<图位>.png`。
4. **裁剪**：统一「先裁掉底部 5~5.5% 的 AI 水印带 → 按目标比例中心裁剪 → 缩放到目标尺寸 → 存 JPEG q88 optimize progressive」。
   - 各图位目标尺寸：通栏横幅（people-band / db-bg）**1920×800 (2.4:1)**；案例卡 1200×900 (4:3)；文章头图 1200×514 (21:9)；og 图 1200×630。
5. **本地替换**：旧图先备份到 `01-设计与素材/换图候选-<日期>/img-backup-*/`；再更新 HTML 指纹 `?v=YYYYMMDD`（用正则只改被换图片的引用，别全站乱改）。
6. **上传 + 核验**：分目录清单上传（**图片传 `/assets/img/...` 真实路径！**）+ HTML 按目录分组上传 → 线上 md5 逐一比对本地。

## 六、已知坑（都踩过）
| 坑 | 现象 | 对策 |
|---|---|---|
| **图片传错目录** | 页面图不更新，但上传脚本报「上传成功」、md5 还「一致」（因为它核验的是自己传错了的那个 URL） | 上传前先确认 HTML 里图片引用的真实相对路径；`remoteDir` 必须写 `/www/wwwroot/takelemon.com/assets/img/<子目录>`；核验 URL 用页面引用的那个 |
| 并行 ImageGen 同名覆盖 | 返回 N 个路径但文件夹里只有 N-1 个文件 | 统一 output_dir + 用 dHash 配对 + 立刻改名 |
| 精修图全黑 | 生成图 18KB 全黑 | 生成后检查文件体积（正常 2.5-3MB）+ 平均亮度，异常就重试（微调 prompt） |
| 换图后浏览器还是旧图 | 服务器已是新图但用户看到旧图 | 缓存指纹 `?v=<日期>`，每次换图同步更新对应引用的 v 参数 |
| `python -c` 内联脚本被 shell 转义搞坏 | SyntaxError / 反斜杠丢失 | 一律写成 .py 文件再执行 |
| NODE_PATH / NO_PROXY 缺失 | 上传脚本报模块找不到 / 502 | 命令前缀带 `NODE_PATH=... NO_PROXY="127.0.0.1,localhost"` |
| shell 无 grep/mv/curl | 批处理管道失败 | 用 Python 脚本替代批处理 |
| CDP 掉线 | `fetch failed` | 重启 start_edge_9223.py（后台） |
| PowerShell `Add-Type` / `schtasks` 被安全策略拦 | 命令被 block | 改用 Python 实现；需要回收站删除时用 `[Microsoft.VisualBasic.FileIO.FileSystem]` 不可用则直接 os.remove（仅限项目内自建临时脚本） |

## 七、删除服务器文件（宝塔面板 API）
1. **先只读列清单**：
   ```
   POST /files?action=GetDirNew   body: path=<绝对路径>&p=1&show_dot=1
   ```
   返回 JSON：`dir[]`（子目录）、`files[]{nm,sz,mt}`。
2. **删除**（走面板回收站，可恢复）：
   ```
   POST /files?action=DeleteFile  body: path=<绝对路径>
   ```
   返回 `{"status":true,"msg":"已将文件移动到回收站!"}`。目录也适用（空目录可删）。
3. ⚠️ 只删确认无引用的文件；同目录里的正常文件（如 `/cases/*.html` 是案例页）绝不能误删。删完用 HTTP 复查：被删路径应 404、页面引用的正确路径应 200 且与本地大小一致。

## 八、收尾
- 记录：MEMORY.md 更新当前版本行；`.workbuddy/memory/YYYY-MM-DD.md` 追加当日条目（版本号、改了哪些文件、坑）。
- 临时脚本用完即清，别留在 `02-网站源代码/`（会被一起上传公网）。
- 项目内清理（用户说"可以清理了"时）：按第二节的白名单保留 `tools/` 与 `05-质量检查/` 的核心脚本，其余一次性脚本/调试截图/死 Edge profile 全删；**删前先 grep 确认无脚本引用**，删后必须重启 Edge CDP 并实测面板仍在登录态（`bt_eval_8888.js` 返回 `loggedIn:true`）才算通过。清理报告存 `05-质量检查/磁盘清理报告-<日期>.md`（+docx）。
