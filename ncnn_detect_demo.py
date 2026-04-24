from ultralytics import YOLO
import time
import cv2
import numpy as np
import math

# 加载模型
model = YOLO("weight/best-seg_ncnn_model")

# 预测图片
source_folder = "figs/test/capture_1763089882_173848_jpg.rf.96537b822277dec77ae1e5132ac72356.jpg"

start_time = time.time()

results = model.predict(
    source=source_folder,
    save=True,
    show_boxes=False,
    task='segment',
    conf=0.1,
    iou=0.3
)

def calculate_rotated_rect_stats(mask):
    """
    计算掩码的最小旋转矩形和沿矩形方向的平均宽度
    """
    if len(mask.shape) > 2:
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
    
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return None, 0, 0
    
    all_contours = np.vstack(contours)
    rotated_rect = cv2.minAreaRect(all_contours)
    avg_width = calculate_average_width_along_axis(mask, rotated_rect)
    
    # 获取旋转矩形的长度（长边的长度）
    center, size, angle = rotated_rect
    rect_length = max(size[0], size[1])
    
    return rotated_rect, avg_width, rect_length

def calculate_average_width_along_axis(mask, rotated_rect):
    """
    计算掩码沿旋转矩形长轴方向的平均宽度
    """
    center, size, angle = rotated_rect
    
    if size[0] > size[1]:
        long_axis_length = size[0]
        short_axis_length = size[1]
        long_axis_angle = angle
    else:
        long_axis_length = size[1]
        short_axis_length = size[0]
        long_axis_angle = angle + 90
    
    widths = []
    num_samples = max(20, int(long_axis_length / 2))
    
    for i in range(num_samples - 10):
        for direction in [-1, 1]:
            distance_from_center = (i / num_samples) * (long_axis_length / 2) * direction
            
            long_axis_angle_rad = math.radians(long_axis_angle)
            point_on_axis = (
                center[0] + distance_from_center * math.cos(long_axis_angle_rad),
                center[1] + distance_from_center * math.sin(long_axis_angle_rad)
            )
            
            perpendicular_angle = long_axis_angle + 90
            perpendicular_angle_rad = math.radians(perpendicular_angle)
            
            width = calculate_width_at_point(mask, point_on_axis, perpendicular_angle_rad, short_axis_length)
            
            if width > 0:
                widths.append(width)
    
    return np.mean(widths) if widths else 0

def calculate_width_at_point(mask, point, angle_rad, max_search_distance):
    """
    在给定点沿垂直方向计算掩码宽度
    """
    height, width = mask.shape[:2]
    x, y = point
    
    if not (0 <= x < width and 0 <= y < height):
        return 0
    
    if mask[int(y), int(x)] == 0:
        return 0
    
    total_width = 0
    
    for direction in [-1, 1]:
        current_distance = 0
        step = 1.0
        
        while current_distance < max_search_distance:
            current_distance += step
            test_x = x + current_distance * math.cos(angle_rad) * direction
            test_y = y + current_distance * math.sin(angle_rad) * direction
            
            if not (0 <= test_x < width and 0 <= test_y < height):
                break
            
            if mask[int(test_y), int(test_x)] == 0:
                total_width += current_distance - step/2
                break
    
    return total_width

def get_class_results(results):
    """
    根据标签返回不同的计算结果：
    - 标签0: 返回平均宽度和旋转矩形长度
    - 标签1: 返回平均宽度
    - 标签2: 返回旋转矩形长度（多个标签2则相加）
    """
    class0_widths = []      # 标签0的平均宽度
    class0_lengths = []     # 标签0的旋转矩形长度
    class1_widths = []      # 标签1的平均宽度
    class2_lengths = []     # 标签2的旋转矩形长度（用于相加）
    
    for i, result in enumerate(results):
        if result.boxes is not None and result.masks is not None:
            # 获取所有检测到的类别
            classes = result.boxes.cls.cpu().numpy() if result.boxes.cls is not None else []
            
            for j, (cls_id, mask_data) in enumerate(zip(classes, result.masks.data)):
                cls_id = int(cls_id)
                print(f"检测到对象 {j+1}: 标签={cls_id}")
                
                # 将掩码转换为二值图像
                mask = mask_data.cpu().numpy()
                mask = (mask > 0.5).astype(np.uint8) * 255
                
                # 计算旋转矩形和平均宽度
                rotated_rect, avg_width, rect_length = calculate_rotated_rect_stats(mask)
                
                if rotated_rect is not None:
                    if cls_id == 0:
                        class0_widths.append(avg_width)
                        class0_lengths.append(rect_length)
                        print(f"  标签0 - 平均宽度: {avg_width:.2f}px, 长度: {rect_length:.2f}px")
                    
                    elif cls_id == 1:
                        class1_widths.append(avg_width)
                        print(f"  标签1 - 平均宽度: {avg_width:.2f}px")
                    
                    elif cls_id == 2:
                        class2_lengths.append(rect_length)
                        print(f"  标签2 - 长度: {rect_length:.2f}px")
    
    # 计算最终结果
    results_dict = {}
    
    # 标签0: 返回平均宽度和旋转矩形长度的平均值
    if class0_widths:
        results_dict['class0_avg_width'] = np.mean(class0_widths)
        results_dict['class0_avg_length'] = np.mean(class0_lengths)
    else:
        results_dict['class0_avg_width'] = 0
        results_dict['class0_avg_length'] = 0
    
    # 标签1: 返回平均宽度的平均值
    if class1_widths:
        results_dict['class1_avg_width'] = np.mean(class1_widths)
    else:
        results_dict['class1_avg_width'] = 0
    
    # 标签2: 返回长度的总和
    results_dict['class2_total_length'] = np.sum(class2_lengths)
    
    return results_dict

def visualize_results(results, output_path="result_visualization.jpg"):
    """
    可视化结果，根据类别用不同颜色显示
    """
    orig_img = results[0].orig_img.copy()
    
    # 定义类别颜色
    class_colors = {
        0: (0, 255, 0),    # 绿色 - 标签0
        1: (255, 0, 0),    # 蓝色 - 标签1  
        2: (0, 0, 255)     # 红色 - 标签2
    }
    
    class_names = {
        0: "Class0",
        1: "Class1", 
        2: "Class2"
    }
    
    for i, result in enumerate(results):
        if result.boxes is not None and result.masks is not None:
            classes = result.boxes.cls.cpu().numpy() if result.boxes.cls is not None else []
            
            for j, (cls_id, mask_data) in enumerate(zip(classes, result.masks.data)):
                cls_id = int(cls_id)
                color = class_colors.get(cls_id, (255, 255, 255))
                
                # 将掩码转换为二值图像
                mask = mask_data.cpu().numpy()
                mask = (mask > 0.5).astype(np.uint8) * 255
                
                # 计算旋转矩形和平均宽度
                rotated_rect, avg_width, rect_length = calculate_rotated_rect_stats(mask)
                
                if rotated_rect is not None:
                    box_points = cv2.boxPoints(rotated_rect)
                    box_points = np.array(box_points, dtype=np.int32)
                    
                    if len(box_points) > 0 and np.all(np.isfinite(box_points)):
                        # 绘制旋转矩形
                        cv2.drawContours(orig_img, [box_points], 0, color, 2)
                        
                        # 添加文本信息
                        center, size, angle = rotated_rect
                        if cls_id == 0:
                            text = f"{class_names[cls_id]}: W{avg_width:.1f} L{rect_length:.1f}"
                        elif cls_id == 1:
                            text = f"{class_names[cls_id]}: W{avg_width:.1f}"
                        else:  # cls_id == 2
                            text = f"{class_names[cls_id]}: L{rect_length:.1f}"
                        
                        cv2.putText(orig_img, text, (int(center[0]), int(center[1]) - 20),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    cv2.imwrite(output_path, orig_img)
    print(f"可视化结果已保存到: {output_path}")

# 处理所有结果
print("开始计算掩码的旋转矩形和平均宽度...")

# 获取分类结果
final_results = get_class_results(results)

# 打印最终结果
print("\n=== 最终计算结果 ===")
print(f"标签0 - 平均宽度: {final_results['class0_avg_width']:.2f}px")
print(f"标签0 - 平均长度: {final_results['class0_avg_length']:.2f}px") 
print(f"标签1 - 平均宽度: {final_results['class1_avg_width']:.2f}px")
print(f"标签2 - 总长度: {final_results['class2_total_length']:.2f}px")

# 生成可视化结果
visualize_results(results)

end_time = time.time()
print(f"\n总处理时间: {end_time - start_time:.2f} 秒")