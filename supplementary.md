# Supplementary Information

## Stage 1: Comparison of LigandSeek2-Find with LigandSeek

Our first-generation model, LigandSeek, localised ligands in cryo-electron microscopy (cryo-EM) density maps without the Match and Build stages for identity matching and pose reconstruction. We compared its strongest version, LigandSeek-PV, with LigandSeek2-Find on the same all-ligand and small-molecule test sets. The evaluation definitions and presentation followed those used for the comparison with Emap2lig-Find.

On the all-ligand test set, LigandSeek2-Find outperformed LigandSeek across all three detection metrics ({{figref:ligandseek2-vs-ligandseek1|a}}). These comprised semantic Dice and one-to-one PRAUC at coverage thresholds of 0.3 and 0.5. For deposited receptors (GT), one-to-one PRAUC₀.₃ increased from 0.517197 to 0.663163. For CryoAtom2-reconstructed receptors (CA2), it increased from 0.439913 to 0.540883. Paired CA2 comparisons showed higher values for LigandSeek2 in 79 PDBs, equal values in 69, and higher values for LigandSeek in 31 ({{figref:ligandseek2-vs-ligandseek1|c}}).

LigandSeek2-Find also showed an overall advantage in the small-molecule view. For GT, one-to-one PRAUC₀.₃ was 0.620856 for LigandSeek and 0.701144 for LigandSeek2. The corresponding CA2 values were 0.567725 and 0.572615 ({{figref:ligandseek2-vs-ligandseek1|b}}). Under CA2 conditions, semantic Dice was 0.460169 and 0.481504, respectively. One-to-one PRAUC₀.₅ was 0.483082 for LigandSeek and 0.499294 for LigandSeek2. In paired CA2 comparisons, LigandSeek2-Find performed better, equally or worse than LigandSeek in 27, 46 and 21 PDBs, respectively ({{figref:ligandseek2-vs-ligandseek1|d}}). Per-PDB precision and recall distributions are shown in {{figref:ligandseek2-vs-ligandseek1|e,f}}.

LigandSeek2-Find showed a much larger average advantage over LigandSeek across all ligands than within the small-molecule category alone. We attribute this difference mainly to the change in foreground sampling during training. LigandSeek sampled ligands in a way resembling weighting by heavy-atom count. LigandSeek2-Find sampled all ligand instances within each PDB equally, regardless of heavy-atom count. Across all preprocessed data, small molecules contained 38.49 heavy atoms on average, compared with 17.02 across all ligand instances. The first-generation model therefore placed greater emphasis on small molecules during training.

{{pptfig:"画图/LigandSeek2_vs_LigandSeek1.pptx"|ligandseek2-vs-ligandseek1}}

<table>
<caption>Table 3 | Stage 1 detection performance of two LigandSeek generations. All values are PDB-equal macro means; PRAUC subscripts indicate bidirectional coverage thresholds between predicted and ground-truth regions.</caption>
<thead>
<tr><th colspan="3">CA2</th><th rowspan="2">Scope</th><th rowspan="2">Model</th><th colspan="3">GT</th></tr>
<tr><th>Semantic Dice</th><th>One-to-one PRAUC₀.₃</th><th>One-to-one PRAUC₀.₅</th><th>Semantic Dice</th><th>One-to-one PRAUC₀.₃</th><th>One-to-one PRAUC₀.₅</th></tr>
</thead>
<tbody>
<tr><td>0.354548</td><td>0.439913</td><td>0.260535</td><td>All ligands</td><td>LigandSeek</td><td>0.419166</td><td>0.517197</td><td>0.315426</td></tr>
<tr><td>0.476877</td><td>0.540883</td><td>0.447013</td><td>All ligands</td><td>LigandSeek2</td><td>0.584498</td><td>0.663163</td><td>0.557571</td></tr>
<tr><td>0.460169</td><td>0.567725</td><td>0.483082</td><td>Small molecules</td><td>LigandSeek</td><td>0.511079</td><td>0.620856</td><td>0.539118</td></tr>
<tr><td>0.481504</td><td>0.572615</td><td>0.499294</td><td>Small molecules</td><td>LigandSeek2</td><td>0.576214</td><td>0.701144</td><td>0.604858</td></tr>
</tbody>
</table>

## Stage 1: Internal ablation of LigandSeek2-Find

We compared six model variants on the same all-ligand test set to assess the contributions of individual designs to ligand detection. Starting with a three-dimensional (3D) U-Net receiving experimental density alone, we added difference density, a multi-view density bank and receptor-atom features. We then introduced centroid-aware positional encoding and joint point–voxel modelling, followed by the final LigandSeek2-Find model. The final model used receptor-atom binding probabilities predicted by the point-cloud branch for Gaussian candidate scoring. The other models used conventional inference without Gaussian candidate scoring.

Adding difference density improved all three metrics under both GT and CA2 conditions. The multi-view density bank further improved detection without introducing additional information sources. Deterministic transformations of the same experimental and simulated receptor density highlighted ligand signals across contrasts and spatial scales while suppressing dominant receptor density. Compared with experimental and difference density alone, the density bank increased GT semantic Dice from 0.482589 to 0.584581. One-to-one PRAUC₀.₃ and PRAUC₀.₅ increased from 0.568837 and 0.452351 to 0.642664 and 0.561188, respectively. All three metrics also improved under CA2 conditions after adding the density bank.

Adding receptor-atom features increased CA2 one-to-one PRAUC₀.₃ from 0.508261 to 0.520122, whereas the GT value decreased from 0.642664 to 0.630947. Introducing centroid-aware positional encoding and joint point–voxel modelling further increased CA2 one-to-one PRAUC₀.₃ to 0.536410. Semantic Dice and one-to-one PRAUC₀.₅ also increased under CA2 conditions with these additions.

Finally, the final inference procedure, which used receptor-atom binding probabilities for candidate scoring, increased one-to-one PRAUC at both thresholds. For GT, one-to-one PRAUC₀.₃ and PRAUC₀.₅ increased from 0.632800 and 0.538543 to 0.663163 and 0.557571, respectively. The corresponding CA2 values increased from 0.536410 and 0.444272 to 0.540883 and 0.447013. Semantic Dice under CA2 conditions decreased from 0.482818 to 0.476877.

<table>
<caption>Table 4 | Internal ablation of LigandSeek2-Find. All values are PDB-equal macro means across the all-ligand test set of 179 PDBs. PRAUC subscripts indicate bidirectional coverage thresholds between predicted and ground-truth regions. The first five rows successively introduce the indicated designs. The last row represents the final inference procedure with Gaussian candidate scoring.</caption>
<colgroup><col style="width: 13%"/><col style="width: 13%"/><col style="width: 13%"/><col style="width: 22%"/><col style="width: 13%"/><col style="width: 13%"/><col style="width: 13%"/></colgroup>
<thead>
<tr><th colspan="3">CA2</th><th rowspan="2">Model variant</th><th colspan="3">GT</th></tr>
<tr><th>Semantic Dice</th><th>One-to-one PRAUC₀.₃</th><th>One-to-one PRAUC₀.₅</th><th>Semantic Dice</th><th>One-to-one PRAUC₀.₃</th><th>One-to-one PRAUC₀.₅</th></tr>
</thead>
<tbody>
<tr><td>0.394437</td><td>0.445977</td><td>0.342370</td><td>3D U-Net: experimental density</td><td>0.394437</td><td>0.445977</td><td>0.342370</td></tr>
<tr><td>0.433585</td><td>0.501017</td><td>0.403186</td><td>+ Difference density</td><td>0.482589</td><td>0.568837</td><td>0.452351</td></tr>
<tr><td>0.452942</td><td>0.508261</td><td>0.427176</td><td>+ Multi-view density bank</td><td>0.584581</td><td>0.642664</td><td>0.561188</td></tr>
<tr><td>0.462745</td><td>0.520122</td><td>0.436629</td><td>+ Receptor-atom features</td><td>0.570334</td><td>0.630947</td><td>0.554198</td></tr>
<tr><td>0.482818</td><td>0.536410</td><td>0.444272</td><td>+ Centroid-aware positional encoding and point–voxel modelling</td><td>0.583242</td><td>0.632800</td><td>0.538543</td></tr>
<tr><td>0.476877</td><td>0.540883</td><td>0.447013</td><td>LigandSeek2-Find: receptor-probability-guided scoring</td><td>0.584498</td><td>0.663163</td><td>0.557571</td></tr>
</tbody>
</table>

## Stage 3: End-to-end ligand instance completion

### Evaluation protocol (completion)

Top-k success measures whether an end-to-end pipeline successfully processes at least one ligand instance in a complex within a specified attempt budget. We extended this assessment with the ligand completion ratio, which measures the **proportion** of ligand instances processed successfully at a specified **relative** attempt budget.

For a PDB entry containing $N$ ground-truth ligands, let $f(t)$ denote the number of ligand instances successfully processed within $t$ charged attempts. Whereas top-k success uses the absolute number of charged attempts $t$, ligand completion ratio uses the relative attempt budget $\rho=\frac{t}{N}$. Correspondingly, the binary outcome indicating **whether any ligand instance was successfully processed** becomes the fraction of successfully processed ligands, $\frac{f(t)}{N}$, at relative budget $\rho$. We report results for $\rho \in [0,300\%]$, rounding the actual attempt budget down to $\lfloor\rho N_p\rfloor$ charged attempts.

Like top-k success, ligand completion ratio evaluates two basic end-to-end capabilities of our pipeline. These comprise detection and identity matching across all ligand categories, and detection, identity matching and modelling of single-residue organic small molecules with no missing atoms. Both metrics use the same accounting rules and test sets for each task. The all-ligand test set contains 179 PDBs and 2,502 ligand instances; the small-molecule subset contains 77 PDBs and 446 instances. Each task was evaluated with deposited receptors (GT) and CryoAtom2-reconstructed receptors (CA2).

### Detection and identity matching across all ligand classes

For detection and identity matching across all ligand classes, increasing the relative attempt budget from 100% to 300% raised mean instance completion. Completion increased from 62.1% to 67.5% for GT and from 51.1% to 58.8% for CA2 ({{figref:supp-e2e-completion-all}}). The corresponding medians increased from 66.7% and 50.0% to 71.4% and 60.2%, respectively. A relative attempt budget of 100% has particular practical significance. This corresponds to a setting in which users already know the ligand identities and relative molecular masses of the complex. This quantitative information then serves as a constraint on the end-to-end pipeline. Under these conditions, our pipeline recovered most of the ligand instances.

{{pptfig:"画图/E2E实例完成度.pptx"|supp-e2e-completion-all}}

<table>
<caption>Table 1 | All-ligand instance completion (%). Means are PDB-equal macro means; medians were calculated across the same 179 PDBs.</caption>
<tr><th>Receptor</th><th>100% mean</th><th>100% median</th><th>300% mean</th><th>300% median</th></tr>
<tr><td>GT</td><td>62.1</td><td>66.7</td><td>67.5</td><td>71.4</td></tr>
<tr><td>CA2</td><td>51.1</td><td>50.0</td><td>58.8</td><td>60.2</td></tr>
</table>

### Modelling organic small molecules with one residue and no missing atoms

Small-molecule instance completion requires detection by Find and correct identity assignment by Match. It also requires a PocketXMol-tuned pose with a heavy-atom root-mean-square deviation (RMSD) below the specified threshold. We report results under eight combinations of the following test conditions. These combine GT or CA2 receptors, top-1 or best-of-50 poses, and heavy-atom RMSD thresholds of <2 Å or <3 Å.

For top-1 poses with RMSD <3 Å, mean completion for GT was 60.1% and 61.1% at 100% and 300% budgets, respectively. The corresponding CA2 values were 47.7% and 53.0% ({{figref:supp-e2e-completion-small}}). For best-of-50 poses, mean completion was 66.0% and 66.9% for GT, and 54.7% and 62.8% for CA2, respectively. The gap between best-of-50 and top-1 poses shows that many correct poses had already been generated but were not ranked first.

{{pptfig:"画图/E2E实例完成度.pptx"|supp-e2e-completion-small}}

<table>
<caption>Table 2 | Small-molecule instance completion (%). Means and medians were calculated across the same 77 PDBs.</caption>
<thead>
<tr><th colspan="4">CA2</th><th rowspan="2">Pose</th><th rowspan="2">RMSD</th><th colspan="4">GT</th></tr>
<tr><th>100% mean</th><th>100% median</th><th>300% mean</th><th>300% median</th><th>100% mean</th><th>100% median</th><th>300% mean</th><th>300% median</th></tr>
</thead>
<tbody>
<tr><td>41.1</td><td>16.7</td><td>44.9</td><td>25.0</td><td>Top-1</td><td>&lt;2 Å</td><td>55.1</td><td>75.0</td><td>55.1</td><td>75.0</td></tr>
<tr><td>47.7</td><td>33.3</td><td>53.0</td><td>50.0</td><td>Top-1</td><td>&lt;3 Å</td><td>60.1</td><td>100.0</td><td>61.1</td><td>100.0</td></tr>
<tr><td>49.1</td><td>50.0</td><td>55.9</td><td>83.3</td><td>Best-of-50</td><td>&lt;2 Å</td><td>63.5</td><td>100.0</td><td>64.4</td><td>100.0</td></tr>
<tr><td>54.7</td><td>66.7</td><td>62.8</td><td>100.0</td><td>Best-of-50</td><td>&lt;3 Å</td><td>66.0</td><td>100.0</td><td>66.9</td><td>100.0</td></tr>
</tbody>
</table>
