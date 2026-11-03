# 三月七·存护公式服／四分 BJD

- 当前工作：完整存护服装的分层外形、全尺寸衣片试版，已附各层和逐片花纹定位看稿。
- 造型：原始存护造型／公式服。
- 目标娃体：UFdoll 四分囡囡体 S 胸（用户指定）；品牌发布记录已核对，实物版本与尺寸待复核。
- 制作条件：可关节活动的四分 BJD；胸型固定为 S 胸。
- 当前交付：完整衣片 v0.2、带花纹看稿 v0.3、分层前后与合穿图、逐片尺寸、1:1 黑白 PDF／SVG 与组装说明；采用标明依据的试版尺寸，尚未试穿。原彩色纹样源稿仍保留在 fabric-print/。
- 历史辅助产物：官方立绘／动作参考、官方 PMX 参考模型、基础试坯 A4 PDF／SVG／参数与检查记录；旧基础版保留为历史记录，新完整衣片在 garment-pattern/，尚无实物验证。

## 制作目标

把公式服可见的配色、渐变、边饰和定位纹样画成可编辑的布料印花图。当前 400 × 500 mm 是纹样排版画布，不是娃衣尺码或最终用布量；后续按实际衣片安排花型位置、布纹方向、缝合与折边范围，再做生产排版。

官方 PMX 模型和贴图用于核对图案与部位关系，不直接把游戏 UV 整图当作实体服装印花。对参考中看不清的细节保留待确认说明。

用户可以缝纫、缠花并使用自有 3D 打印机。服装主体优先采用布料制作；配饰按参考效果、安装与重量，在缠花、打印或组合工艺之间选择。具体部件清单待官方参考拆解后确定。

## 完整服装试版

- **[带花纹的分层前后外形](garment-pattern/patterned/layers-overview.png)** · **[带花纹的全套衣片尺寸图](garment-pattern/patterned/pieces-overview.png)**
- [1:1 PDF、逐片 SVG、参数与组装说明](garment-pattern/) · [两套可视化打版册](../../../docs/garment-guide.html)
- 新衣片有完整外轮廓和工艺线，尺寸为试版设计值；实测输入、假设、松量分别登记。原 fabric-print 的尺寸仍是纹样画布尺寸，勿混用。

## 文件导航

- **[彩色布料印花目录](fabric-print/)**
- [整版尺寸标注图](fabric-print/dimensions-overview-v0.1.png) · [逐块宽高尺寸图](fabric-print/dimensions-components-v0.1.png)（单位 mm，现有纹样画布尺寸）
- [按部位选布与具体来源](bill-of-materials.md) · [图案到面料的分组表](fabric-print/fabric-plan.json) · [通用选材与国内询样入口](../../../docs/fabric-selection.md)
- [SVG 印花母版：preservation-print-master-v0.1](fabric-print/preservation-print-master-v0.1.svg)
- [300 ppi PNG](fabric-print/preservation-print-master-v0.1-300ppi.png) · [300 ppi TIFF](fabric-print/preservation-print-master-v0.1-300ppi.tiff) · [1:1 PDF](fabric-print/preservation-print-master-v0.1-1to1.pdf)
- [印花文件、尺寸与导出清单](fabric-print/manifest.json)
- [纹样对应说明](fabric-print/mapping.md)
- [拼接与背部魔术贴规划](../../../docs/seams-and-back-closure.md) · [本项目拼接清单](fabric-print/sewing-plan.json)
- [交给厂家的说明与打样要求](../../../docs/fabric-print-handoff.md)
- [服装观察与分件方案](costume-analysis.md)
- [历史辅助：中文试坯制作说明](sewing-guide.md)
- [历史辅助：A4 纸样](patterns/muslin-v0.1-draft-a4.pdf)
- [量体表与穿脱条件](measurements.md)
- [参考来源与待确认细节](references.md)
- [材料候选与采购记录](bill-of-materials.md)
- [试坯、改版和制作记录](build-log.md)
- [纸样目录](patterns/README.md)
- [配饰模型目录](models/README.md)
- [通用制作流程](../../../docs/workflow.md)

## 印花交付约定

可编辑 SVG、1:1 PDF、300 ppi sRGB PNG／TIFF；实际文件与尺寸以 `fabric-print/manifest.json` 为准。当前属于纹样打样版，未确认布料、厂家参数与实物颜色，不标记为可直接批量生产的成品版。

生产图仅包含颜色与图案，说明和校对标记单独保存。无需把纹样图印成 A4 纸样；发送厂家时提供画布毫米尺寸，并关闭自动重复、铺满和缩放。

## 里程碑

- [x] 项目范围与目标角色建档
- [x] 官方参考入口登记，注明核验范围
- [ ] 对照公式服确认纹样、颜色与部位对应
- [ ] 选定布料和厂家，确认尺寸、色彩配置与样布
- [ ] 按实际衣片定版定位花型和生产排版
- [ ] 印布打样，记录颜色、线宽与经纬向尺寸变化
- [ ] 完成缝制、配饰试装和成品记录

下一步：先检查彩色纹样稿与官方公式服的对应关系，选布做颜色和细节小样；实际裁片适配作为后续定位印花定版的依据。
