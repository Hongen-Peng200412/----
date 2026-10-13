# Supplementary Information



## Stage 1 Ligand region detection by LigandSeek2 and LigandSeek1

### Comparison protocol

We refer to the Find model presented here and its frozen F2–F1 Gaussian workflow as LigandSeek2. LigandSeek1 denotes the official v1.0.0 release with the complete PV model. Its default probability thresholds are 0.79 for deposited receptors (GT) and 0.88 for CryoAtom2-reconstructed receptors (CA2). Native mean ligand probabilities rank its predicted instances. We evaluated both generations on the same test_0 set of 179 PDB entries and 2,502 ligand instances without retuning on test data. Semantic Dice uses the voxel union of retained instances, whereas one-to-one PRAUC applies bidirectional coverage thresholds between predicted and ground-truth instances.

The small-molecule view contains 94 PDB entries and 821 labelled small-molecule instances. A frozen bidirectional coverage threshold of 0.3 assigns predicted candidates to ground-truth instances. Candidates assigned to other ligand classes are ignored, whereas unassigned candidates remain as false positives. Values below are PDB-equal macro means. Figure error bars show 95% mean confidence intervals from 10,000 PDB bootstrap resamples.

### Complete test set and small-molecule view

On the complete test set, LigandSeek2 had higher semantic Dice and one-to-one PRAUC at both coverage thresholds than LigandSeek1 ({{figref:ligandseek2-vs-ligandseek1|a}}). One-to-one PRAUC₀.₃ increased from 0.517197 to 0.663163 for GT and from 0.439913 to 0.540883 for CA2. In paired CA2 comparisons, LigandSeek2 was higher for 79 PDB entries, values were equal for 69, and LigandSeek1 was higher for 31 ({{figref:ligandseek2-vs-ligandseek1|c}}).

For small molecules, GT one-to-one PRAUC₀.₃ was 0.620856 for LigandSeek1 and 0.701144 for LigandSeek2 ({{figref:ligandseek2-vs-ligandseek1|b}}). The corresponding CA2 values were similar, at 0.567725 and 0.572615. Paired CA2 comparisons gave direction counts of 27, 46 and 21, respectively ({{figref:ligandseek2-vs-ligandseek1|d}}). Per-PDB precision and recall distributions appear in {{figref:ligandseek2-vs-ligandseek1|e,f}}.

{{pptfig:"画图/LigandSeek2_vs_LigandSeek1.pptx"|ligandseek2-vs-ligandseek1}}

<table>
<caption>Table 3 | Stage 1 detection performance of two LigandSeek generations. All values are PDB-equal macro means; PRAUC subscripts indicate bidirectional coverage thresholds between predicted and ground-truth regions.</caption>
<tr><th>Evaluation scope</th><th>Model</th><th>Input</th><th>Semantic Dice</th><th>One-to-one PRAUC₀.₃</th><th>One-to-one PRAUC₀.₅</th></tr>
<tr><td>Complete test_0</td><td>LigandSeek1</td><td>GT</td><td>0.419166</td><td>0.517197</td><td>0.315426</td></tr>
<tr><td>Complete test_0</td><td>LigandSeek2</td><td>GT</td><td>0.584498</td><td>0.663163</td><td>0.557571</td></tr>
<tr><td>Complete test_0</td><td>LigandSeek1</td><td>CA2</td><td>0.354548</td><td>0.439913</td><td>0.260535</td></tr>
<tr><td>Complete test_0</td><td>LigandSeek2</td><td>CA2</td><td>0.476877</td><td>0.540883</td><td>0.447013</td></tr>
<tr><td>Small molecules</td><td>LigandSeek1</td><td>GT</td><td>0.511079</td><td>0.620856</td><td>0.539118</td></tr>
<tr><td>Small molecules</td><td>LigandSeek2</td><td>GT</td><td>0.576214</td><td>0.701144</td><td>0.604858</td></tr>
<tr><td>Small molecules</td><td>LigandSeek1</td><td>CA2</td><td>0.460169</td><td>0.567725</td><td>0.483082</td></tr>
<tr><td>Small molecules</td><td>LigandSeek2</td><td>CA2</td><td>0.481504</td><td>0.572615</td><td>0.499294</td></tr>
</table>




## Stage 3: End-to-end ligand instance completion

### Evaluation protocol (completion)

Top-k success measures whether an end-to-end pipeline successfully processes at least one ligand instance in a complex within a specified attempt budget. We extended this assessment with the ligand completion ratio, which measures the **proportion** of ligand instances processed successfully at a specified **relative** attempt budget.

For a PDB entry containing $N$ ground-truth ligands, let $f(t)$ denote the number of ligand instances successfully processed within $t$ charged attempts. Whereas top-k success uses the absolute number of charged attempts $t$, ligand completion ratio uses the relative attempt budget $\rho=\frac{t}{N}$. Correspondingly, the binary outcome indicating **whether any ligand instance was successfully processed** becomes the fraction of successfully processed ligands, $\frac{f(t)}{N}$, at relative budget $\rho$.

Like top-k success, ligand completion ratio evaluates two basic end-to-end capabilities of our pipeline. These comprise detection and identity matching across all ligand categories, and detection, identity matching and modelling of single-residue organic small molecules with no missing atoms. Both metrics use the same accounting rules and test sets for each task. The all-ligand test set contains 179 PDBs and 2,502 ligand instances; the small-molecule subset contains 77 PDBs and 446 instances. Each task was evaluated with deposited receptors (GT) and CryoAtom2-reconstructed receptors (CA2).

### Detection and identity matching across all ligand classes

For detection and identity matching across all ligand classes, increasing the relative attempt budget from 100% to 300% raised mean instance completion. Completion increased from 62.1% to 67.5% for GT and from 51.1% to 58.8% for CA2 ({{figref:supp-e2e-completion-all}}). The corresponding medians increased from 66.7% and 50.0% to 71.4% and 60.2%, respectively. A relative attempt budget of 100% has particular practical significance. This corresponds to a setting in which users already know the ligand identities and relative molecular masses of the complex. Under these conditions, our pipeline recovered most of the ligand instances.

{{pptfig:"画图/E2E实例完成度.pptx"|supp-e2e-completion-all}}

<table>
<caption>Table 1 | All-ligand instance completion (%). Means are PDB-equal macro means; medians were calculated across the same 179 PDBs.</caption>
<tr><th>Input</th><th>100% mean</th><th>100% median</th><th>300% mean</th><th>300% median</th></tr>
<tr><td>GT</td><td>62.1</td><td>66.7</td><td>67.5</td><td>71.4</td></tr>
<tr><td>CA2</td><td>51.1</td><td>50.0</td><td>58.8</td><td>60.2</td></tr>
</table>

### Modelling organic small molecules with one residue and no missing atoms

Small-molecule instance completion requires detection by Find, correct identity assignment by Match, and a PocketXMol-tuned pose with an RMSD below the specified threshold. We report results under eight combinations of the following test conditions. These combine GT or CA2 receptors, top-1 or best poses, and heavy-atom RMSD thresholds of <2 Å or <3 Å.

For top-1 poses with RMSD <3 Å, mean completion for GT was 60.1% and 61.1% at 100% and 300% budgets, respectively. The corresponding CA2 values were 47.7% and 53.0% ({{figref:supp-e2e-completion-small}}). For best poses, mean completion was 66.0% and 66.9% for GT, and 54.7% and 62.8% for CA2, respectively. The gap between best and top-1 poses shows that many correct poses had already been generated but were not ranked first.

{{pptfig:"画图/E2E实例完成度.pptx"|supp-e2e-completion-small}}

<table>
<caption>Table 2 | Small-molecule instance completion (%). Means and medians were calculated across the same 77 PDBs.</caption>
<tr><th>Input</th><th>Pose</th><th>RMSD</th><th>100% mean</th><th>100% median</th><th>300% mean</th><th>300% median</th></tr>
<tr><td>GT</td><td>Top‑1</td><td>&lt;2 Å</td><td>55.1</td><td>75.0</td><td>55.1</td><td>75.0</td></tr>
<tr><td>CA2</td><td>Top‑1</td><td>&lt;2 Å</td><td>41.1</td><td>16.7</td><td>44.9</td><td>25.0</td></tr>
<tr><td>GT</td><td>Top‑1</td><td>&lt;3 Å</td><td>60.1</td><td>100.0</td><td>61.1</td><td>100.0</td></tr>
<tr><td>CA2</td><td>Top‑1</td><td>&lt;3 Å</td><td>47.7</td><td>33.3</td><td>53.0</td><td>50.0</td></tr>
<tr><td>GT</td><td>Best</td><td>&lt;2 Å</td><td>63.5</td><td>100.0</td><td>64.4</td><td>100.0</td></tr>
<tr><td>CA2</td><td>Best</td><td>&lt;2 Å</td><td>49.1</td><td>50.0</td><td>55.9</td><td>83.3</td></tr>
<tr><td>GT</td><td>Best</td><td>&lt;3 Å</td><td>66.0</td><td>100.0</td><td>66.9</td><td>100.0</td></tr>
<tr><td>CA2</td><td>Best</td><td>&lt;3 Å</td><td>54.7</td><td>66.7</td><td>62.8</td><td>100.0</td></tr>
</table>

