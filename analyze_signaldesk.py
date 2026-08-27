import pandas as pd
 
CSV_PATH = "sample-data/product_usage_data.csv"
 
 
def load_and_clean(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
 
    # --- Data quality fixes worth calling out ---
 
    # 1. Team names are inconsistently cased ("Product" vs "product").
    #    Without this, groupby would silently split one team into two.
    df["team"] = df["team"].str.strip().str.title()
 
    # 2. median_confidence has a literal "n/a" string on one row, which
    #    would otherwise make the whole column non-numeric.
    df["median_confidence"] = pd.to_numeric(df["median_confidence"], errors="coerce")
 
    # 3. Exact duplicate row (Sales / Lead summary / email, 2026-08-05).
    #    The notes column ("duplicate export row") confirms this is a
    #    data export artifact, not two real days of usage, so drop it.
    before = len(df)
    df = df.drop_duplicates(
        subset=[c for c in df.columns if c != "notes"], keep="first"
    )
    dupes_dropped = before - len(df)
    if dupes_dropped:
        print(f"[cleaning] Dropped {dupes_dropped} exact duplicate row(s).\n")
 
    return df
 
 
def workflow_summary(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("workflow", as_index=False).agg(
        sessions=("sessions", "sum"),
        completed=("completed", "sum"),
        accepted_output=("accepted_output", "sum"),
        flagged_for_review=("flagged_for_review", "sum"),
        avg_minutes_saved=("avg_minutes_saved", "mean"),
        median_confidence=("median_confidence", "mean"),
        user_rating=("user_rating", "mean"),
    )
    g["completion_rate"] = (g["completed"] / g["sessions"]).round(2)
    g["acceptance_rate"] = (g["accepted_output"] / g["sessions"]).round(2)
    g["flag_rate"] = (g["flagged_for_review"] / g["sessions"]).round(2)
    g["avg_minutes_saved"] = g["avg_minutes_saved"].round(1)
    g["median_confidence"] = g["median_confidence"].round(2)
    g["user_rating"] = g["user_rating"].round(2)
 
    cols = [
        "workflow", "sessions", "completion_rate", "acceptance_rate",
        "flag_rate", "avg_minutes_saved", "median_confidence", "user_rating",
    ]
    return g[cols].sort_values("sessions", ascending=False)
 
   
def flag_suspicious_days(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flag rows where confidence and outcome quality disagree, or where the
    flag rate is unusually high relative to the workflow's own history.
    This is the check the domain packet explicitly asks for: don't assume
    high model confidence means high quality.
    """
    d = df.copy()
    d["acceptance_rate"] = d["accepted_output"] / d["sessions"]
    d["flag_rate"] = d["flagged_for_review"] / d["sessions"]
 
    # Per-workflow baseline flag rate, so "unusual" is relative, not global.
    baseline = d.groupby("workflow")["flag_rate"].transform("mean")
 
    suspicious = d[
        # confidence is high, but acceptance and rating are weak
        ((d["median_confidence"] >= 0.85) & (d["acceptance_rate"] < 0.5))
        # or flag rate is far above that workflow's own average
        | (d["flag_rate"] > baseline * 1.5)
    ]
 
    cols = [
        "date", "team", "workflow", "source", "sessions",
        "acceptance_rate", "flag_rate", "median_confidence",
        "user_rating", "notes",
    ]
    return suspicious[cols].round(2)
 
 
def main():
    df = load_and_clean(CSV_PATH)
 
    print("=" * 70)
    print("WORKFLOW HEALTH SUMMARY (all days, cleaned)")
    print("=" * 70)
    summary = workflow_summary(df)
    print(summary.to_string(index=False))
 
    print("\n" + "=" * 70)
    print("ROWS WORTH A SECOND LOOK")
    print("=" * 70)
    flagged = flag_suspicious_days(df)
    if flagged.empty:
        print("None found.")
    else:
        print(flagged.to_string(index=False))
        print(
            "\nNote: these are not necessarily 'bad' rows. High confidence "
            "with low acceptance, or an above-average flag rate, just means "
            "the numbers disagree with each other and a human should look "
            "at *why* before drawing conclusions."
        )
 
    print("\n" + "=" * 70)
    print("HEADLINE TAKEAWAY")
    print("=" * 70)
    print(
        "Reply draft on 2026-08-07 is the clearest signal in this data: "
        "median_confidence hit its highest point of the week (0.91) on the "
        "same day acceptance rate and user rating collapsed (flag_rate "
        "spiked to 0.40, rating dropped to 2.1). The note says the review "
        "policy changed mid-day. This is exactly the trap the domain packet "
        "warns about: confidence went up while quality went down. Before "
        "trusting confidence as a quality proxy for Reply draft, someone "
        "should check what changed in the review policy that day."
    )
 
 
if __name__ == "__main__":
    main()
 


