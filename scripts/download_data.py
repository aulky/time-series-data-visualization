"""Download Metro Interstate Traffic Volume (UCI id 492) and save raw CSV.

Writes an unmodified snapshot to data/raw/metro_interstate_traffic_volume.csv:
features and target concatenated in UCI column order, dates kept as the
original strings, no row dropped, no value altered. All quality issues are
handled in scripts/preprocess.py / the notebook.
"""

from hashlib import sha256
from pathlib import Path

import pandas as pd
from ucimlrepo import fetch_ucirepo

RAW_PATH = Path("data/raw/metro_interstate_traffic_volume.csv")


def main() -> None:
    dataset = fetch_ucirepo(id=492)
    features = dataset.data.features
    targets = dataset.data.targets
    frame = pd.concat([features, targets], axis=1)

    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(RAW_PATH, index=False, lineterminator="\n")  # LF, platform-independent byte output

    print(f"saved        : {RAW_PATH} ({RAW_PATH.stat().st_size:,} bytes)")
    print(f"shape        : {frame.shape}")
    print(f"columns      : {list(frame.columns)}")
    print(f"dataset name : {dataset.metadata.name}")
    print(f"instances    : {dataset.metadata.num_instances}")
    print(f"sha256       : {sha256(RAW_PATH.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
