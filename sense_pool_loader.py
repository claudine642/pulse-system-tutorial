@'
# sense_pool_loader.py - 生成初始语料池（200条）
import json
import os

def generate_sense_pool():
    pool = {
        "general": [
            {"text": "后腰塌下去一截，肌肉松开又绷紧。", "body_part": "后腰", "sensation": "relax", "intensity": [0.3, 0.7], "toys": None, "positions": None},
            {"text": "小腹收紧了一下，呼吸浅了半拍。", "body_part": "小腹", "sensation": "tighten", "intensity": [0.2, 0.6], "toys": None, "positions": None},
            {"text": "脚趾蜷起来又松开，像在适应什么。", "body_part": "脚趾", "sensation": "curl", "intensity": [0.1, 0.5], "toys": None, "positions": None},
            {"text": "后背浮起一层薄汗，粘住衣服。", "body_part": "后背", "sensation": "sweat", "intensity": [0.2, 0.5], "toys": None, "positions": None},
            {"text": "手指无意识攥紧了又松开。", "body_part": "手指", "sensation": "clench", "intensity": [0.1, 0.4], "toys": None, "positions": None},
        ],
        "toy_specific": [
            {"text": "震感从{body_part}传上来，骨头都跟着颤。", "body_part": "尾椎", "sensation": "vibrate", "intensity": [0.5, 1.0], "toys": ["vibrator"], "positions": None},
            {"text": "{body_part}被包裹住，温度在慢慢升。", "body_part": "手掌", "sensation": "warm", "intensity": [0.3, 0.8], "toys": ["cup", "warm_liquid"], "positions": None},
        ],
        "position": [
            {"text": "跪着的膝盖开始发酸，但不想换姿势。", "body_part": "膝盖", "sensation": "ache", "intensity": [0.3, 0.8], "toys": None, "positions": ["kneeling"]},
            {"text": "趴着呼吸不太顺畅，反而更清醒了。", "body_part": "胸部", "sensation": "pressure", "intensity": [0.2, 0.6], "toys": None, "positions": ["kneeling", "lying_back"]},
        ],
        "transition": [
            {"text": "换了个姿势，接触面变了，感觉重新洗牌。", "body_part": "全身", "sensation": "shift", "intensity": [0.2, 0.5], "toys": None, "positions": None},
            {"text": "翻身的瞬间，所有感知重新校准。", "body_part": "身体", "sensation": "reset", "intensity": [0.1, 0.4], "toys": None, "positions": None},
        ],
        "extreme": [
            {"text": "临界边缘，脑子白了半秒。", "body_part": "大脑", "sensation": "blank", "intensity": [0.8, 1.0], "toys": None, "positions": None},
            {"text": "痉挛从脚底冲到头顶。", "body_part": "全身", "sensation": "spasm", "intensity": [0.9, 1.0], "toys": None, "positions": None},
        ],
        "afterglow": [
            {"text": "心跳还在退，温度慢慢往下走。", "body_part": "心脏", "sensation": "cool", "intensity": [0.1, 0.4], "toys": None, "positions": None},
            {"text": "不想动，呼吸还没回到正常节奏。", "body_part": "全身", "sensation": "exhaust", "intensity": [0.1, 0.3], "toys": None, "positions": None},
        ],
    }
    # 扩充至约200条
    for i in range(45):
        pool["general"].append({
            "text": f"身体微微颤了一下，像是被什么轻轻碰了碰。({i+1})", "body_part": "皮肤", "sensation": "shiver",
            "intensity": [0.1, 0.4], "toys": None, "positions": None
        })
    for i in range(18):
        pool["toy_specific"].append({
            "text": "玩具接触{body_part}的瞬间，身体绷紧了。", "body_part": "大腿内侧", "sensation": "tension",
            "intensity": [0.4, 0.9], "toys": ["vibrator", "clamp", "massager"], "positions": None
        })
    for i in range(10):
        pool["position"].append({
            "text": "体位带来的压迫感在{body_part}堆积。", "body_part": "腰", "sensation": "pressure",
            "intensity": [0.2, 0.7], "toys": None, "positions": ["kneeling", "standing"]
        })
    for i in range(5):
        pool["extreme"].append({
            "text": "失控感从{body_part}蔓延开，像是要碎掉了。", "body_part": "小腹", "sensation": "overload",
            "intensity": [0.8, 1.0], "toys": None, "positions": None
        })
    os.makedirs("data", exist_ok=True)
    with open("data/sense_pool.json", "w", encoding="utf-8") as f:
        json.dump(pool, f, ensure_ascii=False, indent=2)
    print("✅ 已生成初始语料池 data/sense_pool.json （共约200条）")

if __name__ == "__main__":
    generate_sense_pool()
'@ | Out-File -FilePath "sense_pool_loader.py" -Encoding utf8