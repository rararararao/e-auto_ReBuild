import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome import service
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup,NavigableString
import lxml
import getpass
import time
import re
import random
import sqlite3
import traceback



basePath = os.path.split(os.path.realpath(__file__))[0]

#ユーザー情報の入力待機
chromedriver_path = "" #Chromedriverのディレクトリパス
if os.name == "nt":
	chromedriver_path=os.path.join(*[basePath,"lib","chromedriver.exe"])
else:
	chromedriver_path = os.path.join(*[basePath,"lib","chromedriver"])


#Chromeの起動
options = webdriver.ChromeOptions()
options.add_experimental_option('excludeSwitches', ['enable-logging'])
options.use_chromium = True

chrome_service = service.Service(executable_path=chromedriver_path)

browser = webdriver.Chrome(service=chrome_service,options=options)
browser.implicitly_wait(5)

root_URL = "https://www.brains-el.jp"

conn = sqlite3.connect('e-auto.db')
c = conn.cursor()


#ログイン用の関数
def login():
	#ログインのURL
	url_login = "https://www.brains-el.jp/"
	
	user_id = input("id>")#e-LeaningのID
	user_pass = getpass.getpass("pass>")#e-Leaningのパスワード
	
	browser.get(url_login)
	#ユーザー情報の送信
	e = browser.find_element(by=By.XPATH,value="//*[@data-name=\"login_id\"]")
	e.clear()
	e.send_keys(user_id)
	e = browser.find_element(by=By.XPATH,value="//*[@data-name=\"password\"]")
	e.clear()
	e.send_keys(user_pass)
	#ログインボタンのクリック
	btn = browser.find_element(by=By.CSS_SELECTOR,value=".btn.btn-default.pull-right")
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
		try:
			btn = browser.find_element(by=By.CSS_SELECTOR,value=".class_button.btn.btn-warning")
		except NoSuchElementException:
			return 
		btn.click()

		time.sleep(1)
		#ここで自動解答関数を呼ぶ
		while True:
			#stop_time = random.randint(10,20)#元(3,40)テスト推奨(7,20)
			print("sleep in",3)
			time.sleep(3)
			#print("sleep out")
			get_bool,question_type,question_japanese,question_text,answer_choices = GetQuestionData()
			if get_bool == False:
				break
			AutoAns(question_type,question_japanese,question_text,answer_choices)

		#これはすぐ飛ばないようにする為
		time.sleep(3)

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
			question_type:str = soup.select("div.pull-left")[1]
			question_type = question_type.get_text().split()[2]
			question_type_index = question_type.find("（")
			if question_type_index != -1:
				question_type = question_type[:question_type_index]
			
			if question_type.startswith("択一") or question_type.startswith("並べ替え"):
				answer_choices = [GetText(x) for x in soup.find("div",{"class":"choice_area"}).select("a > span")]
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
				browser.refresh()
				time.sleep(1)
				continue
	print("question data get")

	return get_bool,question_type,question_japanese,question_text,answer_choices

def AutoAns(question_type,question_japanese,question_text,answer_choices):
	print("in AutoAns")
	"""
	Data Base Structures
		- 択一問題 ｛日本語文,解答群,解答｝
			choice(jp text,choices text,ans text)
		- 並べ替え問題 ｛日本語文,解答群,解答｝
			line_up(jp text,choices text,ans text)
		- 空所記入問題 ｛日本語文,英語文,解答｝
			enter(jp text,en text,ans text)
	"""

	#stop_time = random.randint(7,17)
	stop_time = 0
	dont_know = True

	soup = BeautifulSoup(browser.page_source,"lxml")

	if question_type == "択一問題":
		print("choice")

		result = None
		ans_list = soup.select(".each_choice")
		
		c.execute('select ans from choice where jp == ?',(question_japanese,))
		result_all = c.fetchall()

		ans_word = ans_list[0].get("data-answer")
		ans_btn = f"//a[@data-answer=\"{ans_word}\"]/span/button"

		if not result_all:	#データベースに登録されていない問題だったとき
			#stop_time -= 5
			print("don't know")
		
		else:
			for result_one in result_all: #DBから複数の要素を返却されたとき
				if result_one[0] in answer_choices: #すべての選択肢が一致すれば解答が含まれているので
					result = result_one[0]

			if result: 
				dont_know = False

				for ans in ans_list:
					ans_word = ans.get("data-answer")
					if ans_word == result:
						ans_btn = f"//a[@data-answer=\"{ans_word}\"]/span/button"

		print("sleep in",stop_time)
		time.sleep(stop_time)

		try:
			btn = browser.find_element(by=By.XPATH,value=ans_btn)
			btn.click()
		except:
			time.sleep(1)
			btn = browser.find_element(by=By.XPATH,value=ans_btn)
			btn.click()


	elif question_type.startswith("並べ替え"):
		print("line up")

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
				btn = browser.find_element(by=By.XPATH,value=ans_btn)
				btn.click()
		else:
			#stop_time -= 5
			print("don't know")

		print("sleep in",stop_time)
		time.sleep(stop_time)

		btn = browser.find_element(by=By.CSS_SELECTOR,value=".answer.btn.btn-warning")
		btn.click()

	elif question_type == "空所記入問題":
		print("enter")

		c.execute('select ans from enter where jp == ? and en == ?',(question_japanese,question_text))
		result = c.fetchone()

		if result:
			print("sleep in",stop_time)
			time.sleep(stop_time)
			dont_know = False
			result_list = result[0].split(",")

			ans_form = browser.find_elements(by=By.XPATH,value="//*[@class=\"blank_container\"]/input")

			for ans_form_one,word in zip(ans_form,result_list):
				#ここが複数個の時に集め方が今のところ定まってないので待機

				ans_form_one.clear()
				ans_form_one.send_keys(word)
				time.sleep(0.5)
				"""
				ans_form = browser.find_element(by=By.XPATH,value="//*[@class=\"blank_container\"]/input")
				ans_form.clear()
				ans_form.send_keys(word)
				time.sleep(0.5)
				"""
				
		else:
			ans_form = browser.find_elements(by=By.XPATH,value="//*[@class=\"blank_container\"]/input")

			for ans_form_one in ans_form:
				ans_form_one.clear()
				ans_form_one.send_keys("a")
				time.sleep(0.5)

			"""
			#stop_time -= 5
			print("sleep in",stop_time)
			time.sleep(stop_time)
			print("don't know")
			ans_form = browser.find_element(by=By.XPATH,value="//*[@class=\"blank_container\"]/input")
			ans_form.clear()
			ans_form.send_keys(" ")
			time.sleep(0.5)
			"""
			
		btn = browser.find_element(by=By.CSS_SELECTOR,value=".answer.btn.btn-warning")
		btn.click()

	if dont_know:
		AutoCollect(question_type)

	stop_time = random.randint(1,3)
	time.sleep(stop_time)

	btn = browser.find_element(by=By.CSS_SELECTOR,value=".btn.btn-default.next_question")
	btn.click()


def GetText(element):	#択一問題の解答を引っ張ってきたときについてくるボタンのアルファベットを消す関数
	text = None

	for e in element.contents:
		if type(e) is NavigableString and str(e).strip():
			text = str(e).strip()
			break

	return text

"""
問題に解答しようとして、DBにデータが存在しない場合解答をスキップし、AutoCollectを呼び出す
1. 問題文,解答群,解答のDataをELからスクレイピングする
2. 1をDBへ登録する 
"""
def AutoCollect(question_type:str):
	time.sleep(3)
	print("in AutoCollect")
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
		answer_choices = " ".join([GetText(x) for x in soup.find("div",{"class":"choice_area"}).select("a > span")]) 
		answer = GetText(soup.select_one("a.each_choice.disabled.correct > span"))
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

	print("collect end")
	#return 


def EAutoMain():
	login()

	try:
		btn = browser.find_element(by=By.CSS_SELECTOR,value=".button.btn.btn-large.btn-.learning.text-center.center-block.blue_green")
	except NoSuchElementException:
		btn = browser.find_element(by=By.CSS_SELECTOR,value=".button.btn.btn-large.btn-.learning.text-center.center-block.orange")

	time.sleep(1)
	btn.click()
	lesson_URL_list = LessonDataGet()
	for lesson_URL in lesson_URL_list:
		browser.get(root_URL+lesson_URL)
		AutoQuestionSelect(lesson_URL)
		#これはすぐ飛ばないようにする為
		time.sleep(10)


if __name__ == "__main__":
	try:
		EAutoMain()
	except Exception as e:
		print("\n---ErrorLOG---\n")
		print(e)
		print("\n------\n")
		print("\n---Traceback---\n")
		traceback.print_exc()
		print("\n------\n")
		#errorLogへの書き出し準備もできるように
	finally:
		#blower Shutdown
		browser.quit()

		#DB commit and close
		conn.commit()
		conn.close()
		input("PLEASE PRESS ENTER")
