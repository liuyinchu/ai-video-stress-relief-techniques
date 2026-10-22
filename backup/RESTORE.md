# 完整工程恢复说明

下载入口：https://github.com/liuyinchu/ai-video-stress-relief-techniques/releases/tag/v1.0.0

## 备份包含什么

`complete-project-20261022.tar.zst` 保存了从远端完整同步的制作目录，包含 `.git`、全部旧版成片、最新 4K60 与 1080p30 成片、原始旁白、最终混音、配乐音效、脚本、参考资料、关键帧、日志、依赖和虚拟环境。目录内的符号链接保持原样，未将链接指向的系统文件复制进工程。

快照原始提交：`06d2e1a1101168f50fea6a923826c8a545ab7f98`。

正式上线新增的网站与备份脚本位于 Git 的 `main` 分支。两者合起来构成本项目的完整交付。

## 下载与逐项验证

准备 `zstd` 和 Python 3。先克隆本仓库，取得验证脚本和清单，再从 Release 下载完整快照。

```sh
git clone https://github.com/liuyinchu/ai-video-stress-relief-techniques.git source
curl --fail --location --retry 3 \
  https://github.com/liuyinchu/ai-video-stress-relief-techniques/releases/download/v1.0.0/complete-project-20261022.tar.zst \
  --output complete-project-20261022.tar.zst
python3 source/scripts/verify-backup.py \
  complete-project-20261022.tar.zst source/backup/MANIFEST.json
```

验证成功应显示 `verified: true`、`entries: 6607` 和 `regular_file_bytes: 2205073739`。归档 SHA-256 应为：

```text
1889b7e93c714c5a3c68d9260f8dddc812c0353d1892d060bd09b99ee5df14e5
```

MANIFEST.json 的 SHA-256：

```text
1f272f8b9c4d7910bb9f5c816c5519f6eee0e471bcb6b6f71f2613dad1ef8809
```

## 恢复制作目录和上线更新

在没有同名 `project/` 目录的位置解压：

```sh
zstd -dc complete-project-20261022.tar.zst | tar -xf -
cd project
git remote add origin https://github.com/liuyinchu/ai-video-stress-relief-techniques.git
git fetch origin
git merge --ff-only origin/main
```

这会保留快照中的全部制作素材，同时取回后来新增的正式网站、备份工具和交付记录。若只需要影片，可直接下载 Release 中单独提供的 `stress-relief-4k60.mp4`。

## 运行环境

原制作环境为 macOS Apple Silicon、Node.js 24、Python 3.12，使用 PingFang SC 和 Arial。移到不同路径或机器后，应按锁文件重建虚拟环境、安装依赖和等同字体。`tools/env.sh` 为 Bash 的可迁移环境入口；原 `.tool-env` 保留的是制作机器上的路径。

最新成片仍位于 `longform/onetake/output/`。已确认的四个声音文件位于 `longform/assets/audio/`，请按 `longform/onetake/locked-inputs.json` 核验后再修改。
