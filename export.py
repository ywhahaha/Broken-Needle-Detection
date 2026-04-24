from ultralytics import YOLO

# 加载模型（使用相对路径）
model = YOLO("weight/best-seg.pt")  # 确保模型文件在当前目录

model.export(
    format="onnx",      # 导出格式为 ONNX
    # keras=False,        # 不导出为 Keras 格式
    optimize=False,     # 不进行优化 False, 移动设备优化的参数，用于在导出为TorchScript 格式时进行模型优化
    half=True,         # 不启用 FP16 量化
    int8=False,         # 不启用 INT8 量化
    # dynamic=False,      # 不启用动态输入尺寸
    simplify=True,      # 简化 ONNX 模型
    opset=21,         # 使用最新的 opset 版本
    imgsz=(320, 1280),
    # workspace=4.0,      # 为 TensorRT 优化设置最大工作区大小（GiB）
    # nms=False,          # 不添加 NMS（非极大值抑制）
    batch=1,            # 指定批处理大小
    device="cpu"        # 指定导出设备为CPU或GPU，对应参数为"cpu" , "0"
)
