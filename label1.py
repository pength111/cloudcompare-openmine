import pycc
import numpy as np

def main():
    # 1. 获取 CC 实例并检查选中的点云
    CC = pycc.GetInstance()
    entities = CC.getSelectedEntities()
    
    if not entities:
        print("错误：请先在左侧目录树中【选中】一个点云！")
        return

    # 确保选中的是点云对象（过滤掉网格等其他类型）
    cloud = None
    for ent in entities:
        if hasattr(ent, 'getScalarFieldIndexByName'):  # 判断是否是点云
            cloud = ent
            break
    if cloud is None:
        print("错误：选中的对象不是点云！")
        return
    
    print(f"正在处理点云: {cloud.getName()}")
    
    try:
        # ====================================================
        # 2. 核心逻辑：确保 "label" 字段存在，不存在则创建
        # ====================================================
        TARGET_SF_NAME = "label"
        
        # 步骤1：查找是否存在label字段
        sf_idx = cloud.getScalarFieldIndexByName(TARGET_SF_NAME)
        
        # 步骤2：如果不存在，创建新的label字段
        if sf_idx == -1:
            print(f"⚠️ 未找到 '{TARGET_SF_NAME}' 字段，正在创建新字段...")
            sf_idx = cloud.addScalarField(TARGET_SF_NAME)
            if sf_idx == -1:
                print("❌ 错误：创建label字段失败（可能内存不足）")
                return
            print(f"✅ 成功创建 '{TARGET_SF_NAME}' 字段，索引：{sf_idx}")
        else:
            print(f"✅ 找到已存在的 '{TARGET_SF_NAME}' 字段，索引：{sf_idx}")

        # ====================================================
        # 3. 给label字段赋值（可自定义赋值逻辑）
        # ====================================================
        # 获取字段对象
        sf_obj = cloud.getScalarField(sf_idx)
        # 获取字段的numpy数组视图（直接操作原数据，无需拷贝）
        np_array = sf_obj.asArray()
        
        # 【核心赋值逻辑】这里示例：所有点的label设为1
        # 你可以根据需求修改赋值规则，比如：
        # np_array[:] = 0  # 全部设为0
        # np_array[np_array < 0] = 1  # 负数设为1
        np_array[:] = 1  # 示例：全部赋值为1

        # ====================================================
        # 4. 刷新CC界面，确保修改生效
        # ====================================================
        # 重新计算字段的最大/最小值（保证颜色映射正确）
        sf_obj.computeMinAndMax()
        # 将label字段设为当前显示的标量字段
        cloud.setCurrentScalarField(sf_idx)
        # 刷新UI显示
        CC.updateUI()
        
        print(f"✅ 操作完成！点云 '{cloud.getName()}' 的 '{TARGET_SF_NAME}' 字段已赋值为 1")

    except Exception as e:
        print(f"❌ 执行异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()