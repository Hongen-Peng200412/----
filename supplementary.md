# Supplementary Information

## Stage 1: Comparison of LigandSeek2-Find with LigandSeek

Our first-generation model, LigandSeek, localised ligands in cryo-electron microscopy (cryo-EM) density maps without the Match and Build stages for identity matching and pose reconstruction. We compared its strongest version (LigandSeek-PV) with LigandSeek2-Find on the same full test set and small-molecule test subset. The evaluation definitions and presentation followed those used for the comparison with Emap2lig-Find.

On the full test set, LigandSeek2-Find outperformed LigandSeek across all three detection metrics ({{figref:ligandseek2-vs-ligandseek1|a}}). These comprised semantic Dice and one-to-one PRAUC at coverage thresholds of 0.3 and 0.5. When using the deposited receptors, one-to-one $\mathrm{PRAUC}_{0.3}$ was 0.517 for LigandSeek and 0.663 for LigandSeek2-Find. When using CryoAtom2-reconstructed (CA2) receptors, it increased from 0.440 to 0.541. Paired comparisons using CA2 receptors showed higher values for LigandSeek2-Find in 79 PDBs, equal values in 69, and higher values for LigandSeek in 31 ({{figref:ligandseek2-vs-ligandseek1|c}}).

LigandSeek2-Find also showed an overall advantage in the small-molecule test subset. For deposited receptors, one-to-one $\mathrm{PRAUC}_{0.3}$ increased from 0.621 to 0.701. For CA2 receptors, one-to-one $\mathrm{PRAUC}_{0.3}$ increased from 0.568 to 0.573 ({{figref:ligandseek2-vs-ligandseek1|b}}). In paired CA2 comparisons, LigandSeek2-Find performed better than, as well as, or worse than LigandSeek in 27, 46 and 21 PDBs, respectively ({{figref:ligandseek2-vs-ligandseek1|d}}). Per-PDB precision and recall distributions are shown in {{figref:ligandseek2-vs-ligandseek1|e,f}}.

LigandSeek2-Find showed a much larger average advantage over LigandSeek across all ligands than within the small-molecule category alone. We attribute this difference mainly to the change in foreground block sampling during training. LigandSeek sampled ligands in a way resembling weighting by heavy-atom count. LigandSeek2-Find sampled all ligand instances within each PDB equally, regardless of heavy-atom count. Across all preprocessed data, small molecules contained 38.49 heavy atoms on average, compared with 17.02 across all ligand instances. The first-generation model therefore placed greater emphasis on small molecules during training.

{{pptfig:"画图/LigandSeek2_vs_LigandSeek1.pptx"|ligandseek2-vs-ligandseek1|width=5.6in}}

<table data-layout="booktabs" data-pagination="rows">
<caption>Table 3 | Stage 1 detection performance of two LigandSeek generations on the full test set and small-molecule test subset.</caption>
<colgroup><col style="width: 28%"/><col style="width: 12%"/><col style="width: 12%"/><col style="width: 12%"/><col style="width: 12%"/><col style="width: 12%"/><col style="width: 12%"/></colgroup>
<thead>
<tr><th rowspan="2">Model</th><th colspan="3">CA2 receptors</th><th colspan="3">Deposited receptors</th></tr>
<tr><th>Dice</th><th>$\mathrm{PRAUC}_{0.3}$</th><th>$\mathrm{PRAUC}_{0.5}$</th><th>Dice</th><th>$\mathrm{PRAUC}_{0.3}$</th><th>$\mathrm{PRAUC}_{0.5}$</th></tr>
</thead>
<tbody>
<tr class="table-group"><td colspan="7"><em>All ligands</em></td></tr>
<tr><td>LigandSeek</td><td>0.355</td><td>0.440</td><td>0.261</td><td>0.419</td><td>0.517</td><td>0.315</td></tr>
<tr><td>LigandSeek2-Find</td><td><strong>0.477</strong></td><td><strong>0.541</strong></td><td><strong>0.447</strong></td><td><strong>0.584</strong></td><td><strong>0.663</strong></td><td><strong>0.558</strong></td></tr>
<tr class="table-group"><td colspan="7"><em>Small molecules</em></td></tr>
<tr><td>LigandSeek</td><td>0.460</td><td>0.568</td><td>0.483</td><td>0.511</td><td>0.621</td><td>0.539</td></tr>
<tr><td>LigandSeek2-Find</td><td><strong>0.482</strong></td><td><strong>0.573</strong></td><td><strong>0.499</strong></td><td><strong>0.576</strong></td><td><strong>0.701</strong></td><td><strong>0.605</strong></td></tr>
</tbody>
</table>
<p class="table-note">Dice denotes semantic Dice; PRAUC denotes one-to-one PRAUC, with subscripts indicating bidirectional coverage thresholds between predicted and ground-truth regions. CA2 denotes CryoAtom2-reconstructed receptors; deposited receptors correspond to GT. Bold values indicate the higher score in each column within each ligand group.</p>

## Stage 1: Ablation of LigandSeek2-Find

As shown in Table 4, we compared six model variants on the same full test set to assess the contributions of individual designs to ligand detection. Starting with a 3D U-Net receiving experimental density alone(Density only), we added difference density(+ Difference density), a multi-view density bank(+ Density bank) and receptor-atom features(+ Receptor features). We then introduced centroid-aware positional encoding in the receptor embedding head(+ Centroid encoding), followed by the final LigandSeek2-Find model. The final model used receptor-atom binding probabilities predicted by the point-cloud branch for Gaussian candidate scoring, while other models used conventional inference without Gaussian candidate scoring.

According to Table 4, adding difference density improved all metrics under both GT and CA2 conditions. Moreover, the multi-view density bank further improved overall detection ability. It is noteworthy that when constructing multi-view density bank, the deterministic transformations of the same experimental and simulated receptor density do not add any additional information, but highlight ligand signals across contrasts and spatial scales while suppressing dominant receptor density.


Futhermore, we can observe that injecting the receptor information explicitly, adding centroid-aware positional encoding in the receptor embedding head, and introducing Gaussian scoring during inference also generally raise model performance to varying degrees. We refer to the model with all components as LigandSeek2-Find, which has the best overall performance.

<table data-layout="booktabs" data-pagination="rows">
<caption>Table 4 | Internal ablation of LigandSeek2-Find on the full test set.</caption>
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
<tr><td>LigandSeek2-Find</td><td><u>0.477</u></td><td><strong>0.541</strong></td><td><strong>0.447</strong></td><td><u>0.584</u></td><td><strong>0.663</strong></td><td><u>0.558</u></td></tr>
</tbody>
</table>
<p class="table-note">Dice denotes semantic Dice; PRAUC denotes one-to-one PRAUC, with subscripts indicating bidirectional coverage thresholds between predicted and ground-truth regions. CA2 denotes CryoAtom2-reconstructed receptors; deposited receptors correspond to GT. Bold and underlined values indicate the highest and second-highest scores in each column, respectively.</p>

## Stage 3: End-to-end top-k success

### Evaluation protocol (top-k success)

Top-k success measures whether an end-to-end pipeline successfully processes at least one ligand instance in a complex within a specified attempt budget.

Find ranks candidate ligand regions by descending mean probability, yielding Rank 1, Rank 2 and subsequent candidates. For each PDB entry, the pipeline examines these candidates in order for up to $K$ attempts. A PDB entry is classified as successful if any attempt within this budget succeeds.

Top-k success evaluates two basic end-to-end capabilities of our pipeline. These comprise detection and identity matching across all ligand categories, and detection, identity matching and modelling of single-residue organic small molecules with no missing atoms. Attempt-accounting rules are the same as those in the main text. The all-ligand test set contains 179 PDBs and 2,502 ligand instances; the small-molecule subset contains 77 PDBs and 446 instances. Each task was also evaluated with deposited receptors (GT) and CryoAtom2-reconstructed receptors (CA2).

### End-to-end region detection and identity matching across ligand categories

{{pptfig:"画图/E2E结果.pptx"|e2e-all-find-match}}

We first evaluated end-to-end ligand-region detection and identity matching in 179 independent test PDB entries ({{figref:e2e-all-find-match}}). These entries contained coexisting ligand categories, including small molecules, ions and sugars. Under the strictest single-attempt condition ($K=1$), end-to-end region detection and identity matching succeeded in 120 entries (67.0%) with CryoAtom2-reconstructed receptors (CA2), while region detection alone succeeded in 134 entries (74.9%). With deposited receptors (GT), the corresponding counts were 142 (79.3%) for joint success and 148 (82.7%) for region detection alone. As the attempt budget increased to 10, end-to-end success rates rapidly plateaued at 87.7% with CA2 receptors and 92.2% with GT receptors. By comparison, Emap2lig-Find detected ligand regions but could not identify their chemical identities. It detected regions in only 71 entries (39.7%) at $K=1$ and 93 entries (52.0%) within $K \le 10$.

### End-to-end reconstruction of all-atom small-molecule poses

{{pptfig:"画图/E2E结果.pptx"|e2e-small-pipeline}}

We evaluated the full end-to-end reconstruction pipeline (detection, matching, and pose reconstruction) for single-residue organic small molecules with no missing atoms across 77 PDB entries which contain at least one of them ({{figref:e2e-small-pipeline|b,c}}). In all evaluations, PocketXMol-tuned used the centroid of the ligand region predicted by Find to define the binding site and pocket, without relying on ground-truth ligand coordinates. We tested the pipeline using both deposited receptors ({{figref:e2e-small-pipeline|b}}) and CryoAtom2-reconstructed receptors ({{figref:e2e-small-pipeline|c}}), where in the latter, no deposited structural information was used at any stage of the pipeline.

The strictest evaluation allowed one attempt ($K=1$), selected only the top-1 pose and required RMSD < 2 Å. Under this criterion, 34/77 entries (44.2%) succeeded with CryoAtom2-reconstructed receptors, compared with 44/77 (57.1%) with deposited receptors. At RMSD < 3 Å, the corresponding counts were 41/77 (53.2%) and 50/77 (64.9%). Allowing up to 10 charged attempts ($K \le 10$) increased top-1 success with CryoAtom2-reconstructed receptors to 46/77 entries (59.7%) at RMSD < 2 Å and 52/77 (67.5%) at RMSD < 3 Å. With deposited receptors, 51/77 entries (66.2%) and 55/77 (71.4%) achieved success at RMSD < 2 Å and < 3 Å, respectively.

For best-of-50 poses within $K \le 10$, success at RMSD < 2 Å reached 67.5% and 75.3% with CryoAtom2-reconstructed and deposited receptors, respectively. At RMSD < 3 Å, the corresponding success rates were 75.3% and 76.6%.

{{figref:e2e-small-pipeline|a}} further separates the success rates of individual pipeline stages. Within the first 10 charged attempts ($K \le 10$), Find alone succeeded in 88.3% and 89.6% of entries with CryoAtom2-reconstructed and deposited receptors, respectively. Both exceeded Emap2lig-Find's success rate of 70.1% in this subset. Requiring both Find and Match to succeed yielded rates of 81.8% and 83.1%, respectively.
