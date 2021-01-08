import pandas as pd
import numpy as np
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
from Kiwoom import *
import time
from datetime import datetime,timedelta
now = datetime.now()

form_class = uic.loadUiType("_pytrader.ui")[0]

class Algos(QMainWindow, form_class):

    def __init__(self):
        
        super().__init__()
        self.setupUi(self)
        self.trade_stocks_done = False                
        self.kiwoom = Kiwoom()

########계좌번호######## 
        self.account = 5624118510
#############################################################


########변수########
        self.kodex_bid_price = [] ; self.tiger_bid_price = [] 
        self.spread = [] ; self.spread_inv = []
#############################################################
        

########종목코드 실시간 등록########
        self.codes = '069500;102110;114800'
        self.kiwoom.subscribe_stock_conclusion('2000', self.codes)
##############################################################


############종목수량, 매수/매도호가 ##########################
    def get_data(self):
        self.kiwoom.get_amount()
        amount = self.kiwoom.amount 
        bid_price = self.kiwoom.bid_price
        ask_price = self.kiwoom.ask_price
        return amount , bid_price, ask_price
###############################################################################################



########매수/매도 메소드###########################################################################################
 # self.kiwoom.send_order("send_order_req", "0101", account, order_type, code, num, price, hoga, "")    00:지정가, 03 :시장가

    def buy_kodex(self,price,leverage):
        self.kiwoom.SendOrder("send_order_req", "0101", self.account, 1, 364690, leverage, price, '03', "")   
        
    def sell_kodex(self,price,leverage):
        self.kiwoom.SendOrder("send_order_req", "0101", self.account, 2, 364690, leverage, price, '03', "")
        
    def buy_tiger(self,price,leverage):
        self.kiwoom.SendOrder("send_order_req", "0101", self.account, 1, 365040, leverage, price, '03', "")
        
    def sell_tiger(self,price,leverage):
        self.kiwoom.SendOrder("send_order_req", "0101", self.account, 2, 365040, leverage, price, '03', "")
        
    def buy_kodex200(self,price,leverage):
        self.kiwoom.SendOrder("send_order_req", "0101", self.account, 1, '069500', leverage, price, '03', "")
        
    def sell_kodex200(self,price,leverage):
        self.kiwoom.SendOrder("send_order_req", "0101", self.account, 2, '069500', leverage, price, '03', "")

    def buy_tiger200(self,price,leverage):
        self.kiwoom.SendOrder("send_order_req", "0101", self.account, 1, '102110', leverage, price, '03', "")
        
    def sell_tiger200(self,price,leverage):
        self.kiwoom.SendOrder("send_order_req", "0101", self.account, 2, '102110', leverage, price, '03', "")
        
    def buy_kodex_inv(self,price,leverage):
        self.kiwoom.SendOrder("send_order_req", "0101", self.account, 1, 114800, leverage, price, '03', "")
        
    def sell_kodex_inv(self,price,leverage):
        self.kiwoom.SendOrder("send_order_req", "0101", self.account, 2, 114800, leverage, price, '03', "")

###################################################################################################################



### trading algorithms ###
################################################### Algo_1##########################################################
    def one(self,amount,bid_price,ask_price):
        print('[algo_one]-----------------------------------------------------------------------------')
        
        ### 알고리즘 요약
        # 1. kodex200과 tiger200의 매도가격 스프레드가 지난 60개의 데이터 이동평균과 달라지는 경우,
        # 2. 매수호가,매도호가 스프레드를 고려하여 threshold에 반영.
        # 3. 숏 또는 롱 포지션 취한 후, 
        # 4. 반대 포지션으로 청산


        ###초기 설정###
        leverage = 1       
        init_count = 30
        bid_ask_spread = 10

        kodex200 = 'KODEX 200'   
        tiger200 = 'TIGER 200'     
        

        ######스프레드 계산######
        if len(bid_price)!=3:
            pass
        else:    
            self.spread.append(bid_price['069500']-bid_price['102110'])  
            if len(self.spread) <= 60:
                print(len(self.spread),'/60')


        ######이동평균 계산 후 트레이딩 시작######
        if len(self.spread)>=60:
 
            spread = pd.Series(self.spread)

            threshold = spread.rolling(window=60,center=False).mean()

            print('spread :',round(spread.iloc[-1],4), 'threshold :',round((threshold.iloc[-1]+bid_ask_spread),4))

            if spread.iloc[-1] > (threshold.iloc[-1]+bid_ask_spread) and amount[kodex200] >=1:
                print('short position')
                self.sell_kodex200(0,leverage)
                self.buy_tiger200(0,leverage)

            elif spread.iloc[-1] < - (threshold.iloc[-1]+bid_ask_spread) and amount[tiger200]>=1 :
                print('long position')
                self.buy_kodex200(0,leverage)
                self.sell_tiger200(0,leverage)

            elif abs(spread.iloc[-1]) <= threshold.iloc[-1] :
                print('close position')                    
                if amount[kodex200] < init_count :
                    self.buy_kodex200(0,init_count-amount[kodex200])
                    self.sell_tiger200(0,init_count-amount[kodex200])
                elif amount[kodex200] > init_count :
                    self.sell_kodex200(0,amount[kodex200]-init_count)
                    self.buy_tiger200(0,amount[kodex200]-init_count)


################################################### Algo_2##########################################################
    def two(self,amount,bid_price,ask_price):
        print('[algo_two]-----------------------------------------------------------------------------')   
        
        ### 알고리즘 요약
        # 1. kodex200과 kodex_inv의 매도가격 스프레드가 지난 60개의 데이터 이동평균과 달라지는 경우,
        # 2. 매수호가,매도호가 스프레드를 고려하여 threshold에 반영.
        # 3. 숏 또는 롱 포지션 취한 후, 
        # 4. 반대 포지션으로 청산
        
        ###초기 설정###
        leverage = 1
        
        init_count = 30

        kodex200 = 'KODEX 200'
        kodex_inv = 'KODEX 인버스'      
        bid_ask_spread = 10

        ###스프레드 계산###
        if len(bid_price)!=3:
            pass
        else:    
            self.spread_inv.append(bid_price['069500']-bid_price['114800']) 
            
            if len(self.spread_inv) <= 60:
                print(len(self.spread_inv),'/60')


        ###이동평균 계산 후 트레이딩 시작###
        if len(self.spread_inv)>=60:
 
            spread_inv = pd.Series(self.spread_inv)

            threshold = spread_inv.rolling(window=60,center=False).mean()

            print('spread_inv :',round(spread_inv.iloc[-1],4), 'threshold :',round((threshold.iloc[-1]+10),4))

            if spread_inv.iloc[-1] > (threshold.iloc[-1]+10) and amount[kodex200] >=1:
                print('short position')
                self.sell_kodex200(0,leverage)
                self.buy_inverse(0,leverage)

            elif spread_inv.iloc[-1] < - (threshold.iloc[-1]+10) and amount[kodex_inv]>=1 :
                print('long position')
                self.buy_kodex200(0,leverage)
                self.sell_inverse(0,leverage)

            elif abs(spread_inv.iloc[-1]) < threshold.iloc[-1] :
                print('close position')                    
                if amount[kodex200] < init_count :
                    self.buy_kodex200(0,init_count-amount[kodex200])
                    self.sell_inverse(0,init_count-amount[kodex200])
                elif amount[kodex200] > init_count :
                    self.sell_kodex200(0,amount[kodex200]-init_count)
                    self.buy_inverse(0,amount[kodex200]-init_count)
        else:
            pass


        print('------------------------------------------------------------------------------')


################################################### Algo_3##########################################################
    def three(self):
    
        leverage = 1
        
        kospi = 'KODEX 200'
        kodex = 'KODEX 혁신기술테마액티브'
        tiger = 'TIGER AI코리아그로스액티브'       
        
        self.kiwoom.get_amount()
        amount = self.kiwoom.amount

        profit = self.kiwoom.profit
                    
        bid_price = self.kiwoom.bid_price
        ask_price = self.kiwoom.ask_price
        print(ask_price)
        print(bid_price)
        
        if len(price)!=3:
            pass
        else:
            self.kodex_ask_price.append(ask_price['364690']) ; self.tiger_ask_price.append(ask_price['365040'])
            self.kodex_bid_price.append(bid_price['364690']) ; self.tiger_bid_price.append(bid_price['365040'])
      
            self.short_spread.append()
 
            kodex_profit = profit[kodex]          ; tiger_profit = profit[tiger]

            
            if len(self.kodex_ask_price) <= 60:
                print(len(self.kodex_ask_price),'/60')


        if len(self.kodex_ask_price)>=60:
 
            spread = pd.Series(self.spread)

            threshold = spread.rolling(window=60,center=False).mean()

            print('spread :',round(spread.iloc[-1],4), 'threshold :',round(threshold.iloc[-1],4))

            if spread.iloc[-1] > threshold.iloc[-1] and amount[kodex] >=1:
                print('short position')
                self.sell_kodex(0,leverage)
                self.buy_tiger(0,leverage)

            elif spread.iloc[-1] < - threshold.iloc[-1] and amount[tiger]>=1 :
                print('long position')
                self.buy_kodex(0,leverage)
                self.sell_tiger(0,leverage)

            elif abs(spread.iloc[-1]) < threshold.iloc[-1] :
                print('close position')                    
                if amount[kodex] < init_count and profit[kodex] > kodex_ask_price and profit[tiger] > tiger_bid_price:
                    self.buy_kodex(0,init_count-amount[kodex])
                    self.sell_tiger(0,init_count-amount[kodex])
                elif amount[kodex] > init_count and profit[kodex] > kodex_bid_price and profit[tiger] > tiger_ask_price:
                    self.sell_kodex(0,amount[kodex]-init_count)
                    self.buy_tiger(0,amount[kodex]-init_count)
        else:
            pass

        self.kiwoom.get_amount()
        amount = self.kiwoom.amount


        print('------------------------------------------------------------------------------')


################################################### Algo_4##########################################################
    def four(self):
    
        leverage = 1

        init_count = 60  #초기 종목 개수
        
        kospi = 'KODEX 200'
        kodex = 'KODEX 혁신기술테마액티브'
        tiger = 'TIGER AI코리아그로스액티브'       
        
        self.kiwoom.get_amount()
        amount = self.kiwoom.amount

        profit = self.kiwoom.profit
                    
        price = self.kiwoom.price
        ret = self.kiwoom.rate
        bid_price = self.kiwoom.bid_price
        ask_price = self.kiwoom.ask_price
        print(price)
        print(ret)
        
        if len(price)!=3:
            pass
        else:
            kodex_bid_price = bid_price['364690'] ; tiger_bid_price = bid_price['365040'] 
            kodex_ask_price = ask_price['364690'] ; tiger_ask_price = ask_price['365040']       
            kodex_profit = profit[kodex]          ; tiger_profit = profit[tiger]

            kodex_mid_price = (kodex_bid_price+kodex_ask_price)/2
            tiger_mid_price = (tiger_bid_price+tiger_ask_price)/2
            
            self.spread.append( kodex_mid_price - tiger_mid_price ) 
            
            if len(self.spread) <= 60:
                print(len(self.spread),'/60')


        if len(self.spread)>=60:
 
            spread = pd.Series(self.spread)

            threshold = spread.rolling(window=60,center=False).mean()

            print('spread :',round(spread.iloc[-1],4), 'threshold :',round(threshold.iloc[-1],4))

            if spread.iloc[-1] > threshold.iloc[-1] and amount[kodex] >=1:
                print('short position')
                self.sell_kodex(0,leverage)
                self.buy_tiger(0,leverage)

            elif spread.iloc[-1] < - threshold.iloc[-1] and amount[tiger]>=1 :
                print('long position')
                self.buy_kodex(0,leverage)
                self.sell_tiger(0,leverage)

            elif abs(spread.iloc[-1]) < threshold.iloc[-1] :
                print('close position')                    
                if amount[kodex] < init_count and profit[kodex] > kodex_ask_price and profit[tiger] > tiger_bid_price:
                    self.buy_kodex(0,init_count-amount[kodex])
                    self.sell_tiger(0,init_count-amount[kodex])
                elif amount[kodex] > init_count and profit[kodex] > kodex_bid_price and profit[tiger] > tiger_ask_price:
                    self.sell_kodex(0,amount[kodex]-init_count)
                    self.buy_tiger(0,amount[kodex]-init_count)
        else:
            pass

        self.kiwoom.get_amount()
        amount = self.kiwoom.amount


        print('------------------------------------------------------------------------------')