# 先让身体缓一缓

一部关于压力、身体与日常小动作的中文影片。七个主题在同一空间中连续衔接：双吸长呼、凉意、耳部触感、温和活动、写下烦心事、自然纹理，以及整理一小块桌面。

**[观看影片](https://liuyinchu.github.io/ai-video-stress-relief-techniques/) · [4K 成片与完整工程备份](https://github.com/liuyinchu/ai-video-stress-relief-techniques/releases/tag/v1.0.0)**

## 成片

- 连续镜头长片：400.833333 秒，原生 3840×2160 / 60fps；另有 1920×1080 / 30fps 版。
- 画面：Multiplane 0.3.13 + Three.js 0.180.0，时间驱动的三维模型、连续相机轨迹与线性光运动模糊采样。
- 声音：MiniMax 中文女声、原创程序配乐与音效。连续镜头版直接保留已确认版本的音轨。
- 原有横屏、竖屏短片及前一版长片完整保留在工程快照内。

影片内容为科普与自助体验介绍，各方法的证据强弱不同。[研究依据与表述边界](longform/docs/evidence.md)随项目保留。

## 文件导航

| 内容 | 位置 |
| --- | --- |
| 正式网站 | `site/`；发布到 `gh-pages` 分支根目录 |
| 连续镜头画面与管线 | `longform/onetake/` |
| 长片台本、字幕、动作时序 | `longform/content/` |
| 已生成的原始旁白 | `longform/assets/voice/raw/` |
| 前一版长片源代码 | `longform/shots/` |
| 两种画幅的短片源代码 | `shots/` |
| 配乐、音效与混音程序 | `scripts/`、`longform/scripts/` |
| 完整备份清单、校验与恢复说明 | `backup/` |

## 完整工程备份

Git 保存版本化源代码、制作文档、原始旁白和正式网站。**恢复全部制作文件，请下载 Release 中的 `complete-project-20261022.tar.zst`。** 该快照还包含 `.git` 历史、所有忽略文件、依赖、虚拟环境、全部旧版视频、音轨、渲染日志与关键帧，共 6,607 个文件系统条目、2,205,073,739 字节的普通文件内容。

快照对应制作完成时的提交 `06d2e1a1101168f50fea6a923826c8a545ab7f98`。本次上线新增的网站和备份工具保存在当前 Git 分支中；恢复快照后可快进到当前 `main`。步骤见 **[恢复说明](backup/RESTORE.md)**。

原始快照 SHA-256：

```text
1889b7e93c714c5a3c68d9260f8dddc812c0353d1892d060bd09b99ee5df14e5
```

完整条目清单为 [MANIFEST.json](backup/MANIFEST.json)。`scripts/verify-backup.py` 会逐项验证内容、大小、权限和符号链接，不执行或展开归档中的文件。

完整归档已从 GitHub Release 重新下载并逐项验证，记录见 [下载校验回执](backup/remote-verification.json)；源码和历史的检查见 [Git 校验回执](backup/git-verification.json)。另保留 [通过 Git 分块恢复](backup/GIT-TRANSPORT.md) 的备用方式。只需要源码时，可使用 `git clone --single-branch --branch main`，避免同时拉取完整备份分支。

## 本地预览与制作

正式页面为纯静态 HTML / CSS / JavaScript，直接使用已完成的视频。恢复完整工程后，可以运行：

```sh
python3 longform/scripts/serve_review.py --port 18920
# 浏览器打开 http://127.0.0.1:18920/site/
```

停止预览使用 Ctrl+C。网站通过 GitHub Pages 提供服务，不依赖开发机器或 SSH 转发。

重新渲染的入口见 [连续镜头制作说明](longform/onetake/README.md)。依赖由 `package-lock.json` 与 `requirements.lock` 锁定；跨机器使用时应重新创建虚拟环境并准备等同字体，再执行 Multiplane 的确定性校验。随快照保存的虚拟环境用于完整留档，其绝对路径不保证在另一台机器上直接可用。

## 发布网站

先将网站变更提交到 `main` 并推送，再执行：

```sh
bash scripts/publish-pages.sh
```

脚本仅将提交中的 `site/` 树发布到 `gh-pages`；GitHub Pages 采用该分支的根目录。正式页面不包含工程验收入口或本地服务地址。
