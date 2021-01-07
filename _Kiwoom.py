import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from _algos import *
import time
import pandas as pd
import sqlite3

TR_REQ_TIME_INTERVAL = 0.2


class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()

#### 이벤트 처리 ##########################################################
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.ocx.OnEventConnect.connect(self._handler_login)
        self.ocx.OnReceiveTrData.connect(self._handler_tr_data)
        self.ocx.OnReceiveRealData.connect(self._handler_real_data)
        self.ocx.OnReceiveChejanData.connect(self._handler_chejan_data)
##########################################################################


#### 변수 #################################################################
        self.price = {}
        self.rate = {}
        self.amount = {}
        self.bid_price = {}  # 매수호가
        self.ask_price = {}  # 매도호가
##########################################################################


#### 로그인 처리 #########################################################
        self.login_event_loop = QEventLoop()
        self.CommConnect()          # 로그인이 될 때까지 대기
        self.account = self.GetLoginInfo("ACCNO").split(';')[0]
##########################################################################


#### 실시간 등록 #########################################################
        # self.subscribe_market_time('1')
        self.subscribe_stock_conclusion('2000', Algos.one_codes)
##########################################################################


#--------------------------------------------------------------------------------------------------------------
#함수


#### 로그인 ##############################################################
    def CommConnect(self):
        self.ocx.dynamicCall("CommConnect()")
        self.login_event_loop.exec()

    def _handler_login(self, err_code):
        if err_code == 0:
            pass
        self.login_event_loop.exit()

    def GetLoginInfo(self, tag):
        data = self.ocx.dynamicCall("GetLoginInfo(QString)", tag)
        return data
##########################################################################


#### 예수금, 종목수량 #####################################################

    def get_amount(self):
        # TR 요청
        self.request_opw00001()
        self.request_opw00004()

    def request_opw00001(self):
        self.SetInputValue("계좌번호", self.account)
        self.SetInputValue("비밀번호", "")
        self.SetInputValue("비밀번호입력매체구분", "00")
        self.SetInputValue("조회구분", 2)
        self.CommRqData("예수금조회", "opw00001", 0, "9001")
        self.login_event_loop.exec()

    def request_opw00004(self):
        self.SetInputValue("계좌번호", self.account)
        self.SetInputValue("비밀번호", "")
        self.SetInputValue("상장폐지조회구분", 0)
        self.SetInputValue("비밀번호입력매체구분", "00")
        self.CommRqData("계좌평가현황", "opw00004", 0, "9002")
        self.login_event_loop.exec()

    def GetRepeatCnt(self, trcode, rqname):
        ret = self.ocx.dynamicCall(
            "GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret

    def _handler_tr_data(self, screen_no, rqname, trcode, record, next):
        if rqname == "예수금조회":
            주문가능금액 = self.GetCommData(trcode, rqname, 0, "주문가능금액")
            self.cash = int(주문가능금액)
            self.login_event_loop.exit()

        elif rqname == "계좌평가현황":
            rows = self.GetRepeatCnt(trcode, rqname)
            for i in range(rows):
                code = self.GetCommData(trcode, rqname, i, "종목명")
                amount_ = self.GetCommData(trcode, rqname, i, "보유수량")
                self.amount[code] = int(amount_)
            self.login_event_loop.exit()

##########################################################################


#### 실시간 ###############################################################

    def subscribe_stock_conclusion(self, screen_no, codes):
        self.SetRealReg(screen_no, codes, "20", 0)

    def _handler_real_data(self, code, realtype, realdata):
        if realtype == '주식체결':
            temp_ask_price = self.ocx.dynamicCall(
                "GetCommRealData(QString,int)", code, 27)  # 매도호가
            temp_bid_price = self.ocx.dynamicCall(
                "GetCommRealData(QString,int)", code, 28)  # 매수호가
            temp_price = self.ocx.dynamicCall(
                "GetCommRealData(QString,int)", code, 10)
            temp_rate = self.ocx.dynamicCall(
                "GetCommRealData(QString,int)", code, 12)
            self.price[code] = int(temp_price)
            self.rate[code] = float(temp_rate)
            self.bid_price[code] = int(temp_bid_price)
            self.ask_price[code] = int(temp_ask_price)

    def get_chejan_data(self, fid):
        ret = self.ocx.dynamicCall("GetChejanData(int)", fid)
        ret_ = ret.rstrip()
        return ret_
        self.login_event_loop.exec()

    def _receive_chejan_data(self, gubun, item_cnt, fid_list):
        print('[', self.get_chejan_data(908), ']', self.get_chejan_data(302), ':', self.get_chejan_data(905),
              self.get_chejan_data(900), '주', self.get_chejan_data(10), '원')
        self.login_event_loop.exit()

#### 메소드 ###############################################################

    def SetInputValue(self, id, value):
        self.ocx.dynamicCall("SetInputValue(QString, QString)", id, value)

    def CommRqData(self, rqname, trcode, next, screen_no):
        self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)",
                             rqname, trcode, next, screen_no)

    def GetCommData(self, trcode, rqname, index, item):
        data = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)",
                                    trcode, rqname, index, item)
        return data.strip()

    def SetRealReg(self, screen_no, code_list, fid_list, real_type):
        self.ocx.dynamicCall("SetRealReg(QString, QString, QString, QString)",
                             screen_no, code_list, fid_list, real_type)

    def GetCommRealData(self, code, fid):
        data = self.ocx.dynamicCall("GetCommRealData(QString, int)", code, fid)
        return data

    def DisConnectRealData(self, screen_no):
        self.ocx.dynamicCall("DisConnectRealData(QString)", screen_no)

    def SendOrder(self, rqname, screen, accno, order_type, code, quantity, price, hoga, order_no):
        self.ocx.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                             [rqname, screen, accno, order_type, code, quantity, price, hoga, order_no])

    def GetChejanData(self, fid):
        data = self.ocx.dynamicCall("GetChejanData(int)", fid)
        return data

##########################################################################