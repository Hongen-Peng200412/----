# Supplementary Information


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
<p class="table-note">Dice denotes semantic Dice; PRAUC denotes one-to-one PRAUC, with subscripts indicating bidirectional coverage thresholds between predicted and ground-truth regions. CA2 denotes CryoAtom2-reconstructed receptors; deposited receptors correspond to GT. Bold and underlined values indicate the highest and second-highest scores in each column, respectively.</p>

## Stage 3: End-to-end top-k success

### Evaluation protocol (top-k success)

Top-k success measures whether an end-to-end pipeline successfully processes at least one ligand instance in a complex within a specified attempt budget.

Find ranks candidate ligand regions by descending mean probability, yielding Rank 1, Rank 2 and subsequent candidates. For each PDB entry, the pipeline examines these candidates in order for up to $K$ attempts. A PDB entry is classified as successful if any attempt within this budget succeeds.

Top-k success evaluates two basic end-to-end capabilities of our pipeline. These comprise detection and identity matching across all ligand categories, and detection, identity matching and modelling of eligible small molecules. These are single-residue organic small molecules with no atoms missing relative to their templates. Attempt-accounting rules are the same as those in the main text. The all-ligand test set contains 179 PDBs and 2,502 ligand instances; the small-molecule subset contains 77 PDBs and 446 instances. Each task was also evaluated with deposited receptors (GT) and CryoAtom2-reconstructed receptors (CA2).

### End-to-end region detection and identity matching across ligand categories

{{pptfig:"画图/E2E结果.pptx"|e2e-all-find-match}}

We first evaluated end-to-end ligand-region detection and identity matching in 179 independent test PDB entries ({{figref:e2e-all-find-match}}). These entries contained coexisting ligand categories, including small molecules, ions and sugars. Under the strictest single-attempt condition ($K=1$), end-to-end region detection and identity matching succeeded in 120 entries (67.0%) with CryoAtom2-reconstructed receptors (CA2), while region detection alone succeeded in 134 entries (74.9%). With deposited receptors (GT), the corresponding counts were 142 (79.3%) for joint success and 148 (82.7%) for region detection alone. As the attempt budget increased to 10, end-to-end success rates rapidly plateaued at 87.7% with CA2 receptors and 92.2% with GT receptors. By comparison, Emap2lig-Find detected ligand regions but could not identify their chemical identities. It detected regions in only 71 entries (39.7%) at $K=1$ and 93 entries (52.0%) within $K \le 10$.

### End-to-end reconstruction of all-atom small-molecule poses

{{pptfig:"画图/E2E结果.pptx"|e2e-small-pipeline}}

We evaluated the full end-to-end reconstruction pipeline (detection, matching, and pose reconstruction) for eligible small molecules across 77 PDB entries which contain at least one of them ({{figref:e2e-small-pipeline|b,c}}). In all evaluations, PocketXMol-tuned used the centroid of the ligand region predicted by Find to define the binding site and pocket, without relying on ground-truth ligand coordinates. We tested the pipeline using both deposited receptors ({{figref:e2e-small-pipeline|b}}) and CryoAtom2-reconstructed receptors ({{figref:e2e-small-pipeline|c}}), where in the latter, no deposited structural information was used at any stage of the pipeline.

The strictest evaluation allowed one attempt ($K=1$), selected only the top-1 pose and required RMSD < 2 Å. Under this criterion, 34/77 entries (44.2%) succeeded with CryoAtom2-reconstructed receptors, compared with 44/77 (57.1%) with deposited receptors. At RMSD < 3 Å, the corresponding counts were 41/77 (53.2%) and 50/77 (64.9%). Allowing up to 10 charged attempts ($K \le 10$) increased top-1 success with CryoAtom2-reconstructed receptors to 46/77 entries (59.7%) at RMSD < 2 Å and 52/77 (67.5%) at RMSD < 3 Å. With deposited receptors, 51/77 entries (66.2%) and 55/77 (71.4%) achieved success at RMSD < 2 Å and < 3 Å, respectively.

For best-of-50 poses within $K \le 10$, success at RMSD < 2 Å reached 67.5% and 75.3% with CryoAtom2-reconstructed and deposited receptors, respectively. At RMSD < 3 Å, the corresponding success rates were 75.3% and 76.6%.

{{figref:e2e-small-pipeline|a}} further separates the success rates of individual pipeline stages. Within the first 10 charged attempts ($K \le 10$), Find alone succeeded in 88.3% and 89.6% of entries with CryoAtom2-reconstructed and deposited receptors, respectively. Both exceeded Emap2lig-Find's success rate of 70.1% in this subset. Requiring both Find and Match to succeed yielded rates of 81.8% and 83.1%, respectively.

## Find–Build comparison with correct ligand identities

Full completion curves and per-PDB distributions for the Find–Build comparison with correct ligand identities are shown in {{figref:supp-find-correct-match-build}}.

{{pptfig:"画图/E2E结果.pptx"|supp-find-correct-match-build|width=5.5in}}
