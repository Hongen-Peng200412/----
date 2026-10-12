# Supplementary Information

## End-to-end ligand instance completion

We measured instance completion at different relative attempt budgets to assess recovery of multiple ligand instances within each PDB. The analysis used frozen results from LigandSeek-Find, LigandSeek-Match and LigandSeek-Build, hereafter Find, Match and Build. Detection and identity matching across all ligand classes included 2,502 ligand instances in 179 PDBs. Small-molecule modelling included 446 organic small-molecule instances, each occupying one residue with no missing atoms, in 77 PDBs. Both analyses compared deposited receptor structures (GT) with CryoAtom2-reconstructed receptor structures (CA2).

### Metric and attempt budget

For PDB $p$, $N_p$ denotes all target ligand instances in the analysis, and $S_p(K)$ counts distinct instances completed within $K$ charged attempts. The integer budget and instance completion at relative attempt budget $\rho$ are

$$
K_p(\rho)=\lfloor\rho N_p\rfloor,\qquad
F_p(\rho)=\frac{S_p(K_p(\rho))}{N_p}.
$$

Here, $\rho=1$ corresponds to a 100% relative attempt budget, allowing as many charged attempts as target instances in that PDB. The floor operator rounds down; a PDB containing one target instance therefore receives zero attempts at a 50% budget. For the all-ligand analysis, $N_p$ includes every ligand instance in the PDB. For small-molecule modelling, it includes only organic small-molecule instances occupying one residue with no missing atoms.

Instances sharing a chemical identity were counted separately, whereas repeated hits to one instance contributed at most one completion. Candidate processing continued after the first success to accumulate completion of other instances. Undetected instances, identity errors, input construction failures and docking failures remained in the denominator. The frozen candidate order placed selected candidates before unselected candidates, with each segment ranked by decreasing Find score. Candidates beyond rank 20 were retained.

For detection and identity matching across all ligand classes, every candidate consumed one attempt. An instance was completed when its region was detected and Match assigned the correct identity. Small-molecule modelling retained the accounting rule based on the Match-predicted class. False-positive candidates consumed one attempt. Candidates corresponding to non-small-molecule ligands were skipped without charge when Match predicted a non-small-molecule identity. Predictions of a small molecule for those candidates consumed one attempt and failed. Candidates corresponding to small molecules consumed one attempt when their identity was incorrect. Correctly identified molecules outside the single-residue, complete-atom scope were skipped without charge. Eligible, correctly identified instances consumed one attempt and were assessed using the Build pose.

Completion was calculated separately for each PDB, followed by a PDB-equal mean and median. With $P$ PDBs, macro-mean completion is $P^{-1}\sum_{p=1}^{P}F_p(\rho)$. The plots show relative attempt budgets from 0% to 300%. The 300% limit defines the displayed range, not the maximum number of attempts in the frozen candidate sequence. Completion remained constant after candidate exhaustion.

### Detection and identity matching across all ligand classes

Increasing the relative attempt budget from 100% to 300% raised macro-mean instance completion from 62.1% to 67.5% for GT and from 51.1% to 58.8% for CA2 ({{figref:supp-e2e-completion-all}}). The corresponding medians increased from 66.7% and 50.0% to 71.4% and 60.2%, respectively. Larger budgets recovered additional instances under both receptor conditions, while the PDB-level distributions showed variation in completion across complexes.

{{pptfig:"画图/E2E实例完成度.pptx"|supp-e2e-completion-all}}

<table>
<caption>Table 1 | All-ligand instance completion (%). Means are PDB-equal macro means; medians were calculated across the same 179 PDBs.</caption>
<tr><th>Input</th><th>100% mean</th><th>100% median</th><th>300% mean</th><th>300% median</th></tr>
<tr><td>GT</td><td>62.1</td><td>66.7</td><td>67.5</td><td>71.4</td></tr>
<tr><td>CA2</td><td>51.1</td><td>50.0</td><td>58.8</td><td>60.2</td></tr>
</table>

### Modelling organic small molecules with one residue and no missing atoms

Small-molecule completion required detection by Find, correct identity assignment by Match, and a PocketXMol-tuned pose satisfying the heavy-atom root-mean-square deviation (RMSD) threshold. The top-1 pose retained the model's self-ranking. The best-of-50 pose was the generated pose with the lowest heavy-atom RMSD among 50 candidates for each candidate region, assessing pose-generation coverage. Both assessments used strict RMSD thresholds of <2 Å and <3 Å, preserving the original pose ranking and success criteria.

For top-1 poses with RMSD <2 Å, macro-mean completion was 55.1% for GT at both 100% and 300% budgets. CA2 completion increased from 41.1% to 44.9% ({{figref:supp-e2e-completion-small}}). At a 300% budget, best-of-50 completion was 64.4% for GT and 55.9% for CA2 at RMSD <2 Å. The corresponding values at RMSD <3 Å were 66.9% and 62.8%. The gap between best-of-50 and top-1 completion showed that some correct poses were generated but were not ranked first by the model.

{{pptfig:"画图/E2E实例完成度.pptx"|supp-e2e-completion-small}}

<table>
<caption>Table 2 | Small-molecule instance completion (%). Means are PDB-equal macro means; medians were calculated across the same 77 PDBs. All 446 eligible instances remained in their respective PDB denominators.</caption>
<tr><th>Input</th><th>Pose</th><th>RMSD</th><th>100% mean</th><th>100% median</th><th>300% mean</th><th>300% median</th></tr>
<tr><td>GT</td><td>Top-1</td><td>&lt;2 Å</td><td>55.1</td><td>75.0</td><td>55.1</td><td>75.0</td></tr>
<tr><td>CA2</td><td>Top-1</td><td>&lt;2 Å</td><td>41.1</td><td>16.7</td><td>44.9</td><td>25.0</td></tr>
<tr><td>GT</td><td>Top-1</td><td>&lt;3 Å</td><td>60.1</td><td>100.0</td><td>61.1</td><td>100.0</td></tr>
<tr><td>CA2</td><td>Top-1</td><td>&lt;3 Å</td><td>47.7</td><td>33.3</td><td>53.0</td><td>50.0</td></tr>
<tr><td>GT</td><td>Best of 50</td><td>&lt;2 Å</td><td>63.5</td><td>100.0</td><td>64.4</td><td>100.0</td></tr>
<tr><td>CA2</td><td>Best of 50</td><td>&lt;2 Å</td><td>49.1</td><td>50.0</td><td>55.9</td><td>83.3</td></tr>
<tr><td>GT</td><td>Best of 50</td><td>&lt;3 Å</td><td>66.0</td><td>100.0</td><td>66.9</td><td>100.0</td></tr>
<tr><td>CA2</td><td>Best of 50</td><td>&lt;3 Å</td><td>54.7</td><td>66.7</td><td>62.8</td><td>100.0</td></tr>
</table>
