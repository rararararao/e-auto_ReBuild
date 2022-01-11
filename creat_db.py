import sqlite3

conn = sqlite3.connect('e-auto.db')
c = conn.cursor()

c.execute('create table choice(jp text,choices text,ans text)') #択一問題 ｛日本語文,解答群,解答｝
c.execute('create table line_up(jp text,choices text,ans text)') #並べ替え問題 ｛日本語文,解答群,解答｝
c.execute('create table enter(jp text,en text,ans text)') #空所記入問題 ｛日本語文,英語文,解答｝

conn.commit()
conn.close()