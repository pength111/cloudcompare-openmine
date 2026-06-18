import numpy as np
import pycc
from scipy.spatial import cKDTree

def main():
    CC = pycc.GetInstance()
    entities = CC.getSelectedEntities()
    if not entities:
        print("错误：请先选择一个包含分类Label的点云！")
        return

    cloud = entities[0]
    print(f"正在处理点云: {cloud.getName()}")

    try:
        # 1. 获取点数据
        points = np.array(cloud.points())
        
        # 自动获取分类字段
        sf_obj = None
        curr = cloud.getCurrentOutScalarField()
        if isinstance(curr, int) and curr != -1:
             sf_obj = cloud.getScalarField(curr)
        elif not isinstance(curr, int):
             sf_obj = curr
        
        # 如果没激活，尝试按名字找 "Label"
        if sf_obj is None:
            idx = cloud.getScalarFieldIndexByName("Label")
            if idx != -1: sf_obj = cloud.getScalarField(idx)

        if sf_obj is None:
            print("❌ 未找到分类字段，请先【激活显示】包含分类信息的 Scalar Field")
            return
            
        labels = np.array(sf_obj.asArray())

        # ==========================================
        # 【参数设置】
        # ==========================================
        LABEL_CREST = 2     # 坡顶线 Label 值
        LABEL_TOE = 3       # 坡底线 Label 值
        STEP = 20           # 采样步长 (越大越稀疏)
        MAX_DISTANCE = 30.0 # 最大连接距离
        # ==========================================

        # 2. 提取点集
        crest_mask = (labels == LABEL_CREST)
        crest_points = points[crest_mask]
        
        toe_mask = (labels == LABEL_TOE)
        toe_points = points[toe_mask]
        
        if len(crest_points) == 0:
            print(f"❌ 未找到坡顶线点 (Label={LABEL_CREST})")
            return
        if len(toe_points) == 0:
            print(f"❌ 未找到坡底线点 (Label={LABEL_TOE})")
            return

        print(f"提取到: 坡顶点 {len(crest_points)} 个, 坡底点 {len(toe_points)} 个")
        print("正在计算连接线...")

        # 3. 构建 KD-Tree
        tree = cKDTree(toe_points, leafsize=64)
        
        # 4. 创建组来存放线条
        # 使用 ccHObject 替代 ccCustomHObject
        group = pycc.ccHObject("Slope_Hachures_Group")
        
        count = 0
        
        # 5. 循环生成线条
        for i in range(0, len(crest_points), STEP):
            p_start = crest_points[i]
            dist, idx = tree.query(p_start, k=1)
            
            if dist > MAX_DISTANCE:
                continue
                
            p_end = toe_points[idx]
            
            # 【核心修复】不使用 addPoint，而是使用构造函数批量创建
            # 准备 x, y, z 列表
            xs = [float(p_start[0]), float(p_end[0])]
            ys = [float(p_start[1]), float(p_end[1])]
            zs = [float(p_start[2]), float(p_end[2])]
            
            # 直接创建包含 2 个点的点云
            vertices = pycc.ccPointCloud(xs, ys, zs)
            
            # 基于这个点云创建 Polyline
            poly = pycc.ccPolyline(vertices)
            
            # 添加索引 (0连到1)
            poly.addPointIndex(0)
            poly.addPointIndex(1)
            
            # 设置颜色 (使用整数参数)
            poly.setColor(0, 0, 0) # 黑色
            poly.showColors(True)
            poly.setWidth(2)
            
            # 将 vertices 作为 poly 的子对象，防止数据丢失
            poly.addChild(vertices)
            vertices.setEnabled(False) # 隐藏端点
            
            # 添加到组
            group.addChild(poly)
            count += 1

        # 6. 将结果添加到数据库
        if count > 0:
            CC.addToDB(group)
            print(f"✅ 生成完成！共生成 {count} 条示坡线。")
            print("请在左侧目录树查看 'Slope_Hachures_Group' 文件夹。")
        else:
            print("⚠️ 未生成任何线条。可能是 MAX_DISTANCE 设置太小。")
            
        CC.updateUI()

    except Exception as e:
        print(f"发生异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()