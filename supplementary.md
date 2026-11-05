# Supplementary Information

## Additional analyses of ligand-region detection

We evaluated instance-level $\mathrm{PRAUC}_{0.5}$ at a stricter bidirectional coverage threshold of 0.5 using the same all-ligand and small-molecule cohorts. These comprised 179 PDB entries with 2,502 instances and 94 PDB entries with 821 small-molecule instances, respectively. For all ligands, PDB-equal means were 0.558 with GT receptors and 0.447 with CA2 receptors, compared with 0.152 for Emap2lig-Find ({{figref:stage1-additional-analysis|a}}). The corresponding small-molecule scores were 0.605, 0.499 and 0.337, preserving the same advantage ({{figref:stage1-additional-analysis|d}}). Instance-level precision and recall also remained higher with both LigandSeek-Find receptor inputs under this stricter criterion ({{figref:stage1-additional-analysis|b,e}}). Compared with the results at the 0.3 threshold ({{draft.md|figref:stage1-overall-performance(v1)|a,d}}), the relative advantage of LigandSeek-Find over Emap2lig-Find became even more pronounced as the threshold was tightened from 0.3 to 0.5.

To further assess detection under limited candidate counts, we measured the fraction of distinct ligand instances recovered from ranked candidates ({{figref:stage1-additional-analysis|c,f}}). A ground-truth ligand instance was considered detected if at least one examined candidate shared a bidirectional coverage of at least 0.3 with it. Relative candidate counts of 100% and 300% allowed examining up to one and three times the ground-truth instance count per PDB, respectively. In the small-molecule evaluation, candidate blobs matched to non-small-molecule ligands (such as metal ions and sugars) were excluded from the candidate count, whereas unmatched false-positive candidates were retained.

From 100% to 300%, mean completion across all ligands increased from 66.4% to 71.7% with GT receptors and from 55.6% to 63.3% with CA2 receptors. Emap2lig-Find increased from 28.5% to 31.4% over the same candidate-count range. Corresponding small-molecule changes were 70.5% to 73.3% for GT, 59.8% to 68.5% for CA2 and 46.6% to 54.9% for Emap2lig-Find. LigandSeek-Find therefore recovered more true instances under the same candidate-count limits.

{{pptfig:"画图/stage1结果.pptx"|stage1-additional-analysis}}

## Ligand-region detection without a supplied contour level

We also evaluated Emap2lig-Find without an explicitly supplied EMDB-recommended contour level across the same all-ligand and small-molecule test cohorts ({{figref:stage1-no-level-comparison-NO_LEVEL}}). Across all ligands, its mean semantic Dice, instance-level $\mathrm{PRAUC}_{0.3}$ and $\mathrm{PRAUC}_{0.5}$ were 0.050, 0.255 and 0.126, respectively. The corresponding small-molecule scores were 0.073, 0.462 and 0.293 ({{figref:stage1-no-level-comparison-NO_LEVEL|a,c}}).

Without a supplied contour level, Emap2lig-Find returned an average of 353.9 candidate regions per PDB entry, compared with 14.0 ground-truth ligand instances. At a bidirectional coverage threshold of 0.3, its PDB-equal mean instance-level precision and recall were 0.037 and 0.312, respectively ({{figref:stage1-no-level-comparison-NO_LEVEL|b}}). Despite this large candidate pool, recall still remained below that of Emap2lig-Find supplied with the recommended contour level (0.316), as well as LigandSeek-Find with CA2 receptors (0.594) or GT receptors (0.688). LigandSeek-Find requires no contour-level input and thus retains the same results as in {{draft.md|figref:stage1-overall-performance(v1)}} and {{figref:stage1-additional-analysis}}. Under both conditions, particularly without a supplied contour level, Emap2lig-Find thus produced more false-positive candidates while achieving lower recall than LigandSeek-Find.

{{pptfig:"画图/stage1结果.pptx"|stage1-no-level-comparison-NO_LEVEL}}

## Stage 1: Ablation of LigandSeek-Find

As shown in Table 1, we compared six model variants on the same full test set to assess the contributions of individual designs to ligand detection. Starting with a 3D U-Net receiving experimental density alone(Density only), we added difference density(+ Difference density), a multi-view density bank(+ Density bank) and receptor-atom features(+ Receptor features). We then introduced centroid-aware positional encoding in the receptor embedding head(+ Centroid encoding), followed by the final LigandSeek-Find model. The final model used receptor-atom binding probabilities predicted by the point-cloud branch for Gaussian candidate scoring, while other models used conventional inference without Gaussian candidate scoring.

According to Table 1, adding difference density improved all metrics under both GT and CA2 conditions. Moreover, the multi-view density bank further improved overall detection ability. It is noteworthy that when constructing multi-view density bank, the deterministic transformations of the same experimental and simulated receptor density do not add any additional information, but highlight ligand signals across contrasts and spatial scales while suppressing dominant receptor density.


Futhermore, we can observe that injecting the receptor information explicitly, adding centroid-aware positional encoding in the receptor embedding head, and introducing Gaussian scoring during inference also generally raise model performance to varying degrees. We refer to the model with all components as LigandSeek-Find, which has the best overall performance.

<table data-layout="booktabs" data-pagination="rows">
<caption>Table 1 | Internal ablation of LigandSeek-Find on the full test set.</caption>
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

## EMERALD-ID identity matching at deposited ligand sites

We also evaluated EMERALD-ID, which identifies small-molecule ligands by docking each candidate identity at each site and ranking the resulting scores. For a PDB entry containing $N_g$ small-molecule instances and $K$ candidate identities, this requires $O(N_gK)$ docking evaluations. LigandSeek-Match used vectorised computation on an NVIDIA H100 GPU, requiring a mean of only 0.09 s per candidate blob. By contrast, among queries returning valid scores, EMERALD-ID required a mean of 166.67 min per site on a single CPU core (median, 75.05 min). The resulting cost made exhaustive evaluation of PDB entries with many ligand sites and competing identities impractical.

To control computational cost, we excluded the 10% of small-molecule-containing test entries with the highest $N_gK$. The resulting subset comprised 357 deposited small-molecule sites from 84 PDB entries. At each site, EMERALD-ID received all small-molecule identities from the same PDB entry. EMERALD-ID also encountered frequent failures during chemical preparation or scoring, leaving many sites without valid results. Among sites with at least one valid candidate score, matching accuracy was 82.6% (233/282) with deposited receptors and 84.0% (263/313) with CryoAtom2 receptors.

## Density-guided Build with Envelope pockets

In addition to defining a binding pocket as a 15 Å sphere around the binding site (the Centre pocket), PocketXMol supports a tighter, ligand-envelope pocket definition (the Envelope pocket), which includes all atoms of any receptor residue with at least one atom within 10 Å of a deposited ligand atom. Using this tighter pocket definition, we compared PocketXMol, FT-PocketXMol and DG-PocketXMol across all 446 eligible small-molecule test instances to provide a complementary test of density guidance ({{figref:stage3-ablation-envelope}}).

With deposited receptors, top-1 success at RMSD < 2 Å was 62.8% for PocketXMol, 63.0% for FT-PocketXMol and 78.0% for DG-PocketXMol; with CryoAtom2 receptors, the corresponding top-1 success rates were 54.9%, 60.8% and 74.7%, respectively. Under the same RMSD < 2 Å criterion, the best-of-50 success rates of DG-PocketXMol reached 97.1% and 94.2% under the two receptor conditions, respectively. Consistently, DG-PocketXMol reduced median top-1 RMSD from 1.55 Å with PocketXMol to 1.14 Å with deposited receptors, and from 1.81 Å to 1.21 Å with CryoAtom2 receptors. Density guidance therefore improved pose reconstruction even when the input pocket was defined more tightly around the ligand.

{{pptfig:"画图/stage2-stage3结果.pptx"|stage3-ablation-envelope}}


## Attempt-accounting rules for end-to-end evaluation

End-to-end evaluation examines candidate ligand regions in the order ranked by LigandSeek-Find. The attempt-accounting rules cover detection and identity matching across all ligand categories, and full pose reconstruction for eligible small molecules ({{figref:e2e-accounting-rules-draft}}). The same rules apply to instance completion and top-k success.

{{pptfig:"画图/E2E评价计费规则.pptx"|e2e-accounting-rules-draft}}



## End-to-end top-k success across complexes

As in the main text, we evaluated three end-to-end capabilities: general-ligand detection and chemical identification (Find + Match), small-molecule detection and pose reconstruction given ground-truth chemical identities (Find + Build), and fully automated small-molecule modelling without prior site or identity assignment (Find + Match + Build).

To complement the instance-level completion reported in the main text, we assessed complex-level top-k success for Find–Match and Find–Match–Build. Top-k success was the fraction of PDB entries containing at least one successful instance within the first $K$ charged attempts ($K=1–10$; {{figref:e2e-topk-success}}). Candidates followed Find's probability ranking, with attempts charged according to the evaluation rules ({{figref:e2e-accounting-rules-draft}}).


The all-ligand cohort comprised 179 PDB entries containing 2,502 ligand instances ({{figref:e2e-topk-success|a}}). With CA2 receptors, Find–Match success increased from 67.0% (120/179) at $K=1$ to 83.8% (150/179) at $K=3$. With deposited receptors, single-attempt Find–Match success was 79.3% (142/179) across the same cohort. At $K=10$, Find–Match success reached 87.7% with CA2 receptors and 92.2% with deposited receptors. These rates approached the corresponding Find-only success rates of 88.8% and 93.3%, respectively. Emap2lig-Find increased from 42.5% at $K=1$ to 58.1% at $K=10$, remaining below both LigandSeek receptor conditions.

The small-molecule cohort contained 77 PDB entries with 446 eligible instances ({{figref:e2e-topk-success|b}}). At $K=1$, Find–Match success was 66.2% with CA2 receptors and 79.2% with deposited receptors. Both conditions reached 81.8% at $K=3$, followed by 81.8% and 83.1%, respectively, at $K=10$. Find-only success at $K=10$ was 88.3% and 89.6%, respectively, compared with 76.6% for Emap2lig-Find. Most entries that could be identified within ten attempts therefore required no more than three attempts.

We then required successful pose reconstruction with DG-PocketXMol, using binding sites predicted by Find ({{figref:e2e-topk-success|c,d}}). At RMSD <2 Å, top-1 success with CA2 receptors increased from 44.2% to 59.7% as $K$ rose from 1 to 10. With deposited receptors, the corresponding top-1 success rates increased from 57.1% to 66.2%. At $K=10$, best-of-50 success at RMSD <3 Å reached 75.3% with CA2 receptors and 76.6% with deposited receptors. Thus, the full pipeline successfully reconstructed at least one small-molecule ligand pose in most PDB entries.

{{pptfig:"画图/E2E结果.pptx"|e2e-topk-success}}

## Find–Build comparison with correct ligand identities

We supplied the correct ligand identities to both pipelines to compare their combined localisation and pose-reconstruction capabilities. The benchmark comprised 77 PDB entries containing 446 eligible small-molecule instances, with Emap2lig additionally supplied with the EMDB-recommended contour level. Each pipeline used its own predicted ligand regions to guide pose reconstruction. Completion was the fraction of distinct target instances successfully modelled within a relative attempt budget, averaged equally across PDB entries. Undetected and failed instances remained in the full target denominator throughout evaluation. The full curves and per-PDB distributions cover Top-1, Top-5 and best-of-50 poses at heavy-atom RMSD <2 Å and <3 Å ({{figref:supp-find-correct-match-build-emap2lig,supp-find-correct-match-build-ca2,supp-find-correct-match-build-gt}}).

At RMSD <2 Å, increasing the budget from 100% to 300% raised Top-5 mean completion from 49.2% to 55.5% with CA2 receptors. With deposited receptors, the corresponding values were 63.3% and 63.9%, compared with 33.7% and 36.1% for Emap2lig. LigandSeek retained higher completion across both RMSD thresholds and all three pose ranges, demonstrating its combined advantage in localisation and pose reconstruction.

{{pptfig:"画图/E2E结果.pptx"|supp-find-correct-match-build-emap2lig}}

{{pptfig:"画图/E2E结果.pptx"|supp-find-correct-match-build-ca2}}

{{pptfig:"画图/E2E结果.pptx"|supp-find-correct-match-build-gt}}

## Find–Match–Build completion with automated identity assignment

We next evaluated small-molecule completion with automated identity assignment across the same 77 PDB entries and 446 eligible instances. Find predicted candidate regions, Match assigned their chemical identities, and DG-PocketXMol reconstructed their poses. An instance was successfully modelled when localisation and identity assignment were correct and its pose satisfied the specified RMSD threshold. Completion retained the full target denominator and was averaged equally across PDB entries. The curves and per-PDB distributions show all three pose ranges under both receptor conditions ({{figref:supp-find-match-build-ca2,supp-find-match-build-gt}}).

At RMSD <2 Å, Top-5 mean completion increased from 46.5% to 52.7% with CA2 receptors as the budget rose from 100% to 300%. With deposited receptors, the corresponding values were 59.4% and 60.0%. At RMSD <3 Å and a 300% budget, best-of-50 completion reached 62.8% with CA2 receptors and 66.9% with deposited receptors. Larger budgets yielded greater completion gains with CA2 receptors, while results with deposited receptors largely plateaued near the 100% budget. Automated identity assignment therefore preserved most of the completion achieved with correct identities supplied to Find–Build.

{{pptfig:"画图/E2E结果.pptx"|supp-find-match-build-ca2}}

{{pptfig:"画图/E2E结果.pptx"|supp-find-match-build-gt}}
