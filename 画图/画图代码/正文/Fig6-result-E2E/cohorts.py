"""从具名身份清单取得完整目标分母, 不按检出、身份或姿态成功缩小集合."""


# ================================================================================================
def read_cohorts(store, with_full: bool):
    """返回全配体计数、小分子成员及PDB内精确SMILES类别.

    store: SourceStore, 本次原字节读取. with_full: bool, 当前图需要179-PDB全配体时才读取held_out清单. 返回full_counts为dict[PDB,int]或空dict; members为dict[PDB,set[int]], 固定77-PDB/446原实例; identities为dict[(PDB,SMILES),str], 类别如small_molecule, 精确字符串是身份连接键.
    """
    # 原件 /storage/penghongen/Matcher/manifests/test_smallmolecule_v1/identities.jsonl, stage3_occurrence_ids是该PDB该身份的合格原实例编号列表, 如[1,3], 不是预测blob轴; smiles是完整身份字符串, type_tag是原类别.
    # 原生产说明 /home/penghongen/Feedback/Matcher/releases/Matcher_cab21d9ceea5/Matcher/matcher/evaluation/README.md; 本地 C:/Users/15919/Desktop/Matcher/matcher/evaluation/README.md.
    rows = store.json("/storage/penghongen/Matcher/manifests/test_smallmolecule_v1/identities.jsonl")
    members = {}
    for row in rows:
        if row["stage3_occurrence_ids"]:
            members.setdefault(row["pdb_id"], set()).update(row["stage3_occurrence_ids"])
    identities = {(r["pdb_id"], r["smiles"]): r["type_tag"] for r in rows}
    assert (len(members), sum(map(len, members.values()))) == (77, 446)
    full = {}
    if with_full:
        # 原件 /storage/penghongen/AdaLigand/held_out/split/held_out_06_chain/held_out_identity.jsonl, selection.test_0是测试成员资格, ligands.total_count是该PDB全部真实实例数, 如4; 不根据本图成功状态过滤.
        # 预处理说明 C:/Users/15919/Desktop/AdaLigand/Data_Preprocessing/Ori_Data/README.md; 当前论文采用的原清单来源见追溯文档/source/原始输入.md.
        rows = store.json("/storage/penghongen/AdaLigand/held_out/split/held_out_06_chain/held_out_identity.jsonl")
        full = {r["pdb_id"]: r["ligands"]["total_count"] for r in rows if r["selection"]["test_0"]}
        assert (len(full), sum(full.values())) == (179, 2502)
    return full, members, identities
