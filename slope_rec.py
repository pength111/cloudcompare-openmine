import numpy as np
import pycc
from scipy.spatial import cKDTree
from sklearn.cluster import DBSCAN
import random

def main():
    CC = pycc.GetInstance()
    entities = CC.getSelectedEntities()
    if not entities:
        print("错误：请先选择一个点云！")
        return

    cloud = entities[0]
    print(f"正在处理点云: {cloud.getName()}")
    
    try:
        # 1. 获取点数据和颜色数据
        points = np.array(cloud.points())
        # 获取RGB颜色数据 (关键新增)
        if cloud.hasColors():
            colors = np.array(cloud.colors(), dtype=np.uint8)
            print(f"点云包含RGB颜色信息，将同步保留")
        else:
            colors = None
            print("警告：原始点云没有RGB颜色信息")
            
        print(f"点云总点数: {len(points)}")
        
        # 2. 自动查找 Label 字段
        sf_obj = None
        curr = cloud.getCurrentOutScalarField()
        if isinstance(curr, int) and curr != -1:
             temp_sf = cloud.getScalarField(curr)
             temp_vals = np.unique(np.array(temp_sf.asArray()))
             if 0 in temp_vals and 1 in temp_vals:
                 sf_obj = temp_sf
        
        if sf_obj is None:
            print("当前激活字段不符合要求，正在遍历查找...")
            for sf_idx in range(cloud.getNumberOfScalarFields()):
                temp_sf = cloud.getScalarField(sf_idx)
                temp_labels = np.array(temp_sf.asArray())
                unique_vals = np.unique(temp_labels)
                if 0 in unique_vals and 1 in unique_vals:
                    sf_obj = temp_sf
                    break
        
        if sf_obj:
            print(f"读取原始字段: {sf_obj.getName()}")
            original_labels = np.array(sf_obj.asArray()).copy()
            unique_original = np.unique(original_labels)
            if not (0 in unique_original and 1 in unique_original):
                print(f"❌ 错误：字段 {sf_obj.getName()} 中缺少 0 或 1！")
                return
        else:
            print("❌ 未找到包含 0(平盘) 和 1(片帮) 的标量字段")
            return

        # =======================================================
        # 参数设置
        # =======================================================
        SEARCH_RADIUS = 2.0 
        DBSCAN_EPS = 3     
        DBSCAN_MIN_SAMPLES = 1
        
        # 3. 数据准备
        slope_mask = (original_labels == 1)
        flat_mask = (original_labels == 0)
        
        slope_points = points[slope_mask]
        flat_points = points[flat_mask]
        flat_indices = np.where(flat_mask)[0] 
        
        if len(slope_points) == 0 or len(flat_points) == 0:
            print("错误：数据缺失 (Label 0 或 1 数量为 0)")
            return

        print(f"搜索半径: {SEARCH_RADIUS}m ...")
        
        # 4. KD-Tree 查询
        tree = cKDTree(slope_points, leafsize=64)
        dists, _ = tree.query(flat_points, k=1, workers=-1)
        
        # 5. 计算缓冲区索引
        is_in_buffer = dists <= SEARCH_RADIUS
        indices_to_mark = flat_indices[is_in_buffer] # 这是需要提取并删除的点的全局索引
        count = len(indices_to_mark)
        print(f"标记了 {count} 个缓冲区点 (Label=2)")
        
        if count == 0:
            print("未找到缓冲区点，程序结束。")
            return

        # 6. 计算新标签 (仅用于 Buffer_Result 字段显示，不影响剔除逻辑)
        new_labels = original_labels.copy()
        new_labels[indices_to_mark] = 2
        
        # 更新原始点云的标量场 (可选，方便对比)
        new_sf_name = "Buffer_Result"
        idx = cloud.getScalarFieldIndexByName(new_sf_name)
        if idx == -1: idx = cloud.addScalarField(new_sf_name)
        if idx != -1:
            out_sf = cloud.getScalarField(idx)
            out_sf.asArray()[:] = new_labels
            out_sf.computeMinAndMax()
            cloud.setCurrentScalarField(idx)
        
        # =======================================================
        # 步骤 2: DBSCAN 聚类并提取独立缓冲区点云
        # =======================================================
        print("\n[步骤2] 开始 DBSCAN 聚类提取缓冲区...")
        buffer_points = points[indices_to_mark]
        # 获取缓冲区点对应的颜色 (关键新增)
        buffer_colors = colors[indices_to_mark] if colors is not None else None
        
        db = DBSCAN(eps=DBSCAN_EPS, min_samples=DBSCAN_MIN_SAMPLES, n_jobs=-1).fit(buffer_points)
        cluster_labels = db.labels_
        
        unique_clusters = set(cluster_labels)
        if -1 in unique_clusters: unique_clusters.remove(-1)
        
        n_clusters = len(unique_clusters)
        print(f"DBSCAN 完成: 发现 {n_clusters} 个独立缓冲区")
        
        for cid in unique_clusters:
            mask = (cluster_labels == cid)
            c_pts = buffer_points[mask]
            # 获取该聚类对应的颜色 (关键新增)
            c_colors = buffer_colors[mask] if buffer_colors is not None else None
            
            # 创建新点云
            new_cloud = pycc.ccPointCloud(
                c_pts[:, 0].copy(), 
                c_pts[:, 1].copy(), 
                c_pts[:, 2].copy()
            )
            
            # 设置点云颜色 (关键新增)
            if c_colors is not None:
                # 将RGB颜色数组设置到新点云
                new_cloud.resize(len(c_pts))
                new_cloud.setColors(c_colors)
                new_cloud.showColors(True)
            else:
                # 如果原始没有颜色，使用随机颜色
                r = random.randint(50, 255)
                g = random.randint(50, 255)
                b = random.randint(50, 255)
                new_cloud.setColor(r, g, b)  
                new_cloud.showColors(True)
            
            new_cloud.setName(f"Buffer_Cluster_{cid}")
            CC.addToDB(new_cloud)
            
        print(f"✅ 已生成 {n_clusters} 个独立缓冲区点云")

        # =======================================================
        # 【新增】步骤 3: 从原始数据中“剔除”缓冲区
        # =======================================================
        print("\n[步骤3] 生成剔除缓冲区后的剩余点云...")
        
        # 1. 创建一个保留掩膜 (默认为 True，即全部保留)
        keep_mask = np.ones(len(points), dtype=bool)
        
        # 2. 将缓冲区的索引设为 False (剔除)
        keep_mask[indices_to_mark] = False
        
        # 3. 提取剩余的点和颜色 (关键新增)
        remaining_points = points[keep_mask]
        remaining_colors = colors[keep_mask] if colors is not None else None
        remaining_labels = original_labels[keep_mask] # 对应的标签也只保留剩下的 (0和1)
        
        # 4. 创建一个新的“剩余点云”
        remaining_cloud = pycc.ccPointCloud(
            remaining_points[:, 0],
            remaining_points[:, 1],
            remaining_points[:, 2]
        )
        
        # 设置剩余点云的颜色 (关键新增)
        if remaining_colors is not None:
            remaining_cloud.resize(len(remaining_points))
            remaining_cloud.setColors(remaining_colors)
            remaining_cloud.showColors(True)
        
        remaining_cloud.setName(f"{cloud.getName()}_Remaining") # 命名建议加上后缀
        
        # 5. 将标签赋回去 (Label 0 和 1)
        sf_idx = remaining_cloud.addScalarField("label")
        sf = remaining_cloud.getScalarField(sf_idx)
        sf.asArray()[:] = remaining_labels
        sf.computeMinAndMax()
        remaining_cloud.setCurrentScalarField(sf_idx)
        
        # 6. 添加剩余点云到 DB
        CC.addToDB(remaining_cloud)
        
        # 7. 隐藏原始输入点云 (视觉上达到“剔除”效果)
        cloud.setEnabled(False)
        # 如果你想彻底删除原始点云，可以取消下面这行的注释：
        # CC.deleteEntity(cloud)
        
        print(f"✅ 处理完毕！")
        print(f"   - 原始点云已隐藏")
        print(f"   - 生成了剩余点云: {remaining_cloud.getName()} (点数: {len(remaining_points)})")
        
        CC.updateUI()

    except Exception as e:
        print(f"发生异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()