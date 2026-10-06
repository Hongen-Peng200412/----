# Abstract

Cryo-electron microscopy (cryo-EM) has advanced three-dimensional structure determination of macromolecular complexes. De novo modelling algorithms, including ModelAngelo and CryoAtom2, have automated the construction of protein and nucleic acid backbones. However, fully automated, accurate end-to-end reconstruction of ligands involved in catalysis, allosteric regulation and drug action remains challenging. Existing tools address individual steps, with inefficient connections between region localisation, chemical identity matching and pose reconstruction. Here we introduce LigandSeek, a fully automated end-to-end framework that jointly models density and receptor information through three stages: Find, Match and Build. On a benchmark of 179 complexes, Find achieved a one-to-one PRAUC@0.3 of 0.541, increasing to 0.663 with deposited receptor structures. Both exceeded the score of 0.255 achieved by the density-only method Emap2lig-Find. Match achieved 86.6% overall matching accuracy, with a mean matching time of 0.09 s per candidate region. For Build, we incorporated continuous cryo-EM density-field constraints into a receptor-based generative model and fine-tuned it. This reduced the median root-mean-square deviation (RMSD) of top-1 small-molecule poses from 1.81 Å to 1.21 Å. In end-to-end blind evaluation without deposited receptor structures as input, LigandSeek achieved a success rate of 67.5% across 77 PDB entries. With deposited receptor structures, this rate increased to 71.4%. LigandSeek provides an efficient, fully automated workflow from continuous three-dimensional cryo-EM density maps to all-atom ligand poses.

# Introduction

Single-particle cryo-electron microscopy (cryo-EM) has become an important method for determining the three-dimensional structures of macromolecular complexes[@callaway2020revolution; @bai2015cryo]. Deep learning tools such as ModelAngelo[@jamali2024modelangelo], CryoAtom2[@cryoatom2_2025] and EMProt[@emprot2024] have advanced automated modelling of protein and nucleic acid structures. However, ligands bound in the binding pockets of these complexes often regulate catalysis, conformational switching and signalling cascades[@cheng2018cryo]. A key challenge is therefore to combine experimental density and the receptor environment to detect, identify and reconstruct accurate all-atom ligand structures automatically, without expert modelling. Automated, end-to-end reconstruction of all-atom ligand structures from cryo-EM density maps faces three sequential bottlenecks.

The first is region localisation, the Find bottleneck. Cryo-EM density maps span large spatial scales, with heterogeneous local signal-to-noise ratios and diffuse, intermixed densities from water molecules or lipid micelles. Existing density detection methods, such as Emap2lig-Find[@umap2lig], mainly use three-dimensional voxel segmentation networks to locate small-molecule density blobs directly across the entire map. Without information about the surrounding macromolecular receptor, these density-only approaches lack the chemical and geometric context of the binding pocket, tending to produce many false-positive candidate regions and thereby reducing the precision of instance-level localisation.

The second is chemical identity matching, the Match bottleneck. Even after a ligand region is located, associating it with the correct chemical identity remains a major challenge. Although Emap2lig[@umap2lig] combines region detection with pose reconstruction, it lacks automated identity matching. Users must specify the correspondence between regions and ligand identities, preventing full automation of the end-to-end workflow. Alternatively, EMERALD-ID[@emerald_id] provides identity matching by docking candidate ligands individually and inferring their identities from the resulting scores. Its computational complexity is $O(N_g \times K)$, where $N_g$ is the number of candidate sites and $K$ is the number of competing ligand identities. This computational burden, coupled with a lack of GPU acceleration, can make scoring at a single site take hours. Furthermore, it primarily targets small-molecule ligands, limiting its use in complexes containing other ligand types. Rapid, automated identity matching is therefore a key step in connecting region localisation to pose reconstruction.



The third is pose reconstruction, the Build bottleneck. After the binding region and chemical identity have been determined, generative docking models such as DiffDock[@corso2023diffdock] and PocketXMol[@pocketxmol] usually rely primarily on receptor structures, failing to exploit experimental density to guide pose generation. Conversely, density-only deep learning tools such as Emap2lig-Build[@umap2lig] omit protein and nucleic acid receptors, struggling to reconcile density fitting with receptor-environment constraints. Classical non-deep-learning methods, including EMERALD, GemSpot and ChemEM, can incorporate both the receptor environment and experimental density for pose search or optimisation[@muenks2023emerald; @robertson2020gemspot; @sweeney2024chemem]. However, they are computationally slow and remain disconnected from upstream localisation and identity matching.

To address these bottlenecks and unify localisation, matching and pose reconstruction, we developed LigandSeek, an automated end-to-end framework based on joint density and receptor modelling ({{figref:fig-overview_v2,fig-method-v4}}). Across all three stages, the neural networks share a unified representation that jointly encodes the experimental density, receptor-derived simulated and difference densities, and the chemical and geometric environments of receptor atoms.

LigandSeek follows a three-stage Find–Match–Build workflow:

1. LigandSeek-Find uses a hybrid point–voxel network to fuse continuous voxel-density representations with geometric and chemical information from the receptor point cloud. It detects three-dimensional ligand regions while balancing precision and recall.
2. LigandSeek-Match uses a cross-modal matching network with graph and context attention. It integrates ligand language representations, molecular graph representations and contextual information from other ligand identities in the same complex. This enables rapid, accurate identity matching across a broad range of ligand types, including small molecules, metal ions and sugars.
3. LigandSeek-Build fine-tunes the generative model PocketXMol with local density conditioning. This enables generated poses to satisfy both experimental density contours and pocket chemical constraints, thereby improving sampling accuracy.

We evaluated the framework on 179 complexes comprising 2,502 ligand instances. Under blind evaluation conditions, only receptors modelled de novo by CryoAtom2 were used, with no deposited receptor structures provided as input. All three LigandSeek components outperformed their respective baselines. Find achieved a one-to-one PRAUC@0.3 of 0.541, compared with 0.255 for Emap2lig-Find. Match achieved 86.6% overall matching accuracy, with a mean matching time of 0.09 s per candidate region, substantially faster than conventional reverse docking. Build reduced the median root-mean-square deviation (RMSD) of top-1 poses from 1.81 Å with the official model to 1.21 Å. In end-to-end blind evaluation across 77 complexes containing organic small molecules, LigandSeek achieved an all-atom modelling success rate of 67.5% (top-1 RMSD < 3 Å). LigandSeek connects ligand localisation, identity matching and pose reconstruction to generate accurate all-atom ligand poses from cryo-EM density maps. It provides a new tool for drug discovery and high-throughput cryo-EM screening.

# Overview

{{pptfig:"画图/总览图.pptx"|fig-overview_v2}}

LigandSeek takes protein and nucleic acid receptor structures, either deposited or automatically modelled by CryoAtom2, together with three-dimensional cryo-EM density maps.

We represent protein and nucleic acid receptors uniformly as $A = \{(a_i, x_i)\}_{i=1}^{n}$. Here, $n$ is the number of receptor atoms, and $x_i \in \mathbb{R}^3$ is the spatial position of atom $i$. The representation $a_i$ encodes the atom's attributes, such as its element type and amino acid or nucleotide type. These attributes are represented by a 50-dimensional feature vector for each receptor atom.

Let $M_{exp} \in \mathbb{R}^{D \times H \times W}$ denote the voxelised three-dimensional cryo-EM density map. The receptor structure yields a simulated density map $M_{sim} \in \mathbb{R}^{D \times H \times W}$ of the same dimensions. From $M_{exp}$ and $M_{sim}$, we construct a 56-channel multi-view density bank $M \in \mathbb{R}^{56 \times D \times H \times W}$.

{{figref:fig-overview_v2}} shows the model inputs, outputs and overall workflow. LigandSeek reconstructs ligand poses end to end through three stages: Find, Match and Build. The 50-dimensional receptor-atom features and the multi-view density bank are the main inputs shared by all three stages. {{figref:fig-method-v4}} shows the overall network architecture, with further details provided in Methods.

Find combines receptor information and experimental density information to predict ligand regions. It produces $J$ candidate ligand regions (blobs), expressed as:

$$
\mathbf{Find}(A, M) \longrightarrow \{B_j\}_{j=1}^{J}
$$

Each $B_j$ is a 26-connected region in the three-dimensional voxel grid.

Match uses the multi-view density bank $M$, the surrounding receptor pocket $A$ around each blob and auxiliary features from Find ($\mathrm{AUX}$), assigning the predicted blobs $\{B_j\}_{j=1}^{J}$ to user-provided ligand identities $\{S_k\}_{k=1}^{K}$ in the PDB entry. Here, $K$ denotes the number of ligand identities present in that PDB entry. Match determines whether each blob is a false-positive Find prediction and, if it is not, assigns its ligand identity:

$$
\begin{aligned}
&\mathbf{Match}(M, A, AUX; B_j, \{S_k\}_{k=1}^{K}) \\
&\quad = \begin{cases}
(1, S_k), & \begin{aligned}
&\text{if } B_j \text{ is not a false positive} \\
&\text{and has ligand identity } S_k
\end{aligned} \\
(0, \emptyset), & \text{if } B_j \text{ is a false positive}
\end{cases}
\end{aligned}
$$

Once Find locates a ligand region and Match assigns its chemical identity (SMILES), downstream molecular docking tools can reconstruct the three-dimensional ligand pose. We provide interfaces to commonly used docking tools, allowing users to select the appropriate tool for their needs. We also minimally modified the PocketXMol architecture to use density information as additional docking guidance alongside receptor information. We then loaded its official weights for fine-tuning and adopted PocketXMol-tuned as the default Build model.

Build takes a specified initial binding site $p \in R^3$, a small-molecule identity represented by SMILES and the surrounding pocket environment $P$. It also accepts optional guiding density information $M \in \mathbb{R}^{D \times H \times W}$ and generates all-atom coordinates for the small molecule.

We tested the framework on a non-redundant set of 179 PDB entries. To evaluate Find's localisation performance, we computed semantic and instance-level metrics for each full density map. To evaluate Match's identity matching and Build's molecular docking performance, we assessed the relevant ligands from these PDB entries.

{{pptfig:"画图/Method总图.pptx"|fig-method-v4}}
