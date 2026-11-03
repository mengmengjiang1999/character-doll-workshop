# 角色娃衣与配饰工坊

用于积累各类角色的 BJD 娃衣、棉花娃娃衣服、缠花配饰与 3D 打印配饰：从官方参考、量体、打版到试穿和成品记录。

这是个人非商业制作项目。仓库公开，便于保存和交流制作过程。当前已有可打印的基础试坯纸样和配饰打印试件；尚未完成实物试穿，也不是完整角色服装成品版。

## 现在可以使用的文件

- [囡囡体 S 胸试坯 PDF（A4，4 页）](projects/honkai-star-rail/march-7th-preservation-bjd-1-4/patterns/muslin-v0.1-draft-a4.pdf)：上身、基础裙片、独立袖筒、百褶裙试片；前三页纵向，第四页横向，按 100% 打印并核对 50 mm 方框。
- [纸样源文件与参数](projects/honkai-star-rail/march-7th-preservation-bjd-1-4/patterns/README.md)：SVG、标称／假设／设计参数和接缝检查记录。
- [巡猎四瓣额饰与缝接底座](projects/honkai-star-rail/march-7th-hunt-bandai-sitting-plush/models/README.md)：STL、OpenSCAD、参数化生成器及预览，未实际打印／佩戴。
- [官方存护角色模型下载脚本](tools/download_preservation_reference.py)：从官方活动页所用 CDN 下载并校验 PMX 包，保存到本地忽略目录；附原始使用说明。

官方 MMD 角色模型用于观察衣服结构，不当作目标娃体，也不直接转换为娃衣纸样。两套造型的立绘与动作参考已下载到各项目的 `references/local/images/`。

## 已有能力

- 可以购买布料、针线等材料，具备缝纫能力。
- 具备缠花制作能力，头饰及配饰可按效果选用缠花工艺。
- 有 3D 打印机，可制作硬质配饰及连接底座；机型、打印工艺与现有耗材待登记。
- 可查找官方立绘、视频及公开发布的官方模型作为参考，按具体来源的使用说明记录和使用。

## 首批项目

| 项目 | 目标载体 | 当前状态 |
| --- | --- | --- |
| [三月七·存护公式服](projects/honkai-star-rail/march-7th-preservation-bjd-1-4/README.md) | UFdoll 四分囡囡体 S 胸 | 官方模型已下载；基础试坯 v0.1 已生成，待试穿与角色化 |
| [三月七·巡猎公式服](projects/honkai-star-rail/march-7th-hunt-bandai-sitting-plush/README.md) | 万代一番赏 POTEPOTTE 坐姿三月七 | 官方立绘已下载；额饰试件已生成，娃衣尺寸待测 |

两个项目各自保存量体与纸样，四分规格、角色模型比例和商品标称高度均不能替代目标娃体实测。

## 使用方式

1. 在项目的 `references.md` 中核对造型版本，记录官方来源和缺失视角。
2. 填写 `measurements.md`，确认穿脱方式和目标姿态。
3. 按[制作流程](docs/workflow.md)拆分衣片与配饰，完成低成本试坯和工艺小样。
4. 在 `patterns/` 保存纸样，在 `models/` 保存配饰的可编辑源文件及打印导出件。
5. 将试穿问题、改版和通过的实测记录写入 `build-log.md`，通过后再标记成品版。

## 目录

```text
docs/              通用流程、工具材料与参考资料管理
templates/         新角色／新娃体项目模板
projects/
  honkai-star-rail/
    <角色-造型-娃体>/
      README.md             项目目标、分件计划与进度
      measurements.md       娃体实测与穿脱条件
      references.md         来源、视角、模型及使用说明
      bill-of-materials.md  材料候选与实际消耗
      build-log.md          试坯、改版、打印试装与成品验证
      patterns/             可编辑纸样、打印版和版次说明
      models/               自制配饰源文件、打印导出件和适配说明
```

新项目从[项目模板](templates/project-template.md)开始。材料选择见[工具与材料指南](docs/materials-and-tools.md)。

## 再生成

使用 Python 3.9 或更新版本，安装 `requirements.txt` 后，在仓库根目录执行：

```sh
python3 tools/download_preservation_reference.py  # 下载并校验官方模型，存本地忽略目录
python3 tools/render_pmx_reference.py             # 用模型生成本地四视图参考
python3 tools/generate_patterns.py                # 根据参数重建试坯 PDF / SVG
python3 tools/generate_accessories.py --preview  # 重建额饰、底座与预览
```

具体模型来源、下载状态和本地文件位置见[模型获取记录](docs/model-download-report.md)。

## 参考素材与公开文件

参考图、视频和官方模型的原始文件可保存在各项目的 `references/local/`，该目录默认不提交。公开仓库先记录来源链接、观察笔记和自主制作文件；官方模型发布页及使用说明需逐项核对，参考模型不直接视为可打印成品。

本仓库暂未设置统一开源许可证；第三方素材沿用其原始使用条件。详细记录方式见[参考资料管理](docs/references.md)。
