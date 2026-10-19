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

## Stage 3: End-to-end ligand instance completion

### Evaluation protocol (completion)

Top-k success measures whether an end-to-end pipeline successfully processes at least one ligand instance in a complex within a specified attempt budget. We extended this assessment with the ligand completion ratio, which measures the **proportion** of ligand instances processed successfully at a specified relative attempt budget.

For a PDB entry containing $N$ ground-truth ligands, let $f(t)$ denote the number of ligand instances successfully processed within $t$ charged attempts. Whereas top-k success uses the absolute number of charged attempts $t$, ligand completion ratio uses the relative attempt budget $\rho=\frac{t}{N}$. Correspondingly, the binary outcome indicating whether any ligand instance was successfully processed becomes the fraction of successfully processed ligands, $\frac{f(t)}{N}$, at relative budget $\rho$. We report results for $\rho \in [0,300\%]$ with rounding the actual attempt budget down to $\lfloor\rho N_p\rfloor$ charged attempts.

Like top-k success, ligand completion ratio evaluates two basic end-to-end capabilities of our pipeline. These comprise detection and identity matching across all ligand categories, and detection, identity matching and modelling of single-residue organic small molecules with no missing atoms. Both metrics use the same accounting rules and test sets for each task. The all-ligand test set contains 179 PDBs and 2,502 ligand instances; the small-molecule subset contains 77 PDBs and 446 instances. Each task was also evaluated with deposited receptors (GT) and CryoAtom2-reconstructed receptors (CA2).

### Fair Find–correct Match–Build comparison with Emap2lig

To compare the combined detection and modelling capabilities directly, we supplied both LigandSeek and Emap2lig with the correct ligand SMILES ({{figref:supp-find-correct-match-build}}). We evaluated Find–correct Match–Build completion on the same 77 PDBs containing 446 single-residue organic small molecules with no missing atoms. LigandSeek used PocketXMol-tuned centre docking guided by predicted blob centroids, whereas Emap2lig used its native blob-guided Build model. Background candidates consumed one attempt, and out-of-scope foreground candidates were skipped without charge. Undetected instances remained in the full denominator throughout the completion analysis.

For top-1 poses with RMSD <3 Å, mean completion at a 100% budget was 63.2% for GT, 49.6% for CA2 and 38.2% for Emap2lig. Increasing the budget to 300% raised these values to 64.2%, 55.0% and 43.3%, respectively. Using best-of-50 poses at the same threshold, completion at a 100% budget reached 70.5%, 58.0% and 42.5%, respectively. At a 300% budget, the corresponding completion values were 71.5%, 66.3% and 50.0%, respectively. With correct identities supplied to both pipelines, LigandSeek completed more instances, demonstrating its combined advantage in localisation and pose reconstruction.

The gap between best-of-50 and top-1 completion showed that some correct poses had been generated but were not ranked first. With either receptor input, the combination of LigandSeek-Find and PocketXMol-tuned recovered more small-molecule instances within the same attempt budget.

{{pptfig:"画图/Find-Match-Build公平对比.pptx"|supp-find-correct-match-build|width=5.5in}}

### Detection and identity matching across all ligand classes

For detection and identity matching across all ligand classes, increasing the relative attempt budget from 100% to 300% raised mean instance completion. Completion increased from 51.1% to 58.8% for CA2 and from 62.1% to 67.5% for GT({{figref:supp-e2e-completion-all}}). The corresponding medians increased from 50.0% and 66.7% to 60.2% and 71.4%, respectively. A relative attempt budget of 100% has particular practical significance. This corresponds to a scenario in which ligand identities and numbers are known to the user and can constrain the end-to-end pipeline. Under these conditions, our pipeline recovered most of the ligand instances({{figref:supp-e2e-completion-all}}).

{{pptfig:"画图/E2E实例完成度.pptx"|supp-e2e-completion-all}}

<table data-layout="booktabs" data-outline="box" data-col-rules="1,3" data-pagination="rows">
<caption>Table 1 | All-ligand instance completion (%).</caption>
<colgroup><col style="width: 16%"/><col style="width: 21%"/><col style="width: 21%"/><col style="width: 21%"/><col style="width: 21%"/></colgroup>
<thead>
<tr><th rowspan="2">Receptor</th><th colspan="2">100%</th><th colspan="2">300%</th></tr>
<tr><th>Mean</th><th>Median</th><th>Mean</th><th>Median</th></tr>
</thead>
<tbody>
<tr><td>GT</td><td>62.1</td><td>66.7</td><td>67.5</td><td>71.4</td></tr>

<tr><td>CA2</td><td>51.1</td><td>50.0</td><td>58.8</td><td>60.2</td></tr>

</tbody>
</table>
<p class="table-note">Means are PDB-equal macro means; medians were calculated across the same 179 PDBs.</p>

### Modelling organic small molecules with one residue and no missing atoms

Successful processing of a small-molecule instance requires successful detection by Find, correct identity assignment by Match and a PocketXMol-tuned pose with a heavy-atom RMSD below the specified threshold. We report results under eight combinations of the following test conditions. These combine GT or CA2 receptors, top-1 or best-of-50 poses, and heavy-atom RMSD thresholds of <2 Å or <3 Å.

For top-1 poses with RMSD <3 Å, mean completion for CA2 was 47.7% and 53.0% at 100% and 300% budgets, respectively. The corresponding GT values were 60.1% and 61.1% ({{figref:supp-e2e-completion-small}}). For best-of-50 poses, mean completion was 54.7% and 62.8% for CA2, and 66.0% and 66.9% for GT, respectively. The gap between best pose and top-1 pose shows that many correct poses had already been generated but were not ranked first.

{{pptfig:"画图/E2E实例完成度.pptx"|supp-e2e-completion-small}}

<table data-layout="booktabs" data-outline="box" data-col-rules="2,6" data-pagination="rows" data-page-break="before">
<caption>Table 2 | Small-molecule instance completion (%).</caption>
<colgroup><col style="width: 14%"/><col style="width: 10%"/><col style="width: 9.5%"/><col style="width: 9.5%"/><col style="width: 9.5%"/><col style="width: 9.5%"/><col style="width: 9.5%"/><col style="width: 9.5%"/><col style="width: 9.5%"/><col style="width: 9.5%"/></colgroup>
<thead>
<tr><th rowspan="3">Pose</th><th rowspan="3">RMSD</th><th colspan="4">CA2</th><th colspan="4">GT</th></tr>
<tr><th colspan="2">100%</th><th colspan="2">300%</th><th colspan="2">100%</th><th colspan="2">300%</th></tr>
<tr><th>Mean</th><th>Median</th><th>Mean</th><th>Median</th><th>Mean</th><th>Median</th><th>Mean</th><th>Median</th></tr>
</thead>
<tbody>
<tr><td rowspan="2">Top-1</td><td>&lt;2 Å</td><td>41.1</td><td>16.7</td><td>44.9</td><td>25.0</td><td>55.1</td><td>75.0</td><td>55.1</td><td>75.0</td></tr>
<tr><td>&lt;3 Å</td><td>47.7</td><td>33.3</td><td>53.0</td><td>50.0</td><td>60.1</td><td>100.0</td><td>61.1</td><td>100.0</td></tr>
<tr class="table-divider"><td rowspan="2">Best</td><td>&lt;2 Å</td><td>49.1</td><td>50.0</td><td>55.9</td><td>83.3</td><td>63.5</td><td>100.0</td><td>64.4</td><td>100.0</td></tr>
<tr><td>&lt;3 Å</td><td>54.7</td><td>66.7</td><td>62.8</td><td>100.0</td><td>66.0</td><td>100.0</td><td>66.9</td><td>100.0</td></tr>
</tbody>
</table>
<p class="table-note">Means and medians were calculated across the same 77 PDBs.</p>
