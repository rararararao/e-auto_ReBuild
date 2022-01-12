import os
import requests
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import lxml
import getpass
import time
import re
import random
import sqlite3

basePath = os.path.split(os.path.realpath(__file__))[0]

#ユーザー情報の入力待機
chromedriver_path = "" #Chromedriverのディレクトリパス
if os.name == "nt":
	chromedriver_path=os.path.join(*[basePath,"lib","chromedriver.exe"])
else:
	chromedriver_path = os.path.join(*[basePath,"lib","chromedriver"])

user_id = input("id>")#e-LeaningのID
user_pass = getpass.getpass("pass>")#e-Leaningのパスワード

#Chromeの起動
options = webdriver.ChromeOptions()
options.add_argument("--ignore-certificate-errors")
options.add_argument("--ignore-ssl-errors")
browser = webdriver.Chrome(chromedriver_path,options=options)
browser.implicitly_wait(5)

root_URL = "https://www.brains-el.jp"

conn = sqlite3.connect('e-auto.db')
c = conn.cursor()


#ログイン用の関数
def login():
	#ログインのURL
	url_login = "https://www.brains-el.jp/"
	browser.get(url_login)
	#ユーザー情報の送信
	e = browser.find_element_by_xpath("//*[@data-name=\"login_id\"]")
	e.clear()
	e.send_keys(user_id)
	e = browser.find_element_by_xpath("//*[@data-name=\"password\"]")
	e.clear()
	e.send_keys(user_pass)
	#ログインボタンのクリック
	btn = browser.find_element_by_css_selector(".btn.btn-default.pull-right")
	btn.click()

#lessonの進捗度100%じゃないもののURLのリストを返す関数
def LessonDataGet():
	while True:
		browser_source = browser.page_source
		#ページソースがなければ==読み込みに失敗したら一秒待ってF5
		if not browser_source:
			time.sleep(1)
			browser.refresh()
			continue

		soup = BeautifulSoup(browser_source,"lxml")
		lesson = soup.find("div",{"class":"panel panel-success"})

		if lesson is None:
			break
		#TAG
		lesson_list = lesson.select(".list-group.subject_list")

		lesson_URL_list = []

		for lesn in lesson_list:
			percent = LessonProgressGet(lesn)
			if percent != "100" and percent is not None:
				lesson_URL_list.append(LessonURLGet(lesn))

		break

	return lesson_URL_list

#lessonの進捗度を取得する関数
def LessonProgressGet(lesson):

	if lesson is None:
		return None

	progress_div = lesson.find("div",{"class":"progress_rate"})

	percent = progress_div.find("span")
	percent = re.search(r"\d+",percent.get_text())
	if percent is None:
		return None

	return percent.group()

#lessonのURLを取得する関数
def LessonURLGet(lesson):

	lesson_URL = lesson.find("a",{"class":"list-group-item clearfix"})

	lesson_URL = lesson_URL.get("href")
	if lesson_URL is None:
		return ""

	return lesson_URL

def AutoQuestionSelect(lesson_URL):
	while True:
		browser_source = browser.page_source
		#ページソースがなければ==読み込みに失敗したら一秒待ってF5
		if not browser_source:
			time.sleep(1)
			browser.refresh()
			continue

		soup = BeautifulSoup(browser_source,"lxml")
		question_list = soup.select(".each_step")

		if question_list is None:
			break

		for question in question_list:
			btn_chk = question.select(".class_button.btn.btn-warning")
			if not btn_chk:
				continue
			break

		#lessson_num:lessonいくつかを取得
		#course_num : courseを取得(通常レッスンとランダム演習の判定に利用)

		btn = browser.find_element_by_css_selector(".class_button.btn.btn-warning")
		btn.click()

		time.sleep(1)
		#ここで自動解答関数を呼ぶ
		while True:
			stop_time = random.randint(10,20)#元(3,40)テスト推奨(7,20)
			print("sleep in",stop_time)
			time.sleep(stop_time)
			print("sleep out")
			get_bool,question_type,question_japanese,question_text,answer_choices = GetQuestionData()
			print(get_bool)
			if not get_bool:
				break
			AutoAns(question_type,question_japanese,question_text,answer_choices)

		#これはすぐ飛ばないようにする為
		time.sleep(3)
		#これは多分解答後に自動的に戻されるはずなのでいらないかも(自動解答出来上がるまでは必須)
		#browser.get(root_URL+lesson_URL)

#問題のデータを取得する get_bool:取得できたか question_text:問題の英文 question_japanese:問題の日本語 question_type:なに問題か(文字列)
def GetQuestionData():
	count = 1
	get_bool = True
	question_text = ""
	answer_choices:list = None

	while True:
		try:
			soup = BeautifulSoup(browser.page_source,"lxml")
			question_japanese = soup.find("p",{"class":"hint_japanese"}).get_text().strip()
			print(question_japanese,question_text)
			question_type:str = soup.select("div.pull-left")[1]
			print("question_type:",question_type)
			question_type = question_type.get_text().split()[2]
			print("question_type:",question_type)
			question_type_index = question_type.find("（")
			if question_type_index != -1:
				question_type = question_type[:question_type_index]
			
			if question_type.startswith("択一") or question_type.startswith("並べ替え"):
				answer_choices = [x.get_text() for x in soup.find("div",{"class":"choice_area"}).select("a")]
			if question_type.startswith("空所記入"):
				question_text = soup.find("p",{"class":"blanked_text"}).get_text()
				question_text = re.sub("-+","",question_text)
			break
		except:
			if count == 2:
				get_bool = False
				return False,None,None,None,None
			else:
				count += 1
				print(count)
				browser.refresh()
				time.sleep(1)
				continue
	print("question")
	print(question_type,question_japanese,question_text,answer_choices)
	print("----")

	return get_bool,question_type,question_japanese,question_text,answer_choices

def AutoAns(question_type,question_japanese,question_text,answer_choices):
	print("オートアンスに入ったよ")
	"""
	Data Base Structures
		- 択一問題 ｛日本語文,解答群,解答｝
			choice(jp text,choices text,ans text)
		- 並べ替え問題 ｛日本語文,解答群,解答｝
			line_up(jp text,choices text,ans text)
		- 空所記入問題 ｛日本語文,英語文,解答｝
			enter(jp text,en text,ans text)
	"""

	dont_know = True

	soup = BeautifulSoup(browser.page_source,"lxml")

	if question_type == "択一問題":
		print("択一問題だよ")

		ans_list = soup.select(".each_choice")
		
		c.execute('select ans from choice where jp == ?',(question_japanese,))
		result = c.fetchone()

		if not result:	#データベースに登録されていない問題だったとき
			ans_word = ans_list[0].get("data-answer")
			ans_btn = f"//a[@data-answer=\"{ans_word}\"]/span/button"
			print("わからない")
		else:
			dont_know = False
			for ans in ans_list:
				ans_word = ans.get("data-answer")

				print("ans_word:",ans_word)
				print("word:",result[0].strip())

				if ans_word == result[0].strip():
					ans_btn = f"//a[@data-answer=\"{ans_word}\"]/span/button"

		try:
			btn = browser.find_element_by_xpath(ans_btn)
			btn.click()
		except:
			time.sleep(1)
			btn = browser.find_element_by_xpath(ans_btn)
			btn.click()


	elif question_type.startswith("並べ替え"):
		print("並べ替え問題だよ")

		ans_list = soup.select(".each_choice.ui-draggable.ui-draggable-handle")
		ans_btns = []

		c.execute('select ans from line_up where jp == ? and choices == ?',(question_japanese," ".join(answer_choices)))
		result = c.fetchone()

		if result:
			dont_know = False
			result_list = result[0].split(",")
			for word in result_list:
				for ans in ans_list:
					ans_word = ans.get("data-answer")
					if ans_word == word:
						ans_btns.append(f"//a[@data-answer=\"{ans_word}\"]")
						break

			for ans_btn in ans_btns:
				btn = browser.find_element_by_xpath(ans_btn)
				btn.click()
		else:
			print("わからない")

		btn = browser.find_element_by_css_selector(".answer.btn.btn-warning")
		btn.click()

	elif question_type == "空所記入問題":

		c.execute('select ans from enter where jp == ? and en == ?',(question_japanese,question_text))
		result = c.fetchone()

		if result:
			dont_know = False
			result_list = result[0].split(",")
			for word in result_list:
				#ここが複数個の時に集め方が今のところ定まってないので待機
				ans_form = browser.find_element_by_xpath("//*[@class=\"blank_container\"]/input")
				ans_form.clear()
				ans_form.send_keys(word)
				time.sleep(0.5)
			btn = browser.find_element_by_css_selector(".answer.btn.btn-warning")
			btn.click()
		else:
			print("わからない")
			ans_form = browser.find_element_by_xpath("//*[@class=\"blank_container\"]/input")
			ans_form.clear()
			ans_form.send_keys(" ")
			time.sleep(0.5)

		"""
		for ans in result:
			ans_form = browser.find_element_by_xpath("//*[@class=\"blank_container\"]/input")
			ans_form.clear()
			ans_form.send_keys(ans)
			time.sleep(0.5)
		"""


	if dont_know:
		AutoCollect(question_type)

	stop_time = random.randint(1,3)
	time.sleep(stop_time)

	btn = browser.find_element_by_css_selector(".btn.btn-default.next_question")
	btn.click()



"""
問題に解答しようとして、DBにデータが存在しない場合解答をスキップし、AutoCollectを呼び出す
1. 問題文,解答群,解答のDataをELからスクレイピングする
2. 1をDBへ登録する 
"""
def AutoCollect(question_type:str):
	time.sleep(5)
	print("autoCollectに入ったよ")
	"""
	Data Base Structures
		- 択一問題 ｛日本語文,解答群,解答｝
			choice(jp text,choices text,ans text)
		- 並べ替え問題 ｛日本語文,解答群,解答｝
			line_up(jp text,choices text,ans text)
		- 空所記入問題 ｛日本語文,英語文,解答｝
			enter(jp text,en text,ans text)
	"""

	soup = BeautifulSoup(browser.page_source,"lxml")
	#引数を元にスクレイピング
	if question_type.startswith("択一"):
		question_jp = soup.find("p",{"class":"hint_japanese"}).text
		answer_choices = " ".join([x.get_text() for x in soup.find("div",{"class":"choice_area"}).select("a")])
		answer = soup.select_one("td.dt_data.english").text
		c.execute("insert into choice(jp,choices,ans) values(?,?,?)",(question_jp,answer_choices,answer))

	elif question_type.startswith("並べ替え"):
		question_jp = soup.find("p",{"class":"hint_japanese"}).text
		answer_choices = " ".join([x.get_text() for x in soup.find("div",{"class":"choice_area"}).select("a")])
		answer:str = ",".join([x.text for x in soup.select("td.dt_data.english > span.marked")])
		c.execute("insert into line_up(jp,choices,ans) values(?,?,?)",(question_jp,answer_choices,answer))

	elif question_type.startswith("空所記入"):
		question_jp = soup.find("p",{"class":"hint_japanese"}).text
		answer_en = soup.find("p",{"class":"blanked_text"}).text
		answer:str = ",".join([x.text for x in soup.select("td.dt_data.english > span.marked")])
		c.execute("insert into enter(jp,en,ans) values(?,?,?)",(question_jp,answer_en,answer))
	

	conn.commit()
	#return 


def main():
	login()
	btn = browser.find_element_by_css_selector(".button.btn.btn-large.btn-.learning.text-center.center-block.orange")
	time.sleep(1)
	btn.click()
	lesson_URL_list = LessonDataGet()
	for lesson_URL in lesson_URL_list:
		browser.get(root_URL+lesson_URL)
		AutoQuestionSelect(lesson_URL)
		#これはすぐ飛ばないようにする為
		time.sleep(10)


if __name__ == "__main__":
	main()
	#DBを閉じます。
	conn.close()
	input("PLEASE PRESS ENTER")
