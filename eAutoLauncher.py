"""
	(C)opyright 2022 noko1024(https://github.com/noko1024) polyacetal(https://github.com/polyacetal) yugu0202(https://github.com/yugu0202)


    This file is part of e-auto.

    e-auto is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License

    e-auto is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with e-auto.  If not, see <https://www.gnu.org/licenses/>.


"""


import os
import sys
import platform
import subprocess
import zipfile
import re
import urllib.request
import sqlite3

basePath = os.path.split(os.path.realpath(__file__))[0]
print(basePath)

class ChromeDriverInstall():
    def __init__(self):
        self.pf = platform.system()
        self.version = ""
        self.downloadPath = os.path.join(basePath,"temp.zip") 
        self.chromeDriverPath = os.path.join(basePath,"lib")

    def VersionCheck(self):
        if self.pf == "Windows":
            try:
                res = subprocess.check_output('dir /B/O-N "C:\Program Files\Google\Chrome\Application" |findstr "^[0-9].*¥>',shell=True)
            except:
                res = subprocess.check_output('dir /B/O-N "C:\Program Files (x86)\Google\Chrome\Application" |findstr "^[0-9].*¥>',shell=True)
            self.version = res.decode("utf-8")[0:2]
        
        elif self.pf == "Darwin":
            res = subprocess.check_output("/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version",shell=True)
            self.version = re.search(r'\d+.*',res.decode("utf-8")).group()[0:2]
            print("---This OS type is Passive Support---")

        elif self.pf == "Linux":
            res = subprocess.check_output("google-chrome --version|grep -o [0-9].*",shell=True)
            self.version = res.decode("utf-8")[0:2]
            print("---This OS type is Passive Support---")
        
        return self.version
    
    def ChromeDriverDL(self):
        OSdict = {
            "Windows":"win32",
            "Darwin":"mac64",
            "Linux":"linux64"
        }
    
        req = urllib.request.Request("https://chromedriver.storage.googleapis.com/LATEST_RELEASE_"+self.version)
        with urllib.request.urlopen(req) as res:
            chromeDriverVer = res.read().decode("utf-8")
        
        chromeDriverVer = re.search(r'\d+.*',chromeDriverVer)
    
        if chromeDriverVer == None:
            print("現在インストールされている Google Chrome はサポート対象外です。\n他のバーションでお試し下さい")
            return 1
        else:
            chromeDriverVer = chromeDriverVer.group()
    
    #ChromeDriverのzipをダウンロード
        urllib.request.urlretrieve("https://chromedriver.storage.googleapis.com/"+chromeDriverVer+"/chromedriver_"+OSdict.get(self.pf)+".zip",self.downloadPath)

    #既にlibフォルダがあるときはmkdirをスキップ
        try:
            os.mkdir(self.chromeDriverPath)
        except:
            pass

        #ZIPファイルを解凍しlibファイルに格納
        with zipfile.ZipFile(self.downloadPath) as existing_zip:
            existing_zip.extractall(self.chromeDriverPath)
        os.remove(self.downloadPath)

        return 0

class DataBaseIO():
    def __init__(self):
        self.DataBasePath = os.path.join(basePath,"e-auto.db") 
    
    def Drop(self):
        conn = sqlite3.connect(self.DataBasePath)
        c = conn.cursor()
        c.execute('DROP TABLE IF EXISTS choice')
        c.execute('DROP TABLE IF EXISTS line_up')
        c.execute('DROP TABLE IF EXISTS enter')
        conn.commit()
        conn.close()

    def Create(self):
        conn = sqlite3.connect(self.DataBasePath)
        c = conn.cursor()
        c.execute('create table choice(jp text,choices text,ans text)')
        c.execute('create table line_up(jp text,choices text,ans text)')
        c.execute('create table enter(jp text,en text,ans text)')
        conn.commit()
        conn.close()

    def Initialize(self,initMode=False):
        if initMode == True and os.path.isfile(self.DataBasePath):
            self.Drop()
            self.Create()
        
        elif initMode ==False and os.path.isfile(self.DataBasePath):
                print("データベースファイルが既に存在しています。データを削除して初期化を続行しますか？\nデータベースを初期化する場合は y を入力して下さい。")
                if input(">") == "y":
                    self.Drop()
                    self.Create()
                else:
                    print("データベースファイルの初期化を行いませんでした。")
                    return
        else:
            self.Create()




def Main():
    while True:
        print("e-auto Lancherへようこそ")
        print("\n[1]e-autoを起動する\n[2]e-autoの環境を構築する\n[3]e-autoのデータベースを再構築する\n  (e-autoが正常に解答を行わない場合,正常に起動しない場合にお試しください)\n[4]e-autoのライブラリを再構築する\n  (e-autoが正常に起動しない場合にお試しください)\n[5]e-auto Launcherを終了する")
        print("\n利用したい項目の番号を入力して下さい")
        num = input(">")
        if num.isdecimal() and re.fullmatch("[1-5]",num) is not None:
            if num == "1":
                import eAuto
                eAuto.EAutoMain()
                break
            if num == "2":
                print("環境の構築を開始します。")
                print("ライブラリをダウンロード中…")
                CD = ChromeDriverInstall()
                print("Google Chrome Version:"+CD.VersionCheck())
                if not CD.ChromeDriverDL() == 1:
                    print("データベースを構築中")
                    DataBaseIO().Initialize()
                    print("完了しました。")
            if num == "3":
                print("このオプションを利用すると、E-Learningの解答に使われるデータを削除して正常動作に戻るよう試みるため、回答時間が大幅に伸びる可能性があります。\n実行する場合は y を入力してください。")
                if input(">") == "y":
                    print("再構築を開始します。")
                    DataBaseIO().Initialize(True)
                    print("完了しました。")
            if num == "4":
                print("ライブラリを再構築中...")
                CD = ChromeDriverInstall()
                print("Google Chrome Version:"+CD.VersionCheck())
                CD.ChromeDriverDL()
                print("完了しました。")
            if num == "5":
                sys.exit(0)
        print("")

if __name__ == "__main__":
    Main()
