# Cylindrical Ray Trace

同心二重円筒の2次元断面で、厚さゼロの境界を通る光線を追跡するPython CLIです。内半径
`Ri` と外半径 `Ro` の間を絶対屈折率 `n2` の液体、それ以外（外部および内筒内部）を
絶対屈折率 `n1` の媒質として扱います。

## モデル

```text
r < Ri       : n1
Ri < r < Ro  : n2（液体）
r > Ro       : n1
```

各円境界でベクトル形式のスネルの法則を適用し、臨界角を超えた場合は全反射させます。
吸収、散乱、偏光、干渉、回折およびフレネル反射率は扱いません。表示する光路長は、
有限な境界間区間について `OPL = Σ(n_i L_i)` で計算します。

## インストールと実行

```bash
python -m pip install -e .
python -m cylindrical_raytrace \
  --inner-radius 1 --outer-radius 2 \
  --n1 1.0 --n2 1.33 \
  --origin-x -4 --origin-y 0.5 --angle-deg 0
```

角度は正のx軸から反時計回りの度数です。`--output-format json` でJSONを出力できます。
描画機能に必要な `matplotlib` は通常のインストールに含まれます。`--plot ray.png` を
指定すると光路図を保存します。

```bash
python -m cylindrical_raytrace \
  --inner-radius 1 --outer-radius 2 \
  --n1 1.0 --n2 1.33 \
  --origin-x -4 --origin-y 0.5 --angle-deg 0 \
  --plot ray.png
```

既に旧バージョンをインストールしていて `plotting requires` と表示される場合は、
プロジェクトのルートで `python -m pip install -e .` を再実行してください。

```bash
python -m cylindrical_raytrace --help
pytest
```

`--max-events` は全反射が続く場合の停止上限です。始点はどの領域にも置けます。
