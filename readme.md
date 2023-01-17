# CyberPhysicalSolution22-team-d
## Description
2022年度サイバーフィジカルソリューション 競技会C チームDのリポジトリです。

## Setup
venvを用いた仮想環境で依存ライブラリをインストールするには
```bash
sudo apt update && sudo apt upgrade
sudo apt install -y python3-venv zbar-tools

python3 -m venv env
source env/bin/activate

pip3 install -r requirements.txt
```
仮想環境に入る際は
```bash
source ./env/bin/activate
```
とし、仮想環境から抜ける際は
```bash
deactivate
```
とします。
