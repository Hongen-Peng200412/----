# Abstract
冷冻电镜密度图对于生物学很重要，从 CryoEM 中自动建模生物分子也很重要。
从CryoEM端到端地建模蛋白核酸受体做得很好了（CryoAtom2），但是高精度端到端建模小分子结构仍然 remain a challenge。
我们开发了这个方法，按照严格的 Find-Match-Build 三步走，它们的精度各自分别达到 xxx，高于Emap2lig的xxx。且获得了 xxx 的端到端成功率。






# Introduction

CryoEM的蛋白核酸的端到端建模：
Modelangleo、EMProt、CryoATOM2。都很好。自然的 idea 是在建模小分子时利用这些自动推理的结构，不用白不用，


ligand的识别：
Emap2lig 能识别ligand，但主要针对小分子，且只利用密度图本身的信息没用受体，精度差。

ligand的Match:
EMERALD-ID 只能针对小分子做Match。以及：它是根据 docking 的结果反过来预测小分子的 identity，复杂度天然就是O(N_g x K)、而且docking 还是不能用GPU加速，共同导致太慢了。适用范围小（只能做小分子、且不能做长尾PDB）、慢，所以需要改进。

ligand的Build:
一方面，只用受体的docking做得很好（PocketXmol、DiffDock）。另一方面，很少有同时用密度+受体的方法。
也有用纯密度docking的方法，如Emap2lig-Build，EMERALD，但是它们达不到只用受体的方法。
于是自然想到微调：把密度信息加到只用受体方法的docking中，用自动建模的受体代替真实受体。

介绍自己的端到端工作：
多么多么好，达到了xxx。