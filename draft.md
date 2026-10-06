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

Match uses the density bank $M$, the receptor pocket $A$ surrounding each blob and auxiliary features from Find ($\mathrm{AUX}$) to associate the predicted blobs $\{B_j\}_{j=1}^{J}$ with user-provided ligand identities $\{S_k\}_{k=1}^{K}$ in the PDB entry. Here, $K$ denotes the number of ligand identities present in that complex. Specifically, it determines whether each blob is a false-positive Find prediction and, if not, identifies its corresponding ligand identity:

$$
\begin{aligned}
\mathbf{Match}(M, A, AUX; B_j, \{S_k\}_{k=1}^{K}) 
&= \begin{cases}
(1, S_k), & \begin{aligned}
&\text{if } B_j \text{ is not a false positive and corresponds to ligand identity $S_k$}
\end{aligned} \\
(0, \emptyset), & \text{if } B_j \text{ is a false positive}
\end{cases}
\end{aligned}
$$

Once Find locates a ligand region and Match assigns its chemical identity, downstream molecular docking tools can reconstruct the three-dimensional ligand pose. While we provide modular interfaces to standard docking tools, we developed a density-guided variant of PocketXMol as the default Build model. Specifically, PocketXMol was adapted with local density conditioning and fine-tuned from official weights, enabling pose generation constrained by both the receptor environment and experimental density.

Build takes a specified initial binding site $p \in R^3$, a small-molecule identity represented by SMILES and the surrounding pocket environment $P$. It also accepts optional guiding density information $M \in \mathbb{R}^{D \times H \times W}$ and generates all-atom coordinates for the small molecule.

We tested the framework on a non-redundant set of 179 PDB entries. To evaluate Find's localisation performance, we computed semantic and instance-level metrics for each full density map. To evaluate Match's identity matching and Build's molecular docking performance, we assessed the relevant ligands from these PDB entries.

{{pptfig:"画图/Method总图.pptx"|fig-method-v4}}

# Results

## Stage 1

### Stage 1: Evaluation metrics

For a given PDB structure, let the model predict $N_{pred}$ three-dimensional candidate blobs, $\{B_i\}_{i=1}^{N_{pred}}$. The structure contains $N_{gt}$ ground-truth ligand instances, $\{G_j\}_{j=1}^{N_{gt}}$, where $G_j$ denotes the ligand region of instance $j$. We set the bidirectional coverage threshold to $\tau \in \{0.3, 0.5\}$.

We evaluated Find at both the semantic and instance levels. At the semantic level, performance was measured using the Dice score.

At the instance level, predicted instances $\{B_i\}_{i=1}^{N_{pred}}$ and ground-truth instances $\{G_j\}_{j=1}^{N_{gt}}$ form the two vertex sets of a bipartite graph. An edge connects $B_i$ and $G_j$ if each covers at least a fraction $\tau$ of the other. We then used the Hungarian algorithm to obtain a maximum matching between the two sets. Let $N^{\mathrm{1to1}}_{\tau}$ be the number of successfully matched instance pairs. We define one-to-one precision and recall as:

$$
\operatorname{1to1P}_{\tau}
=
\frac{N^{\mathrm{1to1}}_{\tau}}{N_{\mathrm{pred}}},
\qquad
\operatorname{1to1R}_{\tau}
=
\frac{N^{\mathrm{1to1}}_{\tau}}{N_{\mathrm{gt}}},
$$

These quantities yield the one-to-one F1 score at threshold $\tau$, $\operatorname{one-to-one F1}_{\tau}$. Ranking predicted instances by their mean voxel probability yields the corresponding one-to-one precision–recall area under the curve (PRAUC), $\operatorname{one-to-one PRAUC}_{\tau}$.

One-to-one metrics exclude both one-to-many and many-to-one matches between predicted and ground-truth instances. For example, if one predicted blob covers several ground-truth ligands, at most one pair can count as a successful match. These metrics require accurate instance localisation and separation, penalising incorrect splitting or merging as well as localisation errors. They therefore provide a precise assessment of the model's performance.

### Stage 1: Results

Panels a, c and e of {{figref:stage1-main-sixpanel}} show predictions on the full test set. Panels b, d and f show evaluations restricted to small molecules. Ground-truth and predicted instances from other categories, such as sugars and metal ions, were excluded from both numerators and denominators.

We compared LigandSeek-Find using either deposited or CryoAtom2-reconstructed receptors with the density-only method Emap2lig-Find ({{figref:stage1-main-sixpanel|a,b}}). Across the full test set, their mean Dice scores were 0.584, 0.477 and 0.050, respectively. Their mean one-to-one PRAUC@0.3 scores were 0.663, 0.541 and 0.255, respectively ({{figref:stage1-main-sixpanel|a}}). At the stricter matching threshold of 0.5, their mean one-to-one PRAUC@0.5 scores were 0.558, 0.447 and 0.126, respectively. LigandSeek-Find outperformed Emap2lig-Find even without deposited receptor structures as input, and this trend persisted in the small-molecule test subset.

Panels c and d compare LigandSeek-Find directly against Emap2lig-Find using one-to-one PRAUC@0.3 ({{figref:stage1-main-sixpanel|c,d}}). With CryoAtom2-reconstructed receptors, LigandSeek-Find outperformed Emap2lig-Find on 112 structures, performed comparably on 40 and was inferior on only 27 across the full test set ({{figref:stage1-main-sixpanel|c}}), demonstrating a substantial overall advantage. Emap2lig primarily targets small-molecule identification and modelling, and its detection performance was better for small molecules than across all ligand categories, as shown in {{figref:stage1-main-sixpanel|a,b}}.

Across the 179 test PDB entries, each complex contained an average of 14.0 ground-truth ligand instances, whereas Emap2lig-Find predicted an average of 353.9 candidate regions per entry. This flood of false positives severely undermined its precision despite acceptable recall ({{figref:stage1-main-sixpanel|e,f}}). Because downstream tasks cannot tolerate overwhelming candidate pools, inflating recall at the expense of precision is impractical. In contrast, LigandSeek-Find balanced precision and recall effectively ({{figref:stage1-main-sixpanel|e,f}}). While this low precision directly depressed the Dice score of Emap2lig-Find, its top-k success rates remained moderate ({{figref:e2e-all-find-match}}, {{figref:e2e-small-pipeline|a}}), indicating that true instances were still ranked preferentially near the top. Because PRAUC evaluates candidate ranking quality rather than unranked voxel overlap, its PRAUC was correspondingly much higher than its Dice score.

{{pptfig:"画图/stage1结果.pptx"|stage1-main-sixpanel}}

### Stage 1: Representative cases

Four representative cases showed that LigandSeek-Find covered ligand regions more completely than the density-only method Emap2lig-Find and detected regions that it missed ({{figref:stage1-fourcase-main|a–d}}). In the viral replication-associated protein complex 9PQM, both methods detected most of the region occupied by the ATP analogue ATPγS. LigandSeek-Find and Emap2lig-Find achieved Dice scores of 0.816 and 0.766 for this ligand instance, respectively ({{figref:stage1-fourcase-main|a}}). For cholesterol in 9UWI, Emap2lig-Find predictions were concentrated within the ground-truth ligand region, achieving a precision of 0.990 but covering only 0.300 of that region. LigandSeek-Find increased coverage to 0.812, recovering more of the missed ligand region ({{figref:stage1-fourcase-main|b}}). At the NADPH binding site in 9WUP, Emap2lig-Find produced no prediction overlapping the ground-truth ligand region. LigandSeek-Find covered 0.922 of that region in the same comparison ({{figref:stage1-fourcase-main|c}}). Similarly, at the ADP site in 9RMI, Emap2lig-Find covered only 0.103 of the ground-truth region, whereas LigandSeek-Find covered 0.883 ({{figref:stage1-fourcase-main|d}}). These local comparisons demonstrated advantages in both detecting ligand regions and delineating their spatial boundaries more accurately.

LigandSeek-Find retained its main detection and coverage advantages in these cases when deposited receptor structures were replaced with receptors automatically reconstructed by CryoAtom2. With reconstructed receptors, the instance Dice scores for 9PQM, 9UWI and 9WUP were 0.816, 0.848 and 0.715, respectively. These scores were close to those obtained with deposited receptors and exceeded those of Emap2lig-Find ({{figref:stage1-fourcase-main|a–c}}). The 9RMI case illustrated a loss of precision after receptor replacement. For this ligand instance, the predicted region extended beyond the ligand, reducing precision from 0.607 to 0.396 and the Dice score from 0.719 to 0.532 ({{figref:stage1-fourcase-main|d}}). Nevertheless, the prediction still covered 0.810 of the ground-truth ligand region, and its Dice score exceeded the 0.131 achieved by Emap2lig-Find. Thus, across these four cases, LigandSeek-Find usaually retained good detection performance with CryoAtom2-reconstructed receptors when deposited receptor structures were unavailable.

{{pptfig:"画图/stage1可视化.pptx"|stage1-fourcase-main}}

## Stage 2

### Stage 2: Evaluation protocol

Let $B_i$ denote the $i$th blob predicted by Find. Let $G_j$ denote the ground-truth ligand region of instance $j$ in the same PDB entry. Their bidirectional coverage is defined as:

$$
c_{ij}^{B}=\frac{|B_i\cap G_j|}{|B_i|},\qquad
c_{ij}^{G}=\frac{|B_i\cap G_j|}{|G_j|}.
$$

Here, $c_{ij}^{B}$ is the fraction of the blob covered by the ground-truth ligand region. Conversely, $c_{ij}^{G}$ is the fraction of the ground-truth ligand region covered by the blob. For predicted ligand $B_i$, we present the ground-truth instances meeting a coverage threshold of 0.30 in both directions as a set:

$$
\mathcal J_i=\left\{j:c_{ij}^{B}\geq 0.30\ \land\ c_{ij}^{G}\geq 0.30\right\}.
$$

We label $B_i$ as foreground if $\mathcal J_i$ is non-empty, meaning there is a ground-truth ligand that both coverage fractions reach at least 30%, otherwise, we label the blob as background under this criterion. For each foreground blob, we assign a unique ground-truth ligand instance by maximising the geometric mean of the two coverage fractions:

$$
j_i^*=\underset{j\in\mathcal J_i}{\arg\max}\;\sqrt{c_{ij}^{B}c_{ij}^{G}}.
$$

The SMILES representation of that instance defines the ligand identity label for $B_i$.

After training Find, we ran inference with deposited receptors on 1,650 training and 200 validation PDB entries. The resulting candidate blobs and the following features formed the training and validation sets for Match.

Find also processed the 179 test PDB entries separately with deposited and CryoAtom2-reconstructed receptors. Respectively, these conditions yielded 1,238 and 1,160 blobs that were defined as foreground blob and corresponding ligands which could be successfully parsed. They also yielded 413 and 489 false-positive blobs, respectively. The Match test sets included all these blobs, including false positives, under the same two receptor conditions. We applied no additional filtering or processing to the blobs, so this evaluation reflected the operation of the actual inference pipeline.

We refer to the main model, which uses the **full voxel feature set**, pocket context and auxiliary information AUX, as strongest. We also trained three ablation models on the same samples using the same training protocol. The voxel-only model used the full voxel feature set, density-only used only experimental density, and pocket-only used only pocket information.

### Stage 2: Results

{{pptfig:"画图/stage2结果.pptx"|stage2-radar-pair}}

{{figref:stage2-radar-pair|a}} shows false-positive detection and ligand identity matching for the four model variants with deposited receptors. {{figref:stage2-radar-pair|b}} shows the corresponding results with CryoAtom2-reconstructed receptors. We treated each candidate blob as one sample and computed foreground F1 and ligand identity matching accuracy across blobs. We also calculated matching accuracy separately for small molecules, metal ions, sugars and peptides.

With deposited receptors, strongest achieved an overall matching accuracy of 87.8% and a foreground F1 of 86.0%. Matching accuracy was 92.5% for small molecules and 93.1% for metal ions, both exceeding the 70.8% (201/284) achieved for sugars. Peptides accounted for only 0.08% of all ligands in the full dataset. We retained the original test distribution without increasing the representation of this rare category, leaving only one peptide test case.

The voxel-only model achieved a foreground F1 of 84.1% and an overall matching accuracy of 83.7%. Its matching accuracy was slightly below strongest's 87.8%, but substantially above density-only's 78.6% and pocket-only's 79.4%. These comparisons showed that the **full voxel feature set** provided important discriminative information.

Overall matching accuracy showed no marked decline for any of the four models when deposited receptors were replaced with CryoAtom2-reconstructed receptors. By contrast, Find showed some reduction in ligand localisation performance ({{figref:stage1-main-sixpanel|a,b}}). Match was therefore more robust to the change in receptor source.

{{pptfig:"画图/stage2结果.pptx"|stage2-strongest-pair}}

{{figref:stage2-strongest-pair|a,b}} stratifies strongest's results by the number of SMILES representations in each PDB entry. This number corresponds to the ligand identities competing for assignment to each candidate region in that entry. Identity discrimination became more difficult as the number of competing identities increased. For example, with deposited receptors, small-molecule matching accuracy fell from 94.8% in entries with two identities to 65.9% in entries with four. Nevertheless, when fewer than 4 identities competed, matching accuracy generally exceeded 80% across ligand categories. These cases accounted for approximately 80% of tasks, making Match's accuracy acceptable for practical use.

Metal ions retained high matching accuracy across all groups and were easier to distinguish from other ligand identities. This reflected their greater chemical separability from the other ligands. During identity matching, we provided no prior information about the ligand category within each candidate blob. Thus, the high accuracy did not arise from the limited number of metal-ion types.

We also evaluated EMERALD-ID, which supports only small molecules. EMERALD-ID docks candidate small-molecule SMILES representations individually at each site, then uses the resulting docking scores to infer the most likely ligand identity. Its computational complexity per PDB entry is $O(N_g \times K)$. Here, $N_g$ is the number of small-molecule ligand instances, and $K$ is the number of small-molecule identities. In contrast, our model supports GPU acceleration through vectorised computation and required a mean of only 0.09 s to match each candidate blob. This mean runtime was measured on an NVIDIA H100 GPU.

EMERALD-ID cannot use GPU acceleration and required a mean of 64 min to dock one small-molecule identity at one site on a single CPU core. Its runtime was almost prohibitive for PDB entries in the high-cost tail, which required docking more small molecules. We therefore defined a separate evaluation subset for EMERALD-ID within the original test set. Among entries containing small molecules, we excluded the 10% with the highest $N_g \times K$, retaining 357 small-molecule sites from 84 PDB entries. We supplied all small-molecule identities from the same PDB entry for matching. Chemical preparation failed at many sites, preventing EMERALD-ID from returning results. We therefore calculated its matching accuracy only for sites that returned valid results. {{figref:stage2-radar-pair|a}} and {{figref:stage2-radar-pair|b}} show its performance with deposited and CryoAtom2-reconstructed receptors, respectively.

{{pptfig:"画图/E2E结果.pptx"|e2e-all-find-match}}

{{pptfig:"画图/E2E结果.pptx"|e2e-small-pipeline}}
