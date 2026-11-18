# 同名PPT页的原生显示比较

`compare_page.py`读取调用者明确指定的候选和作者图集，以完整@@稳定图名分别定位当前页。它只检验显示，不读取科学原件、不解释图内数值、不修改输入PPT。调用顺序及权限由[更新PPT绘图代码工作流](../../../RULES/自定义命令/更新PPT对应的画图代码.md)规定。

入口是文件内的参数解析及顺序操作：定位图名、复制输入、调用既有PowerPoint导出、比较RGB、复核输入摘要、写比较结果。没有科学模块或默认实验条件。

## 输入与本次产物

`--candidate`指定根temp内刚生成的候选，`--author`指定项目内已保存的作者PPT，`--figure`为含版本后缀的完整图名，`--width`为明确的正整数像素宽度，`--build`必须是根temp内的新空目录。高度由各图集的实际画布比例计算，尺寸不同不会重采样对齐。

```text
temp/本次比较/
├─ candidate.pptx        # 本次候选原字节独立副本
├─ author.pptx           # 作者图集原字节独立副本
├─ render.json           # PowerPoint导出的明确副本地址、页号及PNG输出地址
├─ candidate.png         # 候选同名页全页原生RGB显示
├─ author.png            # 作者同名页全页原生RGB显示
└─ comparison.json       # 当前输入及像素比较记录
```

所有产物只供本次验收，结束由调用任务清空。原图集保持原字节；PowerPoint只打开本次副本，工具不退出用户的PowerPoint进程。

## comparison.json

| 字段 | 类型及含义 | 示例 |
| --- | --- | --- |
| `figure` | str，双方唯一完整图名 | `fig-overview-topology` |
| `inputs` | dict，`candidate`和`author`分别含原始绝对`path`、原字节`sha256`及本次1起始`page` | `page=1`；摘要由本次真实输入计算 |
| `shape_yxc` | dict，每份PNG的高度、宽度和RGB通道数 | `[922,2400,3]` |
| `different_pixels` | int或null，任一RGB通道不同的像素总数；图幅不同时为null | `0`；旧Fig1负例为`6347` |
| `max_rgb_difference` | int或null，所有RGB通道的最大绝对差，范围0至255；图幅不同时为null | `0`；旧Fig1负例为`217` |
| `source_files_unchanged` | bool，原始输入前后摘要均一致 | `true` |
| `passed` | bool，图幅相同、不同像素为0且原输入不变 | `true` |
| `meaning` | str，限定本记录只证明本次显示比较 | `只证明本次原生全页显示一致; 科学来源与计算须另按Figure契约核验` |

退出码0表示上述比较通过，1表示比较未通过；定位、输入、导出异常同样失败，不把缺少结果文件当成功。报告不是科学来源，也不能以截图相同证明服务器输入、候选归属或统计公式正确。
