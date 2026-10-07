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

LigandSeek-Find retained its main detection and coverage advantages in these cases when deposited receptor structures were replaced with receptors automatically reconstructed by CryoAtom2. With reconstructed receptors, the instance Dice scores for 9PQM, 9UWI and 9WUP were 0.816, 0.848 and 0.715, respectively. These scores were close to those obtained with deposited receptors and exceeded those of Emap2lig-Find ({{figref:stage1-fourcase-main|a–c}}). The 9RMI case illustrated a loss of precision after receptor replacement. For this ligand instance, the predicted region extended beyond the ligand, reducing precision from 0.607 to 0.396 and the Dice score from 0.719 to 0.532 ({{figref:stage1-fourcase-main|d}}). Nevertheless, the prediction still covered 0.810 of the ground-truth ligand region, and its Dice score exceeded the 0.131 achieved by Emap2lig-Find. Thus, across these four cases, LigandSeek-Find usually retained good detection performance with CryoAtom2-reconstructed receptors when deposited receptor structures were unavailable.

{{pptfig:"画图/stage1可视化.pptx"|stage1-fourcase-main}}

## Stage 2

### Stage 2: Evaluation protocol

Let $B_i$ denote the $i$-th candidate blob predicted by Find, and let $G_j$ denote the ground-truth ligand region of instance $j$ in the same PDB entry. Their bidirectional coverage is defined as:

$$
c_{ij}^{B}=\frac{|B_i\cap G_j|}{|B_i|},\qquad
c_{ij}^{G}=\frac{|B_i\cap G_j|}{|G_j|},
$$

where $c_{ij}^{B}$ is the fraction of the blob covered by the ground-truth ligand region, and $c_{ij}^{G}$ is the fraction of the ground-truth ligand region covered by the blob. For each candidate blob $B_i$, the indices of ground-truth instances meeting a bidirectional coverage threshold of 0.30 are collected into the set:

$$
\mathcal J_i=\left\{j:c_{ij}^{B}\geq 0.30\ \land\ c_{ij}^{G}\geq 0.30\right\}.
$$

A candidate blob $B_i$ is labeled as foreground if $\mathcal J_i$ is non-empty (i.e. sharing at least 30% bidirectional coverage with a ground-truth ligand); otherwise, it is labeled as background. For each foreground blob, we assign a unique ground-truth ligand instance by maximising the geometric mean of the two coverage fractions:

$$
j_i^*=\underset{j\in\mathcal J_i}{\arg\max}\;\sqrt{c_{ij}^{B}c_{ij}^{G}}.
$$

The SMILES string of this instance defines the ground-truth ligand identity for $B_i$.

After training LigandSeek-Find, we used it to run inference with deposited receptors on 1,650 training and 200 validation PDB entries. The resulting candidate blobs and associated auxiliary features formed the training and validation sets for Match.

We also ran inference with LigandSeek-Find on the 179 test PDB entries using both deposited and CryoAtom2-reconstructed receptors. These conditions yielded 1,238 and 1,160 blobs defined as foreground blobs with corresponding parsable ligands, alongside 413 and 489 false-positive blobs, respectively. The Match test set incorporated all these candidate blobs without manual pre-filtering, ensuring that the benchmark accurately reflected real-world pipeline performance.

We refer to the main model, which integrates the full voxel features, pocket context and auxiliary information, as strongest. For comparison, we trained three ablation models under identical protocols: voxel-only (using only the full voxel features), density-only (using only the experimental density), and pocket-only (using only the pocket information).

### Stage 2: Results

{{pptfig:"画图/stage2结果_忽视2+2例子.pptx"|stage2-radar-pair}}

{{figref:stage2-radar-pair|a}} shows false-positive detection and ligand identity matching for four model variants with deposited receptors. {{figref:stage2-radar-pair|b}} shows the corresponding false-positive detection and identity matching results with CryoAtom2-reconstructed receptors. We treated each candidate blob as one sample and computed foreground F1 and ligand identity matching accuracy across blobs. We also calculated matching accuracy separately for small molecules, metal ions, sugars and peptides.

With deposited receptors, strongest achieved an overall matching accuracy of 87.8% and a foreground F1 of 86.0%. Matching accuracy was 92.5% for small molecules and 93.1% for metal ions, both exceeding the 70.8% (201/284) achieved for sugars. The voxel-only model achieved a foreground F1 of 84.1% and an overall matching accuracy of 83.7%. Its matching accuracy was slightly lower than that of strongest (87.8%) but substantially higher than those of density-only (78.6%) and pocket-only (79.4%). These comparisons indicated that the full voxel feature set contributed substantially to ligand discrimination.

With CryoAtom2-reconstructed receptors, strongest still achieved 86.6% overall matching accuracy and a foreground F1 of 82.9%, which showed no marked decline for any of the four models. By contrast, Find showed a little reduction in ligand localisation performance ({{figref:stage1-main-sixpanel|a,b}}). Match was therefore more robust to the change in receptor source.

{{pptfig:"画图/stage2结果_忽视2+2例子.pptx"|stage2-strongest-pair}}

{{figref:stage2-strongest-pair|a,b}} stratifies strongest's results by the number of SMILES representations in each PDB entry. This number corresponds to the ligand identities competing for assignment to each candidate region. Identity discrimination became more difficult as the number of competing identities increased. For example, with deposited receptors, small-molecule matching accuracy fell from 94.8% in entries with two identities to 65.9% in entries with four. Nevertheless, when fewer than 4 identities competed, matching accuracy generally exceeded 80% across ligand categories. These cases accounted for approximately 80% of practical tasks, making Match's accuracy acceptable for practical use.

Metal ions retained high matching accuracy across all groups and were easier to distinguish from other ligand identities. This reflected their greater chemical separability from the other ligands. During identity matching, we provided no prior information about the ligand category within each candidate blob. Thus, the high accuracy did not arise from the limited number of metal-ion types.

We also evaluated EMERALD-ID, whose supported ligand scope is limited to small molecules. EMERALD-ID docks candidate small-molecule SMILES representations individually at each site, then uses the resulting docking scores to infer the most likely ligand identity. Its computational complexity per PDB entry is $O(N_g \times K)$, where $N_g$ counts small-molecule ligand instances and $K$ counts small-molecule identities. In contrast, our model supports GPU acceleration through vectorised computation and required a mean of only 0.09 s to match each candidate blob. This mean runtime was measured on an NVIDIA H100 GPU.

EMERALD-ID cannot use GPU acceleration and required a mean of 64 min to dock one small-molecule identity at one site on a single CPU core. Its runtime was almost prohibitive for PDB entries in the high-cost tail, which required docking more small molecules. We therefore defined a separate evaluation subset for EMERALD-ID within the original test set. Among entries containing small molecules, we excluded the 10% with the highest $N_g \times K$, retaining 357 small-molecule sites from 84 PDB entries. We supplied all small-molecule identities from the same PDB entry for matching. Chemical preparation failed at many sites, preventing EMERALD-ID from returning results. We therefore calculated its matching accuracy only for sites that returned valid results. {{figref:stage2-radar-pair|a}} and {{figref:stage2-radar-pair|b}} show its performance with deposited and CryoAtom2-reconstructed receptors, respectively.

## Stage 3

### Stage 3: Comparison of official and fine-tuned PocketXMol models

We compared the official PocketXMol model with our fine-tuned version. The official model accepts a ligand SMILES representation and its binding pocket, generating 50 candidate poses by default.

PocketXMol provides two pocket definitions for docking, with the ligand-envelope pocket using a 10 Å envelope around the ligand atoms. All atoms of a receptor residue are included if at least one lies within the envelope, giving the Envelope pocket. The centre-defined pocket comprises all receptor atoms within a 15 Å sphere centred on the binding site, termed the Centre pocket.

We treated these pocket definitions as separate training and testing conditions. We trained one fine-tuned model for each definition and evaluated each model under its corresponding condition.

To assess fine-tuning, we used all single-residue organic small molecules with no atoms missing relative to their templates from the 179 PDB entries. This test set comprised a total of 446 ligand instances.

We used two complementary docking metrics based on heavy-atom root-mean-square deviation (RMSD). Top-1 RMSD measures the error of the top-1 pose, ranked first by the model's own score, and reflects accuracy in blind evaluation. Best RMSD measures the lowest error among the 50 generated candidates, defining the best-of-50 pose. This metric measures the upper limit of the model's pose sampling capacity.

Across the 446 test instances, density-guided PocketXMol-tuned achieved substantially greater pose accuracy than PocketXMol-official under every test condition ({{figref:stage3-official-tuned}}). The improvement was particularly pronounced with the Centre pocket and deposited receptors. Without density guidance, the official model had considerable translational and rotational freedom within the spacious 15 Å pocket. It readily settled in geometrically plausible cavities outside the active binding site. Its median top-1 RMSD reached 2.31 Å, with only 44.7% of predictions achieving RMSD < 2 Å. Local three-dimensional constraints from the cryo-EM density substantially reduced the fine-tuned model's median top-1 RMSD to 1.29 Å. Success rates rose to 73.8% at RMSD < 2 Å and 83.4% at RMSD < 3 Å. For best-of-50 poses, fine-tuning substantially reduced the median minimum RMSD from 1.43 Å to 0.77 Å. The fraction achieving RMSD < 2 Å increased sharply from 61.6% to 93.0%.

Fine-tuning also improved docking accuracy when both models used the more tightly defined Envelope pocket. With deposited receptors, median top-1 RMSD fell from 1.55 Å to 1.14 Å. The corresponding success rate at RMSD < 2 Å increased from 62.9% to 78.0%. Median best RMSD fell from 0.94 Å to 0.69 Å, with 97.1% of best-of-50 poses achieving RMSD < 2 Å. These results showed that cryo-EM density provided effective docking guidance even when the pocket boundaries were already tightly constrained.

The fine-tuned model was also robust to receptor modelling errors introduced by CryoAtom2. Replacing deposited receptors with CryoAtom2-reconstructed receptors increased the official model's median top-1 RMSD from 2.31 Å to 3.01 Å with Centre pockets. Its success rate at RMSD < 2 Å fell to 39.9%. By comparison, PocketXMol-tuned retained a median top-1 RMSD of 1.44 Å and a success rate of 67.5% at RMSD < 2 Å. Its performance substantially exceeded that of the official model even with deposited receptors.

{{pptfig:"画图/stage3结果.pptx"|stage3-official-tuned}}

### Stage 3: Comparison with Emap2lig-Build

We also compared PocketXMol-tuned using Centre pockets with the ligand pose prediction tool Emap2lig-Build. Emap2lig-Build accepts a guiding region and a cryo-EM density map. In its default workflow, the guiding region is the three-dimensional blob predicted by Emap2lig-Find in the preceding stage.

A fair comparison therefore required restricting evaluation to ligand instances for which Emap2lig-Find returned a corresponding blob. Of the 446 small-molecule test instances, Emap2lig-Find returned qualifying blobs for only 237. Each qualifying blob shared at least 30% bidirectional coverage with the ground-truth ligand region. We compared PocketXMol-tuned and Emap2lig-Build only on these instances ({{figref:stage3-find-hit-head-to-head}}).

Across these 237 jointly evaluable instances, PocketXMol-tuned using Centre pockets substantially outperformed Emap2lig-Build. With deposited and CryoAtom2-reconstructed receptors, median top-1 RMSD was 0.90 Å and 1.01 Å, respectively, substantially below Emap2lig-Build's 1.85 Å. Median best-of-50 RMSD was 0.65 Å and 0.70 Å, respectively, also substantially below Emap2lig-Build's 1.33 Å.

{{pptfig:"画图/stage3结果.pptx"|stage3-find-hit-head-to-head}}

### Stage 3: Representative cases

We analysed six representative instances to examine how receptor pockets and experimental density provide complementary constraints on pose generation ({{figref:stage3-cases-main}}).

The first group illustrated typical errors in receptor-only docking without experimental density guidance ({{figref:stage3-cases-main|a–c}}). In 9Q16, 9UB7 and 9R3D, PocketXMol-official avoided receptor clashes, with zero clashing atom pairs in each case. However, without density guidance, its poses shifted within the pocket cavity or adopted flipped conformations. Only 46%–77% of heavy atoms reached the recommended density threshold, denoted by D, and top-1 RMSD reached 3.84–5.69 Å. With density guidance, PocketXMol-tuned placed ligand atoms accurately within the experimental density, increasing D to 80%–100%. RMSD fell sharply to 0.76–1.05 Å, while all three poses remained free of receptor clashes.

The second group illustrated the shortcomings of density-only fitting that ignores receptor steric constraints ({{figref:stage3-cases-main|d–f}}). In 9U7J, 9WUP and 9WQ3, Emap2lig-Build's top-1 poses produced 10, 15 and 11 clashing pairs with surrounding receptor atoms, respectively. Its pose in 9WQ3 also deviated markedly from the deposited position, with an RMSD of 9.30 Å. By combining receptor geometry with density information, PocketXMol-tuned eliminated all receptor clashes and consistently achieved RMSD values of 0.52–1.41 Å.

These cases showed that the receptor structure imposes steric exclusion constraints, whereas cryo-EM density constrains ligand position and conformation. PocketXMol-tuned combined these complementary sources of information to reconstruct ligand poses with high accuracy.

{{pptfig:"画图/stage3可视化.pptx"|stage3-cases-main}}

## End-to-end

In practical cryo-EM structure determination, researchers work with unannotated three-dimensional density maps and unknown binding sites. To assess automated modelling in this setting, we connected Find, Match and Build into a single end-to-end pipeline. We evaluated region detection and identity matching across all ligand categories, and full pose reconstruction for organic small molecules with no missing atoms.

Find ranks candidate ligand regions by descending confidence, producing Rank 1, Rank 2 and subsequent candidates. For each PDB entry, the pipeline examines these candidates in order within a search budget of $K$ attempts. A PDB entry is classified as successful if any attempt within that budget completes the task.

For end-to-end region detection and identity matching across all ligand categories, we applied the following accounting rules. A false-positive candidate predicted by Find consumes one attempt, after which the pipeline examines the next candidate. If a candidate corresponds to a ground-truth ligand with at least 30% coverage in both directions, Match assigns its ligand identity. Correct identity matching completes the task; incorrect matching consumes one attempt. The pipeline continues until the task succeeds or the $K$-attempt budget is exhausted.

For end-to-end modelling of single-residue small molecules with no missing atoms, false-positive candidates likewise consume one attempt before the next candidate is examined.

If a candidate corresponds to a non-small-molecule ligand but Match assigns a small-molecule identity, the attempt is counted as a failure and charged. Otherwise, the candidate is skipped without consuming the attempt budget.

If a candidate corresponds to a small molecule with at least 30% bidirectional coverage, incorrect identity matching consumes one attempt. A correctly matched small molecule that fails the single-residue, no-missing-atom criteria is skipped without charge. Otherwise, PocketXMol-tuned performs docking, and success is determined from the top-1 or best-of-50 pose and the corresponding RMSD threshold.

When a ligand outside the single-residue, complete organic small-molecule subset is correctly detected and matched, we skip docking and charge no attempt. This ensures that all evaluated docking tasks use the same downstream tool, PocketXMol-tuned. However, a region corresponding to a true non-small-molecule ligand is charged if it is misidentified as a small molecule. It remains an unresolved distractor and counts as a failed attempt.

### End-to-end region detection and identity matching across ligand categories

{{pptfig:"画图/E2E结果.pptx"|e2e-all-find-match}}

We first evaluated region detection by Find and exact ligand identity matching by Find+Match across the 179 independent test PDB entries ({{figref:e2e-all-find-match}}). These entries contained coexisting ligand categories, including small molecules, ions and sugars. With a single attempt ($K=1$) and deposited receptors (GT), Find detected a ligand region in 148 entries (82.7%). Of these, 142 entries (79.3% of the full test set) also received the exactly correct SMILES representation. With CryoAtom2-reconstructed receptors (CA2), the corresponding counts were 134 (74.9%) for region detection and 120 (67.0%) for exact identity matching. As the attempt budget increased to 10, success rates rapidly approached 92.2% and 87.7% under the two receptor conditions, respectively. By comparison, Emap2lig-Find detects ligand regions but does not identify their chemical identities. It detected regions in only 71 entries (39.7%) at $K=1$ and 93 entries (52.0%) within $K \le 10$.

### End-to-end reconstruction of all-atom small-molecule poses

{{pptfig:"画图/E2E结果.pptx"|e2e-small-pipeline}}

We evaluated the complete detection, matching and pose reconstruction pipeline in 77 PDB entries containing single-residue organic small molecules with no missing atoms ({{figref:e2e-small-pipeline|b,c}}). PocketXMol received the centre of the ligand region predicted by Find as its binding-site input, which also defined the pocket. With CryoAtom2-reconstructed receptors, no stage of the pipeline used the deposited receptor structure as input.

The strictest evaluation allowed one attempt ($K=1$), selected only the top-1 pose and required RMSD < 2 Å. Under this criterion, 44/77 entries (57.1%) succeeded with deposited receptors, compared with 34/77 (44.2%) with CryoAtom2-reconstructed receptors. At RMSD < 3 Å, the corresponding counts were 50/77 (64.9%) and 41/77 (53.2%). Allowing up to 10 charged attempts ($K \le 10$) increased top-1 success with deposited receptors to 66.2% at RMSD < 2 Å. At RMSD < 3 Å, 55/77 entries (71.4%) achieved successful reconstruction. With CryoAtom2-reconstructed receptors, 46/77 entries (59.7%) succeeded at RMSD < 2 Å and 52/77 (67.5%) at RMSD < 3 Å.

For best-of-50 poses within $K \le 10$, success at RMSD < 2 Å reached 75.3% and 67.5% with deposited and CryoAtom2-reconstructed receptors, respectively. At RMSD < 3 Å, the corresponding success rates were 76.6% and 75.3%.

{{figref:e2e-small-pipeline|a}} further separates the success rates of individual pipeline stages. Within the first 10 charged attempts ($K \le 10$), Find alone succeeded in 89.6% and 88.3% of entries with deposited and CryoAtom2-reconstructed receptors, respectively. Both exceeded Emap2lig-Find's success rate of 70.1% in this subset. Requiring both Find and Match to succeed yielded rates of 83.1% and 81.8%, respectively ({{figref:e2e-small-pipeline|a}}).

### Representative cases

We selected three representative cases, all using CryoAtom2-reconstructed receptors rather than deposited receptor structures as input ({{figref:e2e-flow-9llg,e2e-flow-9bjj,e2e-flow-30ga}}).

In 9LLG ({{figref:e2e-flow-9llg}}), Find's Rank 1 candidate hit the ground-truth ligand region of A1EKL (R:602). Match correctly identified A1EKL among the three candidate identities PLM, A1EKL and CLR. PocketXMol-tuned then generated a top-1 pose with a heavy-atom RMSD of 0.88 Å.

{{pptfig:"画图/E2E案例可视化-端到端流程版_v3.pptx"|e2e-flow-9llg}}

In 9BJJ ({{figref:e2e-flow-9bjj}}), Find's Rank 1 candidate hit the ground-truth ligand region of ATP (B:901). Match correctly identified ATP among the three candidate identities ATP, A1AP0 and Mg²⁺. PocketXMol-tuned then generated a top-1 pose with subångström accuracy, achieving a heavy-atom RMSD of 0.80 Å.

{{pptfig:"画图/E2E案例可视化-端到端流程版_v3.pptx"|e2e-flow-9bjj}}

In 30GA ({{figref:e2e-flow-30ga}}), Find's Rank 1 candidate was a background false positive and consumed one search attempt. The Rank 2 candidate then hit ATP (N:401), and Match correctly identified ATP. PocketXMol-tuned subsequently generated a pose with a heavy-atom RMSD of 1.04 Å.

{{pptfig:"画图/E2E案例可视化-端到端流程版_v3.pptx"|e2e-flow-30ga}}
