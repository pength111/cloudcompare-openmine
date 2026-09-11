# CloudCompare 露天矿山边坡标注工具集

基于 [CloudCompare](https://www.cloudcompare.org/) Python API（`pycc`）开发的露天矿山点云地质特征标注与提取工具集。

## 功能概述

本项目包含 8 个独立运行的 CloudCompare 插件脚本，用于露天矿山点云数据的自动化标注、缓冲区提取和示坡线生成。

### 标注工具（Label 赋值）

| 文件 | Label 值 | 含义 | 说明 |
|------|----------|------|------|
| `label0.py` | 0 | 平盘（台阶平台） | 将所有点标注为平盘 |
| `label1.py` | 1 | 片帮（边坡壁） | 将所有点标注为片帮 |
| `label2ding.py` | 2 | 坡顶线 | 将所有点标注为坡顶线 |
| `label3di.py` | 3 | 坡底线 | 将所有点标注为坡底线 |
| `label4road.py` | 4 | 道路 | 将所有点标注为道路 |

### 分析工具

| 文件 | 功能 |
|------|------|
| `buffer.py` | 基于 KD-Tree + DBSCAN 提取平盘与片帮之间的缓冲区，分离独立缓冲区点云，并从原始数据中剔除缓冲区 |
| `slope_rec.py` | `buffer.py` 的增强版，额外保留原始 RGB 颜色信息 |
| `pomianxian.py` | 基于坡顶线（Label=2）和坡底线（Label=3）自动生成示坡线（连接线） |

## Label 分类体系

```
Label 0 — 平盘（台阶平台 / Bench）
Label 1 — 片帮（边坡壁 / Slope face）
Label 2 — 坡顶线（Crest line）
Label 3 — 坡底线（Toe line）
Label 4 — 道路（Road）
```

## 依赖环境

### Python 库

```bash
pip install -r requirements.txt
```

依赖项：
- **numpy** — 数组运算
- **scipy** — KD-Tree 空间近邻查询
- **scikit-learn** — DBSCAN 聚类

### CloudCompare

本工具集依赖于 CloudCompare 的内置 Python 运行时（`pycc` 模块）。请确保：

1. 安装 [CloudCompare](https://www.cloudcompare.org/)（建议 2.12 或更高版本）
2. CloudCompare 自带 Python 3.x 环境，`pycc` 在其内置环境中可用

## 使用方法

1. 在 CloudCompare 中打开点云数据
2. 在左侧目录树中选中目标点云
3. 菜单栏：**File → Python Script**（或使用内置 Python 控制台）
4. 选择对应的 `.py` 脚本文件运行

### 典型工作流程

```
1. 导入原始点云
2. 运行 label0.py → 全部标注为平盘
3. 手动或自动标注片帮区域 → 运行 label1.py
4. 运行 buffer.py 或 slope_rec.py → 提取缓冲区
5. （可选）标注坡顶/底线 → 运行 pomianxian.py 生成示坡线
```

## 核心算法说明

### 缓冲区提取（buffer.py / slope_rec.py）

1. **KD-Tree 空间查询**：以片帮点（Label=1）构建 KD-Tree，搜索每个平盘点（Label=0）在 2m 半径内是否有片帮点
2. **DBSCAN 聚类**：将符合条件的缓冲区点进行密度聚类，分离为独立的缓冲区簇
3. **点云分离**：每个簇导出为独立点云，同时生成剔除缓冲区后的剩余点云

### 示坡线生成（pomianxian.py）

1. 分别提取坡顶点（Label=2）和坡底点（Label=3）
2. 以坡底点构建 KD-Tree
3. 对每个坡顶点（步长=20），查询最近的坡底点
4. 距离 ≤ 30m 则连接生成 Polyline

## 参数配置

各脚本内均有参数设置区域，可根据实际数据调整：

- `buffer.py` / `slope_rec.py`：`SEARCH_RADIUS`（搜索半径，默认 2m）、`DBSCAN_EPS`（聚类半径，默认 3）、`DBSCAN_MIN_SAMPLES`（最小样本数）
- `pomianxian.py`：`STEP`（采样步长，默认 20）、`MAX_DISTANCE`（最大连接距离，默认 30m）

## 注意事项

- 所有脚本在 CloudCompare 内运行，无法独立在外部 Python 环境中执行
- 脚本执行后会在 CloudCompare 数据库（DB Tree）中生成新的点云实体
- 原始点云在处理后会被隐藏（`setEnabled(False)`），可在左侧目录树中重新显示

## 配套仓库

本工具集负责 OpenMine 露天矿点云处理流程中的**人工标注环节**（给点云赋 Label、
提取缓冲区、生成示坡线）。自动化的主流程 —— 平台坡面分割、坡顶坡底线提取、
示坡线自动生成 —— 跑在常规 Python 环境里，在另一个仓库：

- [pength111/Open-pit](https://github.com/pength111/Open-pit)

**为什么必须分成两个仓库：** 本仓库的脚本全部 `import pycc`，该模块只存在于
CloudCompare 自带的 Python 解释器中，常规 Python 环境无法导入；反过来，主流程
依赖 open3d / scipy / scikit-learn，也不在 CloudCompare 的内置环境里。两边的
依赖和运行方式没有交集，因此各自独立成库、各自维护 `requirements.txt`。

主流程在需要人工修剪的位置会停下来提示，此时回到本工具集操作，处理完再把结果
交回主流程。

## License

MIT License
