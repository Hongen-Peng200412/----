"""仅修正 Windows 调试输出编码, 不读取或修改任何三维模型、外观或相机."""
import sys
sys.__stdout__.reconfigure(encoding='utf-8')
sys.__stderr__.reconfigure(encoding='utf-8')
