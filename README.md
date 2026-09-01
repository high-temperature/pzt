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

### Windowsで旧バージョンが実行される場合

`plotting requires: pip install 'cylindrical-raytrace[plot]'` というエラーは、修正前の
バージョンがPython環境に残っていることを示します。現在のバージョンにはそのエラー文は
存在しません。コマンドプロンプトで、ダウンロードしたプロジェクトのディレクトリへ移動し、
**実行に使うPythonと同じPython**で再インストールしてください。

```bat
cd C:\Users\kyoch\source\repos\pzt-main\pzt-main
python -m pip uninstall -y cylindrical-raytrace
python -m pip install --no-cache-dir .
python -m cylindrical_raytrace --version
```

バージョン表示が `0.1.1` になったら、どのディレクトリからでも実行できます。

```bat
cd C:\Users\kyoch\source\repos
python -m cylindrical_raytrace --inner-radius 1 --outer-radius 2 --n1 1.0 --n2 1.33 --origin-x -4 --origin-y 0.5 --angle-deg 0 --plot ray.png
```

複数のPythonをインストールしている場合は、インストールと実行の両方で同じランチャー
（例えば `py -3.12 -m pip ...` と `py -3.12 -m cylindrical_raytrace ...`）を使ってください。

```bash
python -m cylindrical_raytrace --help
pytest
```

`--max-events` は全反射が続く場合の停止上限です。始点はどの領域にも置けます。

## 超音波：水入りPFAチューブ

`ultrasonic-raytrace` は、内側から順に水、PFA、有限幅の整合層、PZTを配置した2次元
断面を計算します。既定値はPFA `1231 m/s`、水 `1497 m/s`、整合層 `1046 m/s`、
整合層の円周方向幅 `2 mm`、径方向厚さ `0.5 mm`です。整合層がない外周は空気との
境界として、透過させず完全反射させます。PZTに達すると追跡を終了します。

次の例は、内半径4 mm、外半径5 mmのチューブについて、左側（180°）のPZT直前から
中心方向へ超音波を入射します。位置と半径の単位はmm、角度は+x軸基準の度です。

```bash
ultrasonic-raytrace \
  --inner-radius-mm 4 --outer-radius-mm 5 \
  --origin-x-mm -5.49 --origin-y-mm 0 --angle-deg 0 \
  --matching-center-angle-deg 180 \
  --plot ultrasound.png
```

音速や整合層寸法は、それぞれ `--pfa-speed`、`--water-speed`、`--matching-speed`、
`--matching-width-mm`、`--matching-thickness-mm` で変更できます。結果には各境界での
入射角・透過角、媒質、反射、PZT到達判定、および累積伝搬時間（µs）が含まれます。
`--output-format json` も利用できます。

このモデルでは整合層の幅をPFA外周に沿った**円弧長**として解釈し、PZTは整合層の
外面に密着しているものとします。音響インピーダンス（密度）が指定されていないため、
部分反射・透過率・振幅は計算せず、音速によるスネルの法則で経路のみを計算します。
