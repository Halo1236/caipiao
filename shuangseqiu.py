"""
专家杀号：https://zx.500.com/ssq/zhuanjiashahao.php
彩票数据：https://datachart.500.com/ssq/
媒体预测：https://zx.500.com/ssq/mediayc.php
"""
import requests
import bs4
import xlwt
import xlrd
import sys
import re
import os
import json
import numpy as np
import datetime
from collections import OrderedDict

class shuangseqiu():
    '''
    双色球类
    获取双色球的各种数据，并进行简单的处理
    '''
    def __init__(self, start_period = None, file_save_name = None, current_issue = None):
        '''
        :param start_period: 开始爬取数据的双色球起始期次，默认"03001"
        :param file_save_name: 文件保存名称, 默认"双色球数据"
        :param current_issue: #当前双色球最新期次，没有默认值
        '''
        self.start_period = "03001" if not start_period else start_period
        self.file_save_name = "双色球数据" if not file_save_name else file_save_name  #保存数据的文件名
        self.all_cai_piao_detailed_data = OrderedDict() #爬取到的所有彩票数据，包括期数、中奖号码、奖金、开奖时间等详细信息
        self.all_cai_piao_ball_list = [] #爬取到的所有彩票开奖号码数据
        self.current_issue = self.getCurrentPeriod() if not current_issue else current_issue
        # 创建data子目录，用于保存数据
        if not os.path.exists(os.path.join(os.getcwd(), "data")):
            os.mkdir(os.path.join(os.getcwd(), "data"))

        #获取当前日期
        now_time = datetime.datetime.now().strftime('%Y-%m-%d')
        self.file_save_dir = os.path.join(os.getcwd(), "data", now_time)
        if not os.path.exists(self.file_save_dir):
            os.mkdir(self.file_save_dir)
            print("创建{}目录，数据将保存在该目录下".format(self.file_save_dir))
        self.cai_piao_detailed_file_path = os.path.join(self.file_save_dir, self.file_save_name + ".xls")

    def getCurrentPeriod(self):
        '''
        :return: 获取双色球最新期次,数据来自"https://kaijiang.500.com/"
        '''
        url = "https://kaijiang.500.com/"
        html = requests.get(url)
        html = bs4.BeautifulSoup(html.text, 'lxml')
        current_issue = html.find_all('tr', id="ssq")[0].find("td", align="center")
        i, j = re.search("\d{5}", current_issue.string).span()
        print("当前双色球最新期数是->", current_issue.string[i:j])
        return current_issue.string[i:j]

    def crawlingData(self, start_period = None):
        '''
        :param start_period: 开始获取数据的期次,从03年开始出售第一期双色球,默认从第一期开始爬取数据
        :return: 提取到的彩票数据
        '''
        url = 'http://datachart.500.com/ssq/history/newinc/history.php?start=%s&end=%s&sort=1' \
              % ( start_period, self.current_issue)  # 可以提取到期号、中奖号码、奖金、开奖日期等信息
        print(url)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0'
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except Exception:
            print("爬取失败!")
            sys.exit()
        else:
            return self.extractData(response.text)

    def extractData(self, response_text):
        '''
        :param response_text: 爬取到的网页文本内容
        :return: 提取到的彩票数据
        '''
        html = bs4.BeautifulSoup(response_text, 'lxml')
        cai_piao_info = html.find_all('tbody', id='tdata')[0].find_all('tr', class_='t_tr1')
        current_row_index = 0
        all_cai_piao_detailed_data = OrderedDict()
        all_cai_piao_ball_list = []
        for index_cai_piao, one_cai_piao in enumerate(cai_piao_info):
            one_cai_piao = one_cai_piao.find_all('td')
            one_cai_piao = [i.text for index, i in enumerate(one_cai_piao) if index != 8]
            all_cai_piao_ball_list.append([int(i) for i in one_cai_piao[1:8]])
            all_cai_piao_detailed_data[index_cai_piao] = one_cai_piao
            current_row_index += 1
        print("一共爬取到%d期彩票数据" % (current_row_index))
        return all_cai_piao_ball_list, all_cai_piao_detailed_data

    def saveData(self, cai_piao_ball_list, cai_piao_detailed_data):
        # 创建一个workbook 设置编码
        workbook = xlwt.Workbook(encoding='utf-8')
        # 创建一个worksheet
        worksheet = workbook.add_sheet("双色球")
        # 将列标题写入excel
        current_row_index = 0
        for i, str_col in enumerate(
                ['期号', '红球', '红球', '红球', '红球', '红球', '红球', '篮球', '奖池奖金', '一等奖注数', '奖金', '二等奖注数', '奖金', '总投注额', '开奖日期']):
            worksheet.write(current_row_index, i, str_col)  # 参数对应 行, 列, 值
        current_row_index += 1
        for _, one_cai_piao in cai_piao_detailed_data.items():
            for index, i in enumerate(one_cai_piao):
                worksheet.write(current_row_index, index, i)
            current_row_index += 1

        # 保存
        workbook.save(self.cai_piao_detailed_file_path)
        #保存数据成npy
        np.save(os.path.join(self.file_save_dir, self.file_save_name), cai_piao_ball_list)
        #保存数据成json格式
        with open(os.path.join(self.file_save_dir, self.file_save_name + ".json"), "w+") as f:
            json.dump(cai_piao_detailed_data, f)

    def getAllData(self, start_period = None):
        #如果之前爬取过数据，则更新数据，否则开始爬取所有数据
        if os.path.exists(self.cai_piao_detailed_file_path) and os.path.isfile(self.cai_piao_detailed_file_path):
            workread = xlrd.open_workbook(self.cai_piao_detailed_file_path)
            sheet = workread.sheet_by_index(0)  # 索引的方式，从0开始
            nrows = sheet.nrows  # 获取行总数
            last_row_data = sheet.row_values(nrows - 1)
            if last_row_data[0] == self.current_issue:#最后一行数据等于当前最新期数，不需要重新爬取
                cai_piao_ball_list_npy_file_path = os.path.join(self.file_save_dir, self.file_save_name + ".npy")
                cai_piao_ball_list_json_file_path = os.path.join(self.file_save_dir, self.file_save_name + ".json")
                if os.path.exists(cai_piao_ball_list_npy_file_path) and os.path.exists(cai_piao_ball_list_json_file_path):#文件存在，直接加载数据
                    self.all_cai_piao_ball_list = np.load(cai_piao_ball_list_npy_file_path)
                    print("从.npy文件中获取到{}条数据".format(len(self.all_cai_piao_ball_list)))
                    with open(cai_piao_ball_list_json_file_path, "r") as f:
                        self.all_cai_piao_detailed_data = json.load(f)
                else:#npy或者json数据不存在，需要重新读取excel文件获取信息并存储为npy文件
                    self.all_cai_piao_ball_list, self.all_cai_piao_detailed_data = self.getAllDataFromExcelFile()
                    # 保存数据成npy
                    np.save(cai_piao_ball_list_npy_file_path, self.all_cai_piao_ball_list)
                    # 保存数据成json格式
                    with open(cai_piao_ball_list_json_file_path, "w+") as f:
                        json.dump(self.all_cai_piao_detailed_data, f)
            else:#当前保存的数据不是最新的，需要更新
                start_period_tmp = eval(last_row_data[0]) + 1
                cai_piao_ball_list, cai_piao_detailed_data = self.crawlingData(start_period_tmp)

                self.all_cai_piao_ball_list, self.all_cai_piao_detailed_data = self.getAllDataFromExcelFile()
                for k, v in cai_piao_detailed_data.items():
                    self.all_cai_piao_detailed_data[k] = v
                for ball_list in cai_piao_ball_list:
                    self.all_cai_piao_ball_list.append(ball_list)
                self.saveData(self.all_cai_piao_ball_list, self.all_cai_piao_detailed_data)
        else:#工作目录下的data目录下没有保存有双色球历史详细信息的excel文件，开始爬取数据，进行保存
            self.all_cai_piao_ball_list, self.all_cai_piao_detailed_data = self.crawlingData(start_period)
            self.saveData(self.all_cai_piao_ball_list, self.all_cai_piao_detailed_data)

    def getAllDataFromExcelFile(self, file_path = None):
        '''
        :param file_path: 双色球数据excel文件路径
        :return: 文件中保存的双色球数据
        '''
        file_name = self.cai_piao_detailed_file_path if not file_path else file_path
        if not (os.path.exists(file_name) and os.path.isfile(file_name)):#读取的excel文件不存在
            print("{}不存在，无法读取，默认爬取所有数据并保存".format(file_name))
            self.all_cai_piao_ball_list, self.all_cai_piao_detailed_data = self.crawlingData()
            self.saveData(self.all_cai_piao_ball_list, self.all_cai_piao_detailed_data)
            return self.all_cai_piao_ball_list, self.all_cai_piao_detailed_data
        #开始读取数据
        all_cai_piao_ball_list = []
        all_cai_piao_detailed_data= OrderedDict()
        sheet = xlrd.open_workbook(file_name).sheet_by_index(0)  # 索引的方式，从0开始
        for i in range(1, sheet.nrows):
            one_row_data = sheet.row_values(i)
            all_cai_piao_detailed_data[one_row_data[0]] = one_row_data
            all_cai_piao_ball_list.append([int(i) for i in one_row_data[1:8]])
        print("从excel文件中读取到{}条数据".format(len(all_cai_piao_ball_list)))
        return all_cai_piao_ball_list, all_cai_piao_detailed_data

    #获取专家杀号数据，来源：https://zx.500.com/ssq/zhuanjiashahao.php
    def getLatestExpertKillNumberData(self):
        url = "https://zx.500.com/ssq/zhuanjiashahao.php"
        html = requests.get(url)
        html = bs4.BeautifulSoup(html.text, 'lxml')
        red_killed = html.find('tr', class_="nub-header2 nub-line nub-bg").find_all("span", class_ = "nub-ball nb1")
        red_killed = [red.get_text() for red in red_killed]
        blue_killed = html.find('tr', class_="nub-header2 nub-line nub-bg").find_all("span", class_="nub-ball nb2")
        blue_killed = [blue.get_text() for blue in blue_killed]
        return set(red_killed), set(blue_killed)

    #获取媒体预测数据，来源https://zx.500.com/ssq/mediayc.php
    def getMediaForecastsData(self):
        redBallForecastsData = [] #记录媒体预测中给出的红球预测数据列表
        blueBallForecastsData = []#记录媒体预测中给出的篮球预测数据列表
        url = "https://zx.500.com/ssq/mediayc.php"
        html = requests.get(url)
        html = bs4.BeautifulSoup(html.text, 'lxml')
        nums = html.findAll('tbody', id="n1_tbody")[0].findAll('tr', class_ = "")
        for i in nums:
            result = i.findAll("td", class_ = "num")
            redBallForecastsData.append(result[0].get_text())
            blueBallForecastsData.append(result[1].get_text())
        return redBallForecastsData, blueBallForecastsData

if __name__ == "__main__":
    shuangseqiu = shuangseqiu()
    #shuangseqiu.getAllData()
    #shuangseqiu.getAllDataFromExcelFile()
    print(shuangseqiu.getLatestExpertKillNumberData())
    print(shuangseqiu.getMediaForecastsData())