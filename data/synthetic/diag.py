import pandas as pd
df = pd.read_csv("data/synthetic/intelli_credit_dataset.csv")

# High-null columns
high = [(c, df[c].isna().mean()) for c in df.columns if df[c].isna().mean() > 0.30]
print("=== Columns with >30% nulls ===")
for c, pct in sorted(high, key=lambda x: -x[1]):
    has_tag = any(t in c for t in ["_growth","_velocity","_acceleration","_slope","beneish_","piotroski_","months_to_dscr"])
    tag = " [expected]" if has_tag else " [UNEXPECTED]"
    print(f"  {pct:.1%}  {c}{tag}")

# DSCR
h = df[df["label"]==0]["dscr"].dropna()
d = df[df["label"]==1]["dscr"].dropna()
print(f"\n=== DSCR ===")
print(f"Healthy   median={h.median():.2f}  mean={h.mean():.2f}  p25={h.quantile(0.25):.2f}  p75={h.quantile(0.75):.2f}")
print(f"Defaulted median={d.median():.2f}  mean={d.mean():.2f}  p25={d.quantile(0.25):.2f}  p75={d.quantile(0.75):.2f}")

# Beneish
ms = df[df["beneish_m_score"].notna()]
hf = ms[ms["label"]==0]["beneish_manipulation_flag"].mean()
df2 = ms[ms["label"]==1]["beneish_manipulation_flag"].mean()
print(f"\n=== Beneish ===")
print(f"Healthy flag rate: {hf:.1%}")
print(f"Defaulted flag rate: {df2:.1%}")
