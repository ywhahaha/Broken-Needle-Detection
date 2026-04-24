import time
import cv2
import numpy as np
import math
from function.read_config import ConfigReader

ratio_1920 = 0.045803
# 38.42/836.01 0.045956
# 65号 37.42   817.13 0.045794
# 18号 38.43   841.03 0.045693
# 16号 38.24   833      0.045906
# 14号 37.83  825.61  0.045820

class NeedleDetection:
    """
    YOLO分割结果分析器
    用于分析分割掩码的几何特征（旋转矩形、宽度、长度等）
    """
    
    def __init__(self, model, conf_threshold=0.1, iou_threshold=0.3):
        """
        初始化分析器
        
        参数:
            model_path: YOLO模型路径
            conf_threshold: 置信度阈值
            iou_threshold: IOU阈值
        """
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold

        self.config = ConfigReader('default.yaml')
        self.width_correcting_pixels = self.config.width_correcting_pixels
        self.length_correcting_pixels = self.config.length_correcting_pixels
        self.show_details = self.config.show_details
        
        # 加载模型
        self.model = model
        self.results = None
        
        # 分析结果存储
        self.analysis_results = {}
    
    def predict(self, image, save_results=True, show_boxes=True):
        """
        对图像进行预测
        
        参数:
            image: 输入图像
            save_results: 是否保存预测结果
            show_boxes: 是否显示边界框
            
        返回:
            prediction_results: 预测结果
        """     
        start_time = time.time()
        
        # 执行预测
        self.results = self.model.predict(
            source=image,
            save=save_results,
            show_boxes=show_boxes,
            task='segment',
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            retina_masks=True
        )
        
        end_time = time.time()
        if self.show_details: print(f"预测完成，耗时: {end_time - start_time:.2f}秒")
        
        return self.results
    
    def calculate_rotated_rect_stats(self, mask):
        """
        计算掩码的最小旋转矩形和沿矩形方向的平均宽度
        
        参数:
            mask: 二值掩码图像
            
        返回:
            rotated_rect: 旋转矩形信息 (center, size, angle)
            avg_width: 平均宽度
            rect_length: 矩形长度
        """
        if len(mask.shape) > 2:
            mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        
        contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None, 0, 0
        
        all_contours = np.vstack(contours)
        rotated_rect = cv2.minAreaRect(all_contours)
        avg_width = self._calculate_average_width_along_axis(mask, rotated_rect)
        
        # 获取旋转矩形的长度（长边的长度）
        center, size, angle = rotated_rect
        rect_length = max(size[0], size[1])
        
        return rotated_rect, avg_width, rect_length
    
    def _calculate_average_width_along_axis(self, mask, rotated_rect):
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
                
                width = self._calculate_width_at_point(mask, point_on_axis, perpendicular_angle_rad, short_axis_length)
                
                if width > 0:
                    widths.append(width)
        
        return np.mean(widths) if widths else 0
    
    def _calculate_width_at_point(self, mask, point, angle_rad, max_search_distance):
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
    
    def analyze_results(self, results=None):
        """
        分析预测结果，按类别统计几何特征
        
        参数:
            results: 预测结果，如果为None则使用上次预测结果
            
        返回:
            analysis_results: 分析结果字典
        """
        if results is None:
            if self.results is None:
                raise ValueError("没有可用的预测结果，请先调用predict()方法")
            results = self.results
        
        # 初始化结果存储
        class0_widths = []      # 标签0的平均宽度
        class0_lengths = []     # 标签0的旋转矩形长度
        class1_widths = []      # 标签1的平均宽度
        class1_lengths = []     # 标签1的旋转矩形长度
        class2_lengths = []     # 标签2的旋转矩形长度
        
        detection_details = []   # 详细检测信息
        
        if self.show_details: print("开始分析分割结果...")
        
        for i, result in enumerate(results):
            if result.boxes is not None and result.masks is not None:
                # 获取所有检测到的类别
                classes = result.boxes.cls.cpu().numpy() if result.boxes.cls is not None else []
                
                for j, (cls_id, mask_data) in enumerate(zip(classes, result.masks.data)):
                    cls_id = int(cls_id)
                    
                    # 将掩码转换为二值图像
                    mask = mask_data.cpu().numpy()
                    mask = (mask > 0.5).astype(np.uint8) * 255
                    
                    # 计算旋转矩形和平均宽度
                    rotated_rect, avg_width, rect_length = self.calculate_rotated_rect_stats(mask)
                    
                    if rotated_rect is not None:
                        center, size, angle = rotated_rect
                        
                        # 存储检测详情
                        detection_info = {
                            'class_id': cls_id,
                            'object_id': j + 1,
                            'center': center,
                            'size': size,
                            'angle': angle,
                            'width': avg_width,
                            'length': rect_length
                        }
                        detection_details.append(detection_info)
                        
                        # 按类别分类存储
                        if cls_id == 0:
                            class0_widths.append(avg_width)
                            class0_lengths.append(rect_length)
                            if self.show_details: print(f"  检测到标签0对象 {j+1}: 宽度={avg_width:.2f}px, 长度={rect_length:.2f}px")
                        
                        elif cls_id == 1:
                            class1_widths.append(avg_width)
                            class1_lengths.append(rect_length)
                            if self.show_details: print(f"  检测到标签1对象 {j+1}: 宽度={avg_width:.2f}px")
                        
                        elif cls_id == 2:
                            class2_lengths.append(rect_length)
                            if self.show_details: print(f"  检测到标签2对象 {j+1}: 长度={rect_length:.2f}px")
            else:
                return 0,1,1,1,1

        # # 计算最终统计结果
        # self.analysis_results = {
        #     # 标签0: 平均宽度和长度
        #     'class0': {
        #         'avg_width': np.mean(class0_widths) if class0_widths else 0,
        #         'avg_length': np.mean(class0_lengths) if class0_lengths else 0,
        #         'count': len(class0_widths)
        #     },
        #     # 标签1: 平均宽度
        #     'class1': {
        #         'avg_width': np.mean(class1_widths) if class1_widths else 0,
        #         'count': len(class1_widths)
        #     },
        #     # 标签2: 总长度
        #     'class2': {
        #         'total_length': np.sum(class2_lengths),
        #         'count': len(class2_lengths)
        #     },
        #     # 详细检测信息
        #     'detections': detection_details,
        #     # 汇总信息
        #     'summary': {
        #         'total_objects': len(detection_details),
        #         'class0_count': len(class0_widths),
        #         'class1_count': len(class1_widths),
        #         'class2_count': len(class2_lengths)
        #     }
        # }

        class0_avg_widths = round((np.mean(class0_widths) - self.width_correcting_pixels) * ratio_1920, 2).item()
        class0_avg_lengths = round(np.max(class0_lengths) * ratio_1920, 2).item()

        class1_avg_widths = round((class1_widths[np.argmax(class1_lengths)] - self.width_correcting_pixels) * ratio_1920, 2).item()
        class2_total_lengths = round((np.sum(class2_lengths) + self.length_correcting_pixels) * ratio_1920, 2).item()
        
        return 2, class2_total_lengths, class0_avg_lengths, class0_avg_widths, class1_avg_widths #机针长度、针柄长度、针柄直径、针杆直径
    
    
    def visualize_results(self, results=None, output_path="result_visualization.jpg", save_postprocess_image=False):
        """
        可视化分析结果
        
        参数:
            results: 预测结果
            output_path: 输出图像路径
            show_image: 是否显示图像
            
        返回:
            output_path: 输出图像路径
        """
        if results is None:
            if self.results is None:
                raise ValueError("没有可用的预测结果，请先调用predict()方法")
            results = self.results

        if not save_postprocess_image:
            return
        
        orig_img = results[0].orig_img.copy()
        
        # 定义类别颜色和名称
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
                    rotated_rect, avg_width, rect_length = self.calculate_rotated_rect_stats(mask)
                    
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
        
        # 保存结果
        cv2.imwrite(output_path, orig_img)
        if self.show_details: print(f"可视化结果已保存到: {output_path}")
        
        return
    
    def get_analysis_report(self):
        """
        获取分析报告
        
        返回:
            report: 格式化分析报告字符串
        """
        if not self.analysis_results:
            return "没有可用的分析结果，请先调用analyze_results()方法"
        
        report = []
        report.append("=" * 50)
        report.append("           分割结果分析报告")
        report.append("=" * 50)
        
        summary = self.analysis_results['summary']
        report.append(f"检测到对象总数: {summary['total_objects']}")
        report.append(f"标签0数量: {summary['class0_count']}")
        report.append(f"标签1数量: {summary['class1_count']}")
        report.append(f"标签2数量: {summary['class2_count']}")
        report.append("")
        
        # 标签0结果
        class0 = self.analysis_results['class0']
        if class0['count'] > 0:
            report.append("=== 标签0结果 ===")
            report.append(f"平均宽度: {class0['avg_width']:.2f}px")
            report.append(f"平均长度: {class0['avg_length']:.2f}px")
            report.append("")
        
        # 标签1结果
        class1 = self.analysis_results['class1']
        if class1['count'] > 0:
            report.append("=== 标签1结果 ===")
            report.append(f"平均宽度: {class1['avg_width']:.2f}px")
            report.append("")
        
        # 标签2结果
        class2 = self.analysis_results['class2']
        if class2['count'] > 0:
            report.append("=== 标签2结果 ===")
            report.append(f"总长度: {class2['total_length']:.2f}px")
            report.append("")


# 使用示例
if __name__ == "__main__":
    # 创建分析器实例
    from ultralytics import YOLO
    model = YOLO("weight/best-seg_ncnn_model")

    analyzer = NeedleDetection(
        model=model,
        conf_threshold=0.25,
        iou_threshold=0.3
    )
    
    # 图像路径
    image = "low_exposure_frame_1764229849.1395974.png"
    try:
        # 1. 执行预测
        results = analyzer.predict(image)
        
        # 2. 分析结果
        analysis_results = analyzer.analyze_results(results)
        print(analysis_results)
        # 3. 生成可视化结果
        # output_image = analyzer.visualize_results(results, show_image=True)
        
        # 4. 打印分析报告
        # print(analyzer.get_analysis_report())
        
    except Exception as e:
        print(f"处理过程中发生错误: {e}")