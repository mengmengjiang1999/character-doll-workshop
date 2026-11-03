# 三月七角色模型参考：下载与检查记录

日期：2026-11-03。目的：观察角色服装正背面、衣层关系、饰品位置与纹样，辅助娃衣设计。

## 已下载：存护三月七

- 发布页：[《崩坏：星穹铁道》跃迁特别招募](https://www.bilibili.com/blackboard/activity-Hk1xELkY1x.html)。页面源码中的模型下载轮播将三月七预览图关联到以下 ZIP，已经目视核对人物。
- 文件：[官方 B站 CDN 模型包](https://activity.hdslb.com/blackboard/static/20221205/d7f098333308ba7412aa9b57601bfa1d/KkVjYLh8y3.zip)。
- 文件大小：3,655,358 bytes；ZIP CRC 检查通过。
- ZIP SHA-256：`4256b27d90175166460d6ef31d23b3e0ea163d351ad25881a90d87f4d7c41483`。
- 内容：角色 `三月七 1.0.pmx`、弓与箭 PMX、10 张贴图、`使用规则.txt`；主角色引用其中 9 张贴图。
- 格式：官方公开配布的 MMD/PMX 参考模型，不是从本机游戏客户端提取的游戏原始资源。
- 署名：模型编辑「神帝宇」，模型版权 miHoYo；随包说明已读取并原样留存在本地，含非商业用途、不可二次配布等条件。

文件保存在以下本地目录，已经被 Git 忽略：

```text
projects/honkai-star-rail/march-7th-preservation-bjd-1-4/
  references/local/official-models/
    march-7th-preservation-official.zip
    official-release-page.html
    official-release-preview.jpg
    download-manifest.json
    model-metadata.json
    extracted/星穹铁道—三月七/
    rendered/
      front.png
      back.png
      left.png
      right.png
      four-views.png
      render_pmx_reference.py
```

解包时按 ZIP 标记处理编码：有 UTF-8 标记的文件名直接使用，其他文件名以原始 CP437 字节还原 GBK 中文。`使用规则.txt` 自身为带 BOM 的 UTF-8。

## 模型数字检查与四视图

- 主角色文件为 PMX 2.0，文本编码 UTF-16LE；21,218 顶点、28,039 三角形、30 个材质分组。
- 主 PMX SHA-256：`942aef2af3a465e77c1569369b3c422fdf64f8494cbdf3b529a88c3cc66c13dc`。
- 与衣服相关的分组包括：衣服、袖子／袖子1／袖子2、手套、腿环、鞋子／鞋饰、衣饰／衣饰1／衣饰铁、腰饰、腰带、相机、背饰／背饰1、头饰、脖饰。
- 已使用模型顶点、面、材质与 UV 贴图生成正、背、左、右正投影视图；输出已目视检查，UV 超出 0–1 的部分按重复纹理处理。
- 四视图是本地无光照贴图观察图，没有复现游戏着色器、物理、表情或动作。可用于观察轮廓和位置，最终颜色仍对照官方立绘与实物样片。
- 模型材质分组不是服装裁片；模型单位也不代表囡囡体尺寸。纸样另按目标娃体数据设计。

## 巡猎三月七：已定位官方模型，下载等待正常登录

- 精确发布页：[【崩坏：星穹铁道】三月七·巡猎](https://www.aplaybox.com/details/model/KG9eRZVCtc9y)。
- 已读取公开作品详情：发布账号认证为「崩坏：星穹铁道官方账号」，发布日期 2024-07-31，模型编辑「流云景」，格式 MMD，版权 miHoYo。
- 正常下载按钮会先检查用户登录；当前没有可用的已登录下载会话，未下载巡猎 PMX，未尝试绕过登录。
- [2.4 版本官方创作页](https://www.bilibili.com/blackboard/era/RIKeTYdKtVJHEdpJ.html)的公开下载列表未找到巡猎三月七，未采用非官方转存包替代。
- 已下载该官方模型页的[立绘封面](https://oss.aplaybox.com/uploads/works/covers/20240731/f19b3a8bc7b71a4bdbe43742a9fd5571.jpg)，保存为巡猎项目 `references/local/official-models/official-model-cover.jpg`；公开详情与 2.4 活动页存档同目录保存。
- 后续正常登录后可从上述精确发布页下载，保留随包说明并补充哈希；当前仍可使用已保存立绘推进服装结构拆解。

原始模型、贴图、参考立绘和本地四视图不随公开仓库提交；仓库保存来源、校验值和自主制作文件。
