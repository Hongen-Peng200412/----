# Supplementary Information


## Ligand-region detection at a stricter coverage threshold

We evaluated instance-level PRAUC at a stricter bidirectional coverage threshold of 0.5 using the same all-ligand and small-molecule cohorts. These comprised 179 PDB entries with 2,502 instances and 94 PDB entries with 821 small-molecule instances, respectively. For all ligands, PDB-equal means were 0.558 with GT receptors and 0.447 with CA2 receptors, compared with 0.152 for Emap2lig-Find ({{figref:stage1-strict-threshold|a}}). The corresponding small-molecule scores were 0.605, 0.499 and 0.337, preserving the same advantage ({{figref:stage1-strict-threshold|b}}).

{{pptfig:"画图/stage1结果.pptx"|stage1-strict-threshold}}

## Complete detection curves across ranked candidates

We compared detection completion across the full candidate-count range and retained the distribution of results across individual PDB entries ({{figref:stage1-completion-curves}}). All-ligand evaluation included 179 PDB entries and 2,502 instances; small-molecule evaluation included 94 PDB entries and 821 instances. Both evaluated Find alone, without requiring identity matching or pose reconstruction. Candidate–instance pairs required bidirectional coverage of at least 0.3, and each instance contributed only its first detection. Relative candidate counts of 100% and 300% allowed examining up to one and three times the ground-truth instance count, respectively.

From 100% to 300%, mean completion across all ligands increased from 66.4% to 71.7% with GT receptors and from 55.6% to 63.3% with CA2 receptors. Emap2lig-Find increased from 28.5% to 31.4% over the same candidate-count range. Corresponding small-molecule changes were 70.5% to 73.3% for GT, 59.8% to 68.5% for CA2 and 46.6% to 54.9% for Emap2lig-Find. LigandSeek-Find therefore recovered more true instances under the same candidate-count limits. Means weight PDB entries equally, while background candidates and repeated hits retain their candidate positions. The small-molecule evaluation omits only candidates assigned to non-small-molecule instances.

{{pptfig:"画图/stage1结果.pptx"|stage1-completion-curves}}

## Stage 1: Ablation of LigandSeek-Find

As shown in Table 4, we compared six model variants on the same full test set to assess the contributions of individual designs to ligand detection. Starting with a 3D U-Net receiving experimental density alone(Density only), we added difference density(+ Difference density), a multi-view density bank(+ Density bank) and receptor-atom features(+ Receptor features). We then introduced centroid-aware positional encoding in the receptor embedding head(+ Centroid encoding), followed by the final LigandSeek-Find model. The final model used receptor-atom binding probabilities predicted by the point-cloud branch for Gaussian candidate scoring, while other models used conventional inference without Gaussian candidate scoring.

According to Table 4, adding difference density improved all metrics under both GT and CA2 conditions. Moreover, the multi-view density bank further improved overall detection ability. It is noteworthy that when constructing multi-view density bank, the deterministic transformations of the same experimental and simulated receptor density do not add any additional information, but highlight ligand signals across contrasts and spatial scales while suppressing dominant receptor density.


Futhermore, we can observe that injecting the receptor information explicitly, adding centroid-aware positional encoding in the receptor embedding head, and introducing Gaussian scoring during inference also generally raise model performance to varying degrees. We refer to the model with all components as LigandSeek-Find, which has the best overall performance.

<table data-layout="booktabs" data-pagination="rows">
<caption>Table 4 | Internal ablation of LigandSeek-Find on the full test set.</caption>
<colgroup><col style="width: 28%"/><col style="width: 12%"/><col style="width: 12%"/><col style="width: 12%"/><col style="width: 12%"/><col style="width: 12%"/><col style="width: 12%"/></colgroup>
<thead>
<tr><th rowspan="2">Model</th><th colspan="3">CA2 receptors</th><th colspan="3">Deposited receptors</th></tr>
<tr><th>Dice</th><th>$\mathrm{PRAUC}_{0.3}$</th><th>$\mathrm{PRAUC}_{0.5}$</th><th>Dice</th><th>$\mathrm{PRAUC}_{0.3}$</th><th>$\mathrm{PRAUC}_{0.5}$</th></tr>
</thead>
<tbody>
<tr><td>Density only</td><td>0.394</td><td>0.446</td><td>0.342</td><td>0.394</td><td>0.446</td><td>0.342</td></tr>
<tr><td>+ Difference density</td><td>0.434</td><td>0.501</td><td>0.403</td><td>0.483</td><td>0.569</td><td>0.452</td></tr>
<tr><td>+ Density bank</td><td>0.453</td><td>0.508</td><td>0.427</td><td><strong>0.585</strong></td><td><u>0.643</u></td><td><strong>0.561</strong></td></tr>
<tr><td>+ Receptor features</td><td>0.463</td><td>0.520</td><td>0.437</td><td>0.570</td><td>0.631</td><td>0.554</td></tr>
<tr><td>+ Centroid encoding</td><td><strong>0.483</strong></td><td><u>0.536</u></td><td><u>0.444</u></td><td>0.583</td><td>0.633</td><td>0.539</td></tr>
<tr><td>LigandSeek-Find</td><td><u>0.477</u></td><td><strong>0.541</strong></td><td><strong>0.447</strong></td><td><u>0.584</u></td><td><strong>0.663</strong></td><td><u>0.558</u></td></tr>
</tbody>
</table>
<p class="table-note">Dice denotes semantic Dice; PRAUC denotes instance-level PRAUC, with subscripts indicating bidirectional coverage thresholds between predicted and ground-truth regions. CA2 denotes CryoAtom2-reconstructed receptors; deposited receptors correspond to GT. Bold and underlined values indicate the highest and second-highest scores in each column, respectively.</p>

## Stage 3: End-to-end top-k success

### Evaluation protocol (top-k success)

Top-k success measures whether an end-to-end pipeline successfully processes at least one ligand instance in a complex within a specified attempt budget.

Find ranks candidate ligand regions by descending mean probability, yielding Rank 1, Rank 2 and subsequent candidates. For each PDB entry, the pipeline examines these candidates in order for up to $K$ attempts. A PDB entry is classified as successful if any attempt within this budget succeeds.

Top-k success evaluates two basic end-to-end capabilities of our pipeline. These comprise detection and identity matching across all ligand categories, and detection, identity matching and modelling of eligible small molecules. These are single-residue organic small molecules with no atoms missing relative to their templates. Attempt-accounting rules are the same as those in the main text. The all-ligand test set contains 179 PDBs and 2,502 ligand instances; the small-molecule subset contains 77 PDBs and 446 instances. Each task was also evaluated with deposited receptors (GT) and CryoAtom2-reconstructed receptors (CA2).

### End-to-end region detection and identity matching across ligand categories

{{pptfig:"画图/E2E结果.pptx"|e2e-all-find-match}}

We first evaluated end-to-end ligand-region detection and identity matching in 179 independent test PDB entries ({{figref:e2e-all-find-match}}). These entries contained coexisting ligand categories, including small molecules, ions and sugars. Under the strictest single-attempt condition ($K=1$), end-to-end region detection and identity matching succeeded in 120 entries (67.0%) with CryoAtom2-reconstructed receptors (CA2), while region detection alone succeeded in 134 entries (74.9%). With deposited receptors (GT), the corresponding counts were 142 (79.3%) for joint success and 148 (82.7%) for region detection alone. As the attempt budget increased to 10, end-to-end success rates rapidly plateaued at 87.7% with CA2 receptors and 92.2% with GT receptors. By comparison, Emap2lig-Find detected ligand regions but could not identify their chemical identities. It detected regions in only 76 entries (42.5%) at $K=1$ and 104 entries (58.1%) within $K \le 10$.

### End-to-end reconstruction of all-atom small-molecule poses

{{pptfig:"画图/E2E结果.pptx"|e2e-small-pipeline}}

We evaluated the full end-to-end reconstruction pipeline (detection, matching, and pose reconstruction) for eligible small molecules across 77 PDB entries which contain at least one of them ({{figref:e2e-small-pipeline|b,c}}). In all evaluations, DG-PocketXmol used the centroid of the ligand region predicted by Find to define the binding site and pocket, without relying on ground-truth ligand coordinates. We tested the pipeline using both deposited receptors ({{figref:e2e-small-pipeline|b}}) and CryoAtom2-reconstructed receptors ({{figref:e2e-small-pipeline|c}}), where in the latter, no deposited structural information was used at any stage of the pipeline.

The strictest evaluation allowed one attempt ($K=1$), selected only the top-1 pose and required RMSD < 2 Å. Under this criterion, 34/77 entries (44.2%) succeeded with CryoAtom2-reconstructed receptors, compared with 44/77 (57.1%) with deposited receptors. At RMSD < 3 Å, the corresponding counts were 41/77 (53.2%) and 50/77 (64.9%). Allowing up to 10 charged attempts ($K \le 10$) increased top-1 success with CryoAtom2-reconstructed receptors to 46/77 entries (59.7%) at RMSD < 2 Å and 52/77 (67.5%) at RMSD < 3 Å. With deposited receptors, 51/77 entries (66.2%) and 55/77 (71.4%) achieved success at RMSD < 2 Å and < 3 Å, respectively.

For best-of-50 poses within $K \le 10$, success at RMSD < 2 Å reached 67.5% and 75.3% with CryoAtom2-reconstructed and deposited receptors, respectively. At RMSD < 3 Å, the corresponding success rates were 75.3% and 76.6%.

{{figref:e2e-small-pipeline|a}} further separates the success rates of individual pipeline stages. Within the first 10 charged attempts ($K \le 10$), Find alone succeeded in 88.3% and 89.6% of entries with CryoAtom2-reconstructed and deposited receptors, respectively. Both exceeded Emap2lig-Find's success rate of 76.6% in this subset. Requiring both Find and Match to succeed yielded rates of 81.8% and 83.1%, respectively.

## Find–Build comparison with correct ligand identities

Full completion curves and per-PDB distributions for the Find–Build comparison with correct ligand identities are shown in {{figref:supp-find-correct-match-build}}.

{{pptfig:"画图/E2E结果.pptx"|supp-find-correct-match-build|width=5.5in}}


## Candidate quality at limited candidate counts

To assess detection under limited candidate counts, we measured the fraction of distinct ligand instances recovered from ranked candidates. Relative candidate counts of 100% and 300% permit examining up to one and three times the ground-truth instance count per complex, respectively. At 100%, mean detection completion across all ligands was 55.6% with CA2 and 66.4% with GT, compared with 28.5% for Emap2lig-Find ({{figref:stage1-candidate-quality|c}}). For small molecules, the corresponding values were 59.8%, 70.5% and 46.6% ({{figref:stage1-candidate-quality|d}}). At 300%, small-molecule completion reached 68.5% with CA2 and 73.3% with GT, compared with 54.9% for Emap2lig-Find.

{{pptfig:"画图/stage1结果.pptx"|stage1-candidate-quality}}



## Emap2lig without an explicitly supplied contour level

Emap2lig was evaluated without an explicitly supplied EMDB-recommended contour level. The following results retain this independent condition.

### LigandSeek-Find improves ligand-region detection

We evaluated Find on 179 cryo-EM density maps with resolutions below 4.0 Å, containing ligands, released after 1 January 2026, and non-redundant with the training, validation, and internal datasets. These complexes contained 2,502 deposited ligand instances spanning multiple classes, including organic small molecules, metal ions and sugars. The small-molecule subset comprised 821 instances distributed across 94 complexes. We compared LigandSeek-Find with deposited receptors (GT) or CryoAtom2-reconstructed receptors (CA2) against the density-only baseline Emap2lig-Find[@umap2lig].

We assessed voxel-wise overlap using semantic Dice, and evaluated ligand-instance detection using instance-level metrics, including precision, recall, and the precision–recall area under the curve (PRAUC). Instance-level metrics used one-to-one matching at a bidirectional coverage threshold of 0.3 (Methods). We also evaluated PRAUC at the stricter threshold of 0.5.



With CA2 receptors, mean Dice increased from 0.050 for Emap2lig-Find to 0.477, and instance-level $\mathrm{PRAUC}_{0.3}$ increased from 0.255 to 0.541 ({{figref:stage1-overall-performance-NO_LEVEL|a}}). With GT receptors, LigandSeek-Find achieved a mean Dice of 0.584 and an instance-level $\mathrm{PRAUC}_{0.3}$ of 0.663. The advantage persisted for small molecules, with corresponding PRAUC scores of 0.573 for CA2 and 0.701 for GT, compared with 0.462 for Emap2lig-Find ({{figref:stage1-overall-performance-NO_LEVEL|b}}).

{{pptfig:"画图/stage1结果.pptx"|stage1-overall-performance-NO_LEVEL}}

Paired comparisons confirmed that the advantage extended across individual complexes ({{figref:stage1-overall-performance-NO_LEVEL|c,d}}). With CA2 receptors, LigandSeek-Find scored higher than Emap2lig-Find on 112 complexes, equally on 40 and lower on 27 across all ligands. At the stricter coverage threshold of 0.5, instance-level PRAUC remained higher with both receptor sources, including in the small-molecule subset ({{figref:stage1-strict-threshold-NO_LEVEL}}).

Across the 179 complexes, each contained an average of 14.0 ground-truth ligand instances, whereas Emap2lig-Find produced an average of 353.9 candidate regions. Its mean instance-level precision was 0.037, compared with 0.631 for LigandSeek-Find with CA2 receptors; mean recall was 0.312 versus 0.594 ({{figref:stage1-candidate-quality-NO_LEVEL|a}}). LigandSeek-Find therefore reduced false positives while recovering more ligand instances, with the same pattern observed for small molecules ({{figref:stage1-candidate-quality-NO_LEVEL|b}}). At the voxel level, additional false-positive density also reduced the overlap measured by Dice.

To assess detection under limited candidate counts, we measured the fraction of distinct ligand instances recovered from ranked candidates. Relative candidate counts of 100% and 300% permit examining up to one and three times the ground-truth instance count per complex, respectively. At 100%, mean detection completion across all ligands was 55.6% with CA2 and 66.4% with GT, compared with 25.9% for Emap2lig-Find ({{figref:stage1-candidate-quality-NO_LEVEL|c}}). For small molecules, the corresponding values were 59.8%, 70.5% and 44.2% ({{figref:stage1-candidate-quality-NO_LEVEL|d}}). At 300%, small-molecule completion reached 68.5% with CA2 and 73.3% with GT, compared with 51.6% for Emap2lig-Find.

{{pptfig:"画图/stage1结果.pptx"|stage1-candidate-quality-NO_LEVEL}}

Emap2lig-Find was closer to LigandSeek-Find in instance-level PRAUC and detection completion than in semantic Dice. Its highest-ranked candidates therefore retained substantial ligand-detection signal despite the much larger final candidate pool. LigandSeek-Find recovered more true instances at both candidate limits, providing a more compact input for downstream identity assignment. Complete detection curves and per-PDB distributions are shown in {{figref:stage1-completion-curves-NO_LEVEL}}.



### Ligand-region detection at a stricter coverage threshold

We evaluated instance-level PRAUC at a stricter bidirectional coverage threshold of 0.5 using the same all-ligand and small-molecule cohorts. These comprised 179 PDB entries with 2,502 instances and 94 PDB entries with 821 small-molecule instances, respectively. For all ligands, PDB-equal means were 0.558 with GT receptors and 0.447 with CA2 receptors, compared with 0.126 for Emap2lig-Find ({{figref:stage1-strict-threshold-NO_LEVEL|a}}). The corresponding small-molecule scores were 0.605, 0.499 and 0.293, preserving the same advantage ({{figref:stage1-strict-threshold-NO_LEVEL|b}}).

{{pptfig:"画图/stage1结果.pptx"|stage1-strict-threshold-NO_LEVEL}}

### Complete detection curves across ranked candidates

We compared detection completion across the full candidate-count range and retained the distribution of results across individual PDB entries ({{figref:stage1-completion-curves-NO_LEVEL}}). All-ligand evaluation included 179 PDB entries and 2,502 instances; small-molecule evaluation included 94 PDB entries and 821 instances. Both evaluated Find alone, without requiring identity matching or pose reconstruction. Candidate–instance pairs required bidirectional coverage of at least 0.3, and each instance contributed only its first detection. Relative candidate counts of 100% and 300% allowed examining up to one and three times the ground-truth instance count, respectively.

From 100% to 300%, mean completion across all ligands increased from 66.4% to 71.7% with GT receptors and from 55.6% to 63.3% with CA2 receptors. Emap2lig-Find increased from 25.9% to 30.1% over the same candidate-count range. Corresponding small-molecule changes were 70.5% to 73.3% for GT, 59.8% to 68.5% for CA2 and 44.2% to 51.6% for Emap2lig-Find. LigandSeek-Find therefore recovered more true instances under the same candidate-count limits. Means weight PDB entries equally, while background candidates and repeated hits retain their candidate positions. The small-molecule evaluation omits only candidates assigned to non-small-molecule instances.

{{pptfig:"画图/stage1结果.pptx"|stage1-completion-curves-NO_LEVEL}}



#### Stage 3: Fair comparison with Emap2lig-Build

We performed a fair comparison between LigandSeek's small-molecule docking engine (PocketXMol-tuned) and Emap2lig-Build, which predicts ligand poses directly from cryo-EM density without receptor information. In its official workflow, Emap2lig-Build accepts a candidate blob predicted by Emap2lig-Find as its guiding region rather than the ground-truth binding site. To mirror this realistic setting fairly, we evaluated PocketXMol-tuned using Centre pockets defined around the centroids of candidate blobs predicted by LigandSeek-Find.

Of the 446 test small-molecule instances, Emap2lig-Find returned qualifying blobs with at least 30% bidirectional coverage for 237 instances. Under the same criterion, LigandSeek-Find successfully detected 304 instances with deposited receptors and 293 instances with CryoAtom2-reconstructed receptors. When restricted to instances jointly detected and evaluable by both pipelines, the original small-molecule test set yielded 231 pairs under the deposited-receptor condition and 228 pairs under the CryoAtom2 condition. These subsets served as the benchmarks for directly comparing PocketXMol-tuned against Emap2lig-Build.

{{pptfig:"画图/stage3结果.pptx"|stage3-predicted-region-head-to-head-NO_LEVEL}}

{{figref:stage3-predicted-region-head-to-head-NO_LEVEL}} compares the LigandSeek and Emap2lig docking modules. Our model maintained higher accuracy across all tested conditions. Among the shared GT instances, median top-1 RMSD was 0.85 Å for PocketXMol-tuned and 1.83 Å for Emap2lig-Build. Median best RMSD was 0.63 Å and 1.32 Å, respectively. This advantage was maintained with CryoAtom2-reconstructed receptors ({{figref:stage3-predicted-region-head-to-head-NO_LEVEL}}).

#### Stage 3: Representative cases

We analysed six representative instances to examine how receptor pockets and experimental density provide complementary constraints on pose generation ({{figref:stage3-cases-main-NO_LEVEL}}).

The first group illustrated typical errors in receptor-only docking without experimental density guidance ({{figref:stage3-cases-main-NO_LEVEL|a–c}}). In 9Q16, 9UB7 and 9R3D, PocketXMol-official avoided receptor clashes, with zero clashing atom pairs in each case. However, its poses shifted within the pocket cavity or adopted flipped conformations, with only 46%–77% of heavy atoms reaching the recommended density threshold. Under density guidance, PocketXMol-tuned placed ligand atoms accurately within the experimental density, increasing this fraction to 80%–100% and reducing top-1 RMSD sharply to 0.76–1.05 Å, while all three poses remained free of receptor clashes.

The second group illustrated the shortcomings of density-only fitting that ignores receptor steric constraints ({{figref:stage3-cases-main-NO_LEVEL|d–f}}). In 9U7J, 9WUP and 9WQ3, Emap2lig-Build's top-1 poses produced 10, 15 and 11 clashing pairs with surrounding receptor atoms, respectively. Its pose in 9WQ3 also deviated markedly from the deposited position, with an RMSD of 9.30 Å. By combining receptor geometry with density information, PocketXMol-tuned eliminated all receptor clashes and consistently achieved RMSD values of 0.52–1.41 Å.

These cases showed that the receptor structure imposes steric constraints, whereas cryo-EM density constrains ligand position and conformation. PocketXMol-tuned combines these complementary sources of information to reconstruct ligand poses with high accuracy.

{{pptfig:"画图/stage3可视化.pptx"|stage3-cases-main-NO_LEVEL}}






#### Fair comparison with Emap2lig

{{pptfig:"画图/E2E结果.pptx"|e2e-find-build-direct-comparison-NO_LEVEL}}

Emap2lig can localise and build ligands, but it cannot match chemical identities to detected blobs. Consequently, it cannot be compared directly with our full end-to-end pipeline. To compare their combined detection and modelling capabilities directly, we supplied both LigandSeek and Emap2lig with the ground-truth ligand SMILES ({{figref:e2e-find-build-direct-comparison-NO_LEVEL}}), assuming an ideal, always-successful Match stage for both methods. We then evaluated both pipelines on the same 77 PDBs containing 446 eligible small-molecule instances. LigandSeek used PocketXMol-tuned centre docking guided by predicted blob centroids, whereas Emap2lig used its native blob-guided Build model. Background candidates consumed one attempt, and out-of-scope foreground candidates were skipped without consuming an attempt. Undetected instances remained in the full denominator throughout the completion analysis.

For top-1 poses with RMSD <3 Å, mean completion at a 100% budget was 63.2% for GT, 49.6% for CA2 and 38.2% for Emap2lig. Increasing the budget to 300% raised these values to 64.2%, 55.0% and 43.3%, respectively. Using best-of-50 poses at the same threshold, completion at a 100% budget reached 70.5%, 58.0% and 42.5%, respectively. At a 300% budget, the corresponding completion values were 71.5%, 66.3% and 50.0%, respectively. With correct identities supplied to both pipelines, LigandSeek completed more instances, demonstrating its combined advantage in localisation and pose reconstruction.

Emap2lig is not a fully automated end-to-end modelling tool, but an interactive, semi-automated tool that relies on users to assign the correct SMILES to each detected blob. Even under the favourable assumption of perfect identity matching for Emap2lig, comparison of {{figref:e2e-find-build-direct-comparison-NO_LEVEL}} and the full LigandSeek results in the main text shows that the full LigandSeek pipeline still outperforms it.

Full completion curves and per-PDB distributions are shown in {{figref:supp-find-correct-match-build-NO_LEVEL}}.



### Stage 3: End-to-end top-k success

#### Evaluation protocol (top-k success)

Top-k success measures whether an end-to-end pipeline successfully processes at least one ligand instance in a complex within a specified attempt budget.

Find ranks candidate ligand regions by descending mean probability, yielding Rank 1, Rank 2 and subsequent candidates. For each PDB entry, the pipeline examines these candidates in order for up to $K$ attempts. A PDB entry is classified as successful if any attempt within this budget succeeds.

Top-k success evaluates two basic end-to-end capabilities of our pipeline. These comprise detection and identity matching across all ligand categories, and detection, identity matching and modelling of eligible small molecules. These are single-residue organic small molecules with no atoms missing relative to their templates. Attempt-accounting rules are the same as those in the main text. The all-ligand test set contains 179 PDBs and 2,502 ligand instances; the small-molecule subset contains 77 PDBs and 446 instances. Each task was also evaluated with deposited receptors (GT) and CryoAtom2-reconstructed receptors (CA2).

#### End-to-end region detection and identity matching across ligand categories

{{pptfig:"画图/E2E结果.pptx"|e2e-all-find-match-NO_LEVEL}}

We first evaluated end-to-end ligand-region detection and identity matching in 179 independent test PDB entries ({{figref:e2e-all-find-match-NO_LEVEL}}). These entries contained coexisting ligand categories, including small molecules, ions and sugars. Under the strictest single-attempt condition ($K=1$), end-to-end region detection and identity matching succeeded in 120 entries (67.0%) with CryoAtom2-reconstructed receptors (CA2), while region detection alone succeeded in 134 entries (74.9%). With deposited receptors (GT), the corresponding counts were 142 (79.3%) for joint success and 148 (82.7%) for region detection alone. As the attempt budget increased to 10, end-to-end success rates rapidly plateaued at 87.7% with CA2 receptors and 92.2% with GT receptors. By comparison, Emap2lig-Find detected ligand regions but could not identify their chemical identities. It detected regions in only 71 entries (39.7%) at $K=1$ and 93 entries (52.0%) within $K \le 10$.

#### End-to-end reconstruction of all-atom small-molecule poses

{{pptfig:"画图/E2E结果.pptx"|e2e-small-pipeline-NO_LEVEL}}

We evaluated the full end-to-end reconstruction pipeline (detection, matching, and pose reconstruction) for eligible small molecules across 77 PDB entries which contain at least one of them ({{figref:e2e-small-pipeline-NO_LEVEL|b,c}}). In all evaluations, PocketXMol-tuned used the centroid of the ligand region predicted by Find to define the binding site and pocket, without relying on ground-truth ligand coordinates. We tested the pipeline using both deposited receptors ({{figref:e2e-small-pipeline-NO_LEVEL|b}}) and CryoAtom2-reconstructed receptors ({{figref:e2e-small-pipeline-NO_LEVEL|c}}), where in the latter, no deposited structural information was used at any stage of the pipeline.

The strictest evaluation allowed one attempt ($K=1$), selected only the top-1 pose and required RMSD < 2 Å. Under this criterion, 34/77 entries (44.2%) succeeded with CryoAtom2-reconstructed receptors, compared with 44/77 (57.1%) with deposited receptors. At RMSD < 3 Å, the corresponding counts were 41/77 (53.2%) and 50/77 (64.9%). Allowing up to 10 charged attempts ($K \le 10$) increased top-1 success with CryoAtom2-reconstructed receptors to 46/77 entries (59.7%) at RMSD < 2 Å and 52/77 (67.5%) at RMSD < 3 Å. With deposited receptors, 51/77 entries (66.2%) and 55/77 (71.4%) achieved success at RMSD < 2 Å and < 3 Å, respectively.

For best-of-50 poses within $K \le 10$, success at RMSD < 2 Å reached 67.5% and 75.3% with CryoAtom2-reconstructed and deposited receptors, respectively. At RMSD < 3 Å, the corresponding success rates were 75.3% and 76.6%.

{{figref:e2e-small-pipeline-NO_LEVEL|a}} further separates the success rates of individual pipeline stages. Within the first 10 charged attempts ($K \le 10$), Find alone succeeded in 88.3% and 89.6% of entries with CryoAtom2-reconstructed and deposited receptors, respectively. Both exceeded Emap2lig-Find's success rate of 70.1% in this subset. Requiring both Find and Match to succeed yielded rates of 81.8% and 83.1%, respectively.

### Find–Build comparison with correct ligand identities

Full completion curves and per-PDB distributions for the Find–Build comparison with correct ligand identities are shown in {{figref:supp-find-correct-match-build-NO_LEVEL}}.

{{pptfig:"画图/E2E结果.pptx"|supp-find-correct-match-build-NO_LEVEL|width=5.5in}}
