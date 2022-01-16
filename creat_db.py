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


import sqlite3

conn = sqlite3.connect('e-auto.db')
c = conn.cursor()

c.execute('create table choice(jp text,choices text,ans text)') #択一問題 ｛日本語文,解答群,解答｝
c.execute('create table line_up(jp text,choices text,ans text)') #並べ替え問題 ｛日本語文,解答群,解答｝
c.execute('create table enter(jp text,en text,ans text)') #空所記入問題 ｛日本語文,英語文,解答｝

conn.commit()
conn.close()