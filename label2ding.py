import pycc
import numpy as np

def main():
    # 1. 获取 CC 实例
    CC = pycc.GetInstance()
    entities = CC.getSelectedEntities()
    
    if not entities:
        print("错误：请先在左侧目录树中【选中】一个点云！")
        return

    cloud = entities[0]
    print(f"正在处理点云: {cloud.getName()}")
    
    try:
        # ====================================================
        # 2. 锁定要修改的标量场 (Scalar Field)
        # ====================================================
        # 这里指定您要修改的字段名称，通常是 "Label" 或 "Classification"
        TARGET_SF_NAME = "label"
        
        # 步骤 A: 尝试按名字查找
        sf_idx = cloud.getScalarFieldIndexByName(TARGET_SF_NAME)
        
        # 步骤 B: 如果按名字找不到，尝试获取当前显示的字段
        #if sf_idx == -1:
            #print(f"未找到名为 '{TARGET_SF_NAME}' 的字段，尝试获取当前显示的字段...")
            #current_out = cloud.getCurrentOutScalarField()
            
            # 兼容性处理：判断返回的是索引(int)还是对象
            #if isinstance(current_out, int):
                #sf_idx = current_out
            #else:
                # 如果返回的是对象，我们需要获取它的索引
                # 最稳妥的方法是再根据这个对象的名字找一次索引
                #if current_out is not None:
                    #sf_idx = cloud.getScalarFieldIndexByName(current_out.getName())

        # 如果还是找不到 (-1)，我们可以选择新建一个，或者报错
        if sf_idx == -1:
            print(f"⚠️ 未找到可用字段。正在新建一个名为 '{TARGET_SF_NAME}' 的字段...")
            sf_idx = cloud.addScalarField(TARGET_SF_NAME)
            if sf_idx == -1:
                print("❌ 错误：无法创建字段 (内存不足)")
                return

        # ====================================================
        # 3. 执行修改 (全部设为 2)
        # ====================================================
        # 获取字段对象
        sf_obj = cloud.getScalarField(sf_idx)
        print(f"正在修改字段: {sf_obj.getName()}")
        
        # 获取数据数组 (Direct View)
        np_array = sf_obj.asArray()
        
        # 【核心操作】直接将所有值赋值为 2
        np_array[:] = 2
        
        # ====================================================
        # 4. 刷新显示
        # ====================================================
        # 重新计算极值 (Min/Max)，否则颜色可能不更新
        sf_obj.computeMinAndMax()
        
        # 激活该字段显示
        cloud.setCurrentScalarField(sf_idx)
        
        # 刷新 UI
        CC.updateUI()
        print(f"✅ 成功！点云 '{cloud.getName()}' 的所有点 '{sf_obj.getName()}' 已改为 2。")

    except Exception as e:
        print(f"发生异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()