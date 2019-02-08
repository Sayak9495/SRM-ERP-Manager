import time
import random
from bs4 import BeautifulSoup

from selenium import webdriver
from PIL import Image
from io import BytesIO

from threading import Thread

from flask import Flask, session, redirect
from flask import request
from flask import send_file
from flask import render_template
from selenium.webdriver.common.action_chains import ActionChains
import os

app = Flask(__name__,static_url_path='/static')

driver = None
uname = None
pwd = None

def init_driver():
	global driver
	driver=webdriver.Chrome("D:\\chromedriver_win32\\chromedriver.exe")
	driver.get("http://evarsity.srmuniv.ac.in/srmsip/")


@app.route("/")
def start():
	thr = Thread(target=init_driver)
	thr.start()
	return render_template('index.html')


@app.route("/",methods=['POST'])
def start_():
	global uname
	global pwd
	uname = request.form['uname']
	pwd = request.form['pwd']
	return redirect("/init")

@app.route("/init")
def init():
	#Start Selenium instance, enter id and pwd and get captcha_img
	
	global driver
	captcha_img = driver.find_element_by_class_name('captcha').screenshot_as_png
	print(type(captcha_img))
	im = Image.open(BytesIO(captcha_img))
	im_rand_name = str(random.randint(99,9999999909999))+".png"
	im.save('static/'+im_rand_name)
	captcha_req = driver.find_element_by_id('sdivcolor')
	return render_template('captcha_init.html',src=im_rand_name,captcha_req=captcha_req.text)

@app.route("/init",methods=['POST'])
def login():
	global driver
	global uname
	global pwd
	captcha = request.form['captcha']
	uname_field = driver.find_element_by_xpath('(//*[@class="inputcls"])[1]')
	uname_field.click()
	uname_field.send_keys(uname)
	pwd_field = driver.find_element_by_xpath('(//*[@class="inputcls"])[2]')
	pwd_field.click()
	pwd_field.send_keys(pwd)
	captcha_field = driver.find_element_by_xpath('(//*[@class="inputcls"])[3]')
	captcha_field.click()
	captcha_field.send_keys(captcha)
	driver.find_element_by_xpath('//*[@id="loginform1"]/table/tbody/tr[7]/td/input[1]').click()
	time.sleep(3) 
	
	att_lst = get_att()
	timetable,legend = get_timetable()
	max_hrs = get_max_hrs(timetable)


	for i in legend:
		if (i not in att_lst):
			att_lst[i]=['NA','NA','NA','NA','NA','NA','NA']

	return (render_template('attendance.html',att_lst=att_lst,timetable=timetable,legend=legend,max_hrs=max_hrs))

def get_att():
	global driver
	element_to_hover_over = driver.find_element_by_xpath('//*[@id="dm0m0i2tdT"]')
	hover = ActionChains(driver).move_to_element(element_to_hover_over)
	hover.perform()
	time.sleep(1)
	driver.find_element_by_xpath('//*[@id="dm0m2i2tdT"]').click()
	time.sleep(1)
	attendance = driver.find_element_by_xpath('//*[@id="home"]')
	attendance = attendance.get_attribute('innerHTML')

	soup = BeautifulSoup(attendance,'html.parser')
	soup = (soup.findAll('tr'))[3:]
	print(len(soup))
	att_lst={}
	#lst.append(['Sub_ID','Sub_Name','Max_hrs','Att_hrs','Absnt_hrs','Avg %','OD/ML %','Total %'])
	for data in soup:
		data_ = data.findAll('td')
		tmp_lst=[]
		for content in data_:
			tmp_lst.append(content.text)
		att_lst[tmp_lst[0].strip()]=tmp_lst[1:]
	
	return(att_lst)

def get_timetable():
	global driver

	### GET TIMETABLE ###
	element_to_hover_over = driver.find_element_by_xpath('//*[@id="dm0m0i2tdT"]')
	hover = ActionChains(driver).move_to_element(element_to_hover_over)
	hover.perform()
	time.sleep(1)
	driver.find_element_by_xpath('//*[@id="dm0m2i1tdT"]').click()
	time.sleep(1)
	timetable = driver.find_element_by_xpath('(//*[@id="home"])[1]')
	timetable = timetable.get_attribute('innerHTML')

	soup = BeautifulSoup(timetable,'html.parser')
	soup = (soup.findAll('tr'))[3:8]
	timetable_lst=[]
	for data in soup:
		data_ = data.findAll('td')[1:]
		tmp_lst=[]
		for content in data_:
			tmp_lst.append(((content.text).split(","))[0])
		timetable_lst.append(tmp_lst)

	### GET LEGEND ###
	legend = driver.find_element_by_xpath('(//*[@id="home"])[2]')
	legend = legend.get_attribute('innerHTML')
	soup = BeautifulSoup(legend,'html.parser')
	soup = (soup.findAll('tr'))[2:]
	legend={}
	for data in soup:
		data_ = data.findAll('td')
		legend[(data_[0].text).strip()]=(data_[1].text).strip()

	### REPLACE TIMETABLE CODES WITH LEGEND ###

	#print("#################")
	return(timetable_lst,legend)

def get_max_hrs(timetable):
	max_hrs={}
	for tt in timetable:
		for t in tt:
			try:
				max_hrs[t] = max_hrs[t]+1
			except:
				max_hrs[t] = 1
	for i in max_hrs:
		max_hrs[i]=max_hrs[i]*15
	return max_hrs

if __name__ == '__main__':
	app.run(debug=True)