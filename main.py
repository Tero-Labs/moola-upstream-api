# Title:
# Function
# Author: Abdur Rahman

# ------ How to run in development ---------
#  uvicorn main:app --reload
# Then run in browser.
#			http://127.0.0.1:8000
# ------------------------------------------

# -------- Lib Import ----------------
from fastapi import FastAPI,Depends, Query,Request # Query = for length checking

# 30-04-2021 - Friday
from fastapi.middleware.cors import CORSMiddleware
import random 
import datetime

# 07-05-2021
# for validation from a list only
from typing import Optional
from enum import Enum
# 17-05-2021 - For UUID Validation in Key entry
from uuid import UUID
import uuid

# 20th May 2021 - Thrusday ---
# ---- DB
import databases
#from databases import Database
# for enviroment variable reading.
import os

# 4th June 2021 -- Friday ----
# For redirecting to to fee page ---
from fastapi.responses import RedirectResponse

# 10th July 2021 - Saturday
# Paginationation added to /activity

# 18th June 2021 -- Friday ----
# filtering irrelvant JSON elements in get/account/activity
#import json
# -------- Lib Import End --------------

__version__ = '0.1.71'

DATABASE_URL = os.environ.get('WORKING_DATABASE_URL','')
database = databases.Database(DATABASE_URL)
print('DATABASE_URL=',DATABASE_URL)

#---
# --- 9th June 2021 --
BASE_URL_GETFEE = os.environ.get('BASE_URL_GETFEE','')
BASE_URL_REALTIME_EXCHANGE_RATE = os.environ.get('BASE_URL_REALTIME_EXCHANGE_RATE','')
# --- 25TH jUNE 2021,Friday  --
BASE_URL_GETLIQUIDATION_PRICE = os.environ.get('BASE_URL_GETLIQUIDATION_PRICE','')

# --- 10th June 2021 --
ENABLE_ERROR_LOG_DUMP = os.environ.get('ENABLE_ERROR_LOG_DUMP','')

ENABLE_SUCCESS_LOG_DUMP = os.environ.get('ENABLE_SUCCESS_LOG_DUMP','')
#---

class CurrencyPermittedList(str, Enum):
	cUSD = "cUSD"
	Celo = "Celo"
	cEUR = "cEUR"

class CurrencyPermittedList_cUSD_cEUR(str, Enum):
	cUSD = "cUSD"
	cEUR = "cEUR"


class ActicityPermittedList(str, Enum):
	deposit = "deposit"
	withdraw = "withdraw"
	borrow = "borrow"
	repay = "repay"
	liquidate = "liquidate"


# --- Default Currency if no currency parameter is provided. ---
Default_Currency = 'Celo'
Secondary_Default_Currency ='cUSD'

Default_Activity='deposit'
# ---------------------------------------------------------------

# Added 30th April 2021,
app = FastAPI( title="Moola Middleware API", description="To Serve MobileApps & Dashboards",
    version=__version__)


# 30-04-2021 - Friday 
# --------- CORS -----------
origins = [
     "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#-------- End of CORS ---------


# ---------- 20th May Added ----------------------
@app.on_event("startup")
async def startup():
	await database.connect()


@app.on_event("shutdown")
async def shutdown():
	await database.disconnect()

# /get/info/about
@app.get("/get/info/about")
async def info_about():
	executionDateTime = datetime.datetime.now(datetime.timezone.utc).strftime("%m-%d-%Y %H:%M:%S.%f")

	return {'status':'OK',
			'dateTime':executionDateTime,
			'version':__version__
			}


# http://127.0.0.1:8000/get/getExchangeRates
# https://mooapi.herokuapp.com/get/getExchangeRates
@app.get("/get/getExchangeRates")
async def get_ExchangeRates(request: Request):

	start_perf_timer = datetime.datetime.utcnow()
	executionDateTime = start_perf_timer.timestamp()
	
	query = "select * from func_getexchange_rate();"

	try:
		result = await database.fetch_one(query=query)
		return_dic = {'status':'OK',
				'dateTime':executionDateTime,
				'USD': {'Celo':result['usd_to_celo'],'cEUR':result['usd_to_ceuro'],'cUSD': result['usd_to_cusd'] },
				'cUSD':{'Celo':result['cusd_to_celo'],'cEUR':result['cusd_to_ceuro'],'USD':result['cusd_to_usd']},
				'Celo':{'cUSD':result['celo_to_cusd'],'cEUR':result['celo_to_ceuro'],'USD':result['celo_to_usd']},
				'cEUR':{'cUSD':result['ceuro_to_cusd'],'Celo':result['ceuro_to_celo'],'USD':result['ceuro_to_usd']}
				}

	except Exception as e:
		is_error_detected=True
		return_dic = {'status':'ERROR',
				'detail':str(e)
				}
	else:
		is_error_detected=False

	# ------ 10th June 2021 Thrusday -----
	if (ENABLE_ERROR_LOG_DUMP=='1' and is_error_detected==True):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	if (ENABLE_SUCCESS_LOG_DUMP=='1' and is_error_detected==False):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	return return_dic


# http://127.0.0.1:8000/get/getReserveLiquidityRate?userPublicKey=796C27aB58C626075De11519dD4a49573f64967F
# https://mooapi.herokuapp.com/get/getReserveLiquidityRate?userPublicKey=796C27aB58C626075De11519dD4a49573f64967F
@app.get("/get/getReserveLiquidityRate")
async def get_ReserveLiquidityRate(request: Request,userPublicKey: str):

	start_perf_timer = datetime.datetime.utcnow()
	executionDateTime = start_perf_timer.timestamp()

	userPublicKey = userPublicKey.lower()

	query = "select * from  func_getreservedata_liquidityrate();"

	try:
		result = await database.fetch_all(query=query)
		return_dic = {'status':'OK',
				'dateTime':executionDateTime,
				'userPublicKey':userPublicKey,
				'data':result
				}

	except Exception as e:
		is_error_detected=True
		return_dic = {'status':'ERROR',
				'detail':str(e)
				}
	else:
		is_error_detected=False

	# ------ 10th June 2021 Thrusday -----
	if (ENABLE_ERROR_LOG_DUMP=='1' and is_error_detected==True):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	if (ENABLE_SUCCESS_LOG_DUMP=='1' and is_error_detected==False):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	return return_dic

# - http://127.0.0.1:8000/get/getNetWorth?userPublicKey=796C27aB58C626075De11519dD4a49573f64967F
# - https://mooapi.herokuapp.com/get/getNetWorth?userPublicKey=796C27aB58C626075De11519dD4a49573f64967F
@app.get("/get/getNetWorth")
async def get_NetWorth(request: Request,userPublicKey: str):

	start_perf_timer = datetime.datetime.utcnow()
	executionDateTime = start_perf_timer.timestamp()

	userPublicKey = userPublicKey.lower()

	query = "select * from func_getnet_worth(:address);"
	values = {"address":userPublicKey}

	try:
		result = await database.fetch_one(query=query,values=values)
		return_dic = {'status':'OK',
			'dateTime':executionDateTime,
			'userPublicKey':userPublicKey,
			'netWorth': result['networth']
			}

	except Exception as e:
		is_error_detected=True
		return_dic = {'status':'ERROR',
				'detail':str(e)
			}
	else:
		is_error_detected=False

	# ------ 10th June 2021 Thrusday -----
	if (ENABLE_ERROR_LOG_DUMP=='1' and is_error_detected==True):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	if (ENABLE_SUCCESS_LOG_DUMP=='1' and is_error_detected==False):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	return return_dic


# 15th June -
# - http://127.0.0.1:8000/get/getReserveData
# - https://mooapi.herokuapp.com/get/getReserveData
@app.get("/get/getReserveData")
async def get_ReserveData(request: Request):
	start_perf_timer = datetime.datetime.utcnow()
	executionDateTime = start_perf_timer.timestamp()

	query = "select * from func_getreserve_data();"

	try:
		result = await database.fetch_all(query=query)
		return_dic = {'status':'OK',
				'dateTime':executionDateTime,
				'data': result
				}

	except Exception as e:
		is_error_detected=True
		return_dic = {'status':'ERROR',
				'detail':str(e)
				}
	else:
		is_error_detected=False

	# ------ 10th June 2021 Thrusday -----
	if (ENABLE_ERROR_LOG_DUMP=='1' and is_error_detected==True):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	if (ENABLE_SUCCESS_LOG_DUMP=='1' and is_error_detected==False):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	return return_dic

 

# http://127.0.0.1:8000/get/getReserveData/activeUsers
# https://mooapi.herokuapp.com/get/getReserveData/activeUsers
@app.get("/get/getReserveData/activeUsers")
async def get_ReserveData_activeUsers(request: Request):
	start_perf_timer = datetime.datetime.utcnow()
	executionDateTime = start_perf_timer.timestamp()

	query = 'call stp_getreservedata_activeusers();'

	try:
		result = await database.fetch_one(query=query)
		return_dic = {'status':'OK',
				'dateTime':executionDateTime,
				'activeUsers': result['out_activeusers']
				}

	except Exception as e:
		is_error_detected=True
		return_dic = {'status':'ERROR',
					'detail':str(e)
					}
	else:
		is_error_detected=False

	# ------ 10th June 2021 Thrusday -----
	if (ENABLE_ERROR_LOG_DUMP=='1' and is_error_detected==True):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	if (ENABLE_SUCCESS_LOG_DUMP=='1' and is_error_detected==False):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	return return_dic

# http://127.0.0.1:8000/get/getReserveData/totalDeposited
# http://127.0.0.1:8000/get/getReserveData/totalDeposited?currency=cUSD
# https://mooapi.herokuapp.com/get/getReserveData/totalDeposited
@app.get("/get/getReserveData/totalDeposited")
async def get_ReserveData_TotalDeposited(request: Request,currency: Optional[CurrencyPermittedList] = Default_Currency):

	start_perf_timer = datetime.datetime.utcnow()
	executionDateTime = start_perf_timer.timestamp()
	
	query = "call stp_getreservedata_totaldeposited(:currency);"
	values = {"currency":currency}

	try:
		result = await database.fetch_one(query=query,values=values)
		return_dic = {'status':'OK',
					'dateTime':executionDateTime,
					'currency':currency,
					'totalDeposited': result['out_totaldeposited']}
	
	except Exception as e:
		is_error_detected=True
		return_dic = {'status':'ERROR',
					'detail':str(e)
					}
	else:
		is_error_detected=False

	# ------ 10th June 2021 Thrusday -----
	if (ENABLE_ERROR_LOG_DUMP=='1' and is_error_detected==True):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	if (ENABLE_SUCCESS_LOG_DUMP=='1' and is_error_detected==False):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	return return_dic


# http://127.0.0.1:8000/get/getReserveData/totalBorrowed
# https://mooapi.herokuapp.com/get/getReserveData/totalBorrowed
@app.get("/get/getReserveData/totalBorrowed")
async def get_ReserveData_TotalBorrowed(request: Request,currency: Optional[CurrencyPermittedList] = Default_Currency):

	start_perf_timer = datetime.datetime.utcnow()
	executionDateTime = start_perf_timer.timestamp()

	query = 'call stp_getreservedata_totalborrowed(:currency);'
	values = {"currency":currency}

	try:
		result = await database.fetch_one(query=query,values=values)
		return_dic= {'status':'OK',
					'dateTime':executionDateTime,
					'currency':currency,
					'totalBorrowed': result['out_totalborrowed']
					}

	except Exception as e:
		is_error_detected=True
		return_dic = {'status':'ERROR',
					'detail':str(e)
					}
	else:
		is_error_detected=False

	# ------ 10th June 2021 Thrusday -----
	if (ENABLE_ERROR_LOG_DUMP=='1' and is_error_detected==True):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	if (ENABLE_SUCCESS_LOG_DUMP=='1' and is_error_detected==False):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	return return_dic



# Newly created function /get/getReserveData/Total-ActiveUser-Deposited-Borrowed with Merger of - Total-ActiveUser,Deposited,Borrowed
#http://127.0.0.1:8000/get/getReserveData/total-activeUser-deposited-borrowed?currency=cEUR
#https://mooapi.herokuapp.com/get/getReserveData/total-activeUser-deposited-borrowed?currency=cEUR
@app.get("/get/getReserveData/total-activeUser-deposited-borrowed")
async def get_ReserveData_activeUser_deposited_borrowed(request: Request,currency: Optional[CurrencyPermittedList_cUSD_cEUR]):

	start_perf_timer = datetime.datetime.utcnow()
	executionDateTime = start_perf_timer.timestamp()

	query = "call stp_getreservedata_total_activeuser_deposited_borrowed(:currency);"
	values = {"currency":currency}

	try:
		result = await database.fetch_one(query=query,values=values)
		return_dic =  {'status':'OK',
				'dateTime':executionDateTime,
				'currency':currency,
				'activeUser': result['out_activeuser'] ,
				'totalDeposited' : result['out_deposited'] ,
				'totalBorrowed':  result['out_totalborrowed']
				}
	
	except Exception as e:
		is_error_detected=True
		return_dic = {'status':'ERROR',
					'detail':str(e)
					}
	else:
		is_error_detected=False

	# ------ 10th June 2021 Thrusday -----
	if (ENABLE_ERROR_LOG_DUMP=='1' and is_error_detected==True):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	if (ENABLE_SUCCESS_LOG_DUMP=='1' and is_error_detected==False):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	return return_dic

# http://127.0.0.1:8000/get/getUserAccountInfo/balance?userPublicKey=7d8f3b14b6f511eb85290242ac130003 -Error
# http://127.0.0.1:8000/get/getUserAccountInfo/balance?userPublicKey=313bc86D3D6e86ba164B2B451cB0D9CfA7943e5c
# http://127.0.0.1:8000/get/getUserAccountInfo/balance?userPublicKey=313bc86D3D6e86ba164B2B451cB0D9CfA7943e5c&currency=cUSD
# - https://mooapi.herokuapp.com/get/getUserAccountInfo/balance?userPublicKey=313bc86D3D6e86ba164B2B451cB0D9CfA7943e5c
# return - currency cUSD ??
@app.get("/get/getUserAccountInfo/balance")
async def get_UserAccountInfo_Balance(request: Request,userPublicKey: str, currency: Optional[CurrencyPermittedList_cUSD_cEUR] = Secondary_Default_Currency):
	start_perf_timer = datetime.datetime.utcnow()
	executionDateTime = start_perf_timer.timestamp()

	userPublicKey = userPublicKey.lower()

	query = "call stp_getuseraccountinfo_balance(:address,:currency);"
	values = {"address":userPublicKey,"currency":currency}
	
	try:
		result = await database.fetch_one(query=query,values=values)

		return_dic = {'status':'OK',
					'dateTime':executionDateTime,
					'userPublicKey':userPublicKey,
					'balancecUSD':{'currency':'cUSD','balance': result['out_balancecusd']},
					'balanceCelo':{'currency':'Celo','balance': result['out_balancecelo']},
					'balanceEURO':{'currency':'cEURO','balance': result['out_balanceceuro']},
					'balanceGrandTotal':{'currency':currency,'balance': result['out_balancegrandtotal']}
					}

	except Exception as e:
		is_error_detected=True
		return_dic = {'status':'ERROR',
					'detail':str(e)
					}
	else:
		is_error_detected=False

	# ------ 10th June 2021 Thrusday -----
	if (ENABLE_ERROR_LOG_DUMP=='1' and is_error_detected==True):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	if (ENABLE_SUCCESS_LOG_DUMP=='1' and is_error_detected==False):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	return return_dic

# http://127.0.0.1:8000/get/getUserAccountInfo/deposit?userPublicKey=A8433849d611F19235B6ef49515055f5cd1ee0Ab
# - https://mooapi.herokuapp.com/get/getUserAccountInfo/deposit?userPublicKey=A8433849d611F19235B6ef49515055f5cd1ee0Ab
@app.get("/get/getUserAccountInfo/deposit")
async def get_UserAccountInfo_Deposit(request: Request,userPublicKey: str):

	start_perf_timer = datetime.datetime.utcnow()
	executionDateTime = start_perf_timer.timestamp()

	userPublicKey = userPublicKey.lower()

	query = "select * from  func_getuseraccountinfo_deposit(:address);"
	values = {"address":userPublicKey}

	try:
		result = await database.fetch_all(query=query,values=values)
		return_dic = {'status':'OK',
				'dateTime':executionDateTime,
				'userPublicKey':userPublicKey,
				'data': result
				}

	except Exception as e:
		is_error_detected=True
		return_dic = {'status':'ERROR',
					'detail':str(e)
					}
	else:
		is_error_detected=False

	# ------ 10th June 2021 Thrusday -----
	if (ENABLE_ERROR_LOG_DUMP=='1' and is_error_detected==True):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	if (ENABLE_SUCCESS_LOG_DUMP=='1' and is_error_detected==False):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	return return_dic

# --- @@@@@@@@@@
# --- Taking too long because 56d0Ae52f33f7C2e38E92F6D20b8ccfD7Dc318Ce has 37k+ records --
#http://127.0.0.1:8000/get/getUserAccountInfo/activity?userPublicKey=56d0Ae52f33f7C2e38E92F6D20b8ccfD7Dc318Ce&currency=cUSD -- 37k+ recs
#http://127.0.0.1:8000/get/getUserAccountInfo/activity?userPublicKey=56d0Ae52f33f7C2e38E92F6D20b8ccfD7Dc318Ce -- 37k+ recs
#http://127.0.0.1:8000/get/getUserAccountInfo/activity?userPublicKey=A8433849d611F19235B6ef49515055f5cd1ee0Ab --- No record , Null
# - https://mooapi.herokuapp.com/get/getUserAccountInfo/activity?userPublicKey=A8433849d611F19235B6ef49515055f5cd1ee0Ab
# --- with pagination support
#https://mooapi.herokuapp.com/get/getUserAccountInfo/activity?userPublicKey=A8433849d611F19235B6ef49515055f5cd1ee0Ab&pageNo=0&pageSize=10
#http://127.0.0.0:8000/get/getUserAccountInfo/activity?userPublicKey=A8433849d611F19235B6ef49515055f5cd1ee0Ab&pageNo=0&pageSize=10
#
@app.get("/get/getUserAccountInfo/activity")
# async def get_UserAccountInfo_Activity(request: Request,userPublicKey: str,currency: Optional[CurrencyPermittedList] = Default_Currency):
async def get_UserAccountInfo_Activity(request: Request,userPublicKey: str,currency: Optional[CurrencyPermittedList] = Default_Currency,pageNo: int = 0,pageSize: int = 20):

	start_perf_timer = datetime.datetime.utcnow()
	executionDateTime = start_perf_timer.timestamp()

	userPublicKey = userPublicKey.lower()

	#query = "select * from func_getuseraccountinfo_activity(:address,:currency);"
	#values = {"address":userPublicKey,"currency":currency}
	query = "select * from func_getuseraccountinfo_activity_paginated(:address,:currency,:pageno,:pagesize);"
	values = {"address":userPublicKey,"currency":currency,"pageno":pageNo,"pagesize":pageSize}

	try:
		result = await database.fetch_all(query=query,values=values)

		#--------------------------------------------------------------
		# Post processing to remove certain redundant fields -- conditional field triming as per action.
		
		new_result = []
		new_row = {}
		
		for row in list(result):
			new_row = dict(row)
			# delete the un-necesary  keys -
			if dict(row).get('type') == 'deposit':
				del new_row['healthFactor']
				del new_row['liquidationPrice']
				del new_row['amountOfDebtRepaid']
				del new_row['amountOfDebtRepaidValue']
				del new_row['liquidatorClaimed']
				del new_row['liquidatorClaimedValue']
			
			if dict(row).get('type') == 'withdraw':
				del new_row['healthFactor']
				del new_row['liquidationPrice']
				del new_row['amountOfDebtRepaid']
				del new_row['amountOfDebtRepaidValue']
				del new_row['liquidatorClaimed']
				del new_row['liquidatorClaimedValue']
			
			if dict(row).get('type') == 'repay':
				del new_row['amountOfDebtRepaid']
				del new_row['amountOfDebtRepaidValue']
				del new_row['liquidatorClaimed']
				del new_row['liquidatorClaimedValue']
				
			if dict(row).get('type') == 'borrow':
				del new_row['amountOfDebtRepaid']
				del new_row['amountOfDebtRepaidValue']
				del new_row['liquidatorClaimed']
				del new_row['liquidatorClaimedValue']
				
			if dict(row).get('type') == 'liquidate':
				del new_row['amount']
				del new_row['source']
				del new_row['value'] # 8th July 
				
			new_result.append(new_row)
			
		return_dic = {'status':'OK',
				'dateTime':executionDateTime,
				'userPublicKey':userPublicKey,
				'currency' : currency,
				'pageNo' : pageNo,
				'pageSize' : pageSize,
				'activity':new_result}

	#----------------------------------------------------------------
	except Exception as e:
		is_error_detected=True
		return_dic = {'status':'ERROR',
					'detail':str(e)
					}
	else:
		is_error_detected=False

		
	# ------ 10th June 2021 Thrusday -----
	if (ENABLE_ERROR_LOG_DUMP=='1' and is_error_detected==True):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)
		
	if (ENABLE_SUCCESS_LOG_DUMP=='1' and is_error_detected==False):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)
		
	return return_dic


# ----- Creates an error if userPublic key is missing --- need error traping in all -Done
# http://127.0.0.1:8000/get/getUserAccountInfo/riskData?userPublicKey=84Cd08F5de891F82F6BD2938b06Ed84F6aBaB5e7 - OK
# - https://mooapi.herokuapp.com/get/getUserAccountInfo/riskData?userPublicKey=84Cd08F5de891F82F6BD2938b06Ed84F6aBaB5e7 
@app.get("/get/getUserAccountInfo/riskData")
#@app.get("/get/getUserAccountInfo/healthfactor")
async def get_UserAccountInfo_HealthFactor(request: Request,userPublicKey: str,currency: Optional[CurrencyPermittedList] = Default_Currency):

	start_perf_timer = datetime.datetime.utcnow()
	executionDateTime = start_perf_timer.timestamp()

	userPublicKey = userPublicKey.lower()

	query = "select * from func_getuseraccountinfo_healthfactor(:address,:currency);"
	values = {"address":userPublicKey,"currency":currency}

	try:
		result = await database.fetch_one(query=query,values=values)
		return_dic = {'status':'OK',
					'dateTime':executionDateTime,
					'userPublicKey':userPublicKey,
					'currency':currency,
					'healthfactor': result['healthfactor'],
					'liquidationPrice':result['liquidationprice'],
					'state': result['state']
					}

	except Exception as e:
		is_error_detected=True
		return_dic = {'status':'ERROR',
					'detail':str(e)
					}
	else:
		is_error_detected=False

	# ------ 10th June 2021 Thrusday -----
	if (ENABLE_ERROR_LOG_DUMP=='1' and is_error_detected==True):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	if (ENABLE_SUCCESS_LOG_DUMP=='1' and is_error_detected==False):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	return return_dic



# /get/getUserAccountInfo/borrow?userPublicKey=7d8f3b14b6f511eb85290242ac130003
# http://127.0.0.1:8000/get/getUserAccountInfo/borrow?userPublicKey=A8433849d611F19235B6ef49515055f5cd1ee0Ab
# - https://mooapi.herokuapp.com/get/getUserAccountInfo/borrow?userPublicKey=A8433849d611F19235B6ef49515055f5cd1ee0Ab
@app.get("/get/getUserAccountInfo/borrow")
async def get_UserAccountInfo_Borrow(request: Request,userPublicKey: str):

	start_perf_timer = datetime.datetime.utcnow()
	executionDateTime = start_perf_timer.timestamp()

	userPublicKey = userPublicKey.lower()

	query = "select * from  func_getuseraccountinfo_borrow(:address);"
	values = {"address":userPublicKey}

	try:
		result = await database.fetch_all(query=query,values=values)

		return_dic = {'status':'OK',
				'dateTime':executionDateTime,
				'userPublicKey':userPublicKey,
				'data': result
				}

	except Exception as e:
		is_error_detected=True
		return_dic = {'status':'ERROR',
				'detail':str(e)
				}
	else:
		is_error_detected=False

	# ------ 10th June 2021 Thrusday -----
	if (ENABLE_ERROR_LOG_DUMP=='1' and is_error_detected==True):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	if (ENABLE_SUCCESS_LOG_DUMP=='1' and is_error_detected==False):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	return return_dic


# 17th May 2021 - 
#http://127.0.0.1:8000/get/getUserAccountInfo/debt?userPublicKey=313bc86D3D6e86ba164B2B451cB0D9CfA7943e5c&currency=Celo
# - https://mooapi.herokuapp.com/get/getUserAccountInfo/debt?userPublicKey=313bc86D3D6e86ba164B2B451cB0D9CfA7943e5c&currency=Celo
@app.get("/get/getUserAccountInfo/debt")
async def get_UserAccountInfo_Debt(request: Request,userPublicKey: str,currency: Optional[CurrencyPermittedList] = Default_Currency):

	start_perf_timer = datetime.datetime.utcnow()
	executionDateTime = start_perf_timer.timestamp()

	userPublicKey = userPublicKey.lower()

	query = "call stp_getuseraccountinfo_debt(:address,:currency);"
	values = {"address":userPublicKey,"currency":currency}

	try:
		result = await database.fetch_one(query=query,values=values)
		return_dic ={'status':'OK',
				'dateTime':executionDateTime,
				'userPublicKey':userPublicKey,
				'currency': currency,
				'debt': result['out_debt'] #UserAccountInfo_debt
				}

	except Exception as e:
		is_error_detected=True
		return_dic = {'status':'ERROR',
					'detail':str(e)
					}
	else:
		is_error_detected=False

	# ------ 10th June 2021 Thrusday -----
	if (ENABLE_ERROR_LOG_DUMP=='1' and is_error_detected==True):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	if (ENABLE_SUCCESS_LOG_DUMP=='1' and is_error_detected==False):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	return return_dic




# 17th May 2021 - 
# ---- @ ERROR - needs fixing --- Fixed - Had a duplicated stored procedure 
# http://127.0.0.1:8000/get/getUserAccountInfo/max?userPublicKey=56d0Ae52f33f7C2e38E92F6D20b8ccfD7Dc318Ce&activityType=deposit
# - https://mooapi.herokuapp.com/get/getUserAccountInfo/max?userPublicKey=56d0Ae52f33f7C2e38E92F6D20b8ccfD7Dc318Ce&activityType=deposit
@app.get("/get/getUserAccountInfo/max")
async def get_UserAccountInfo_Max(request: Request,userPublicKey: str, activityType: Optional[ActicityPermittedList] ,currency: Optional[CurrencyPermittedList] = Default_Currency):

	start_perf_timer = datetime.datetime.utcnow()
	executionDateTime = start_perf_timer.timestamp()

	userPublicKey = userPublicKey.lower()

	query = "call stp_getuseraccountinfo_max(:address,:activity_type,:currency);"
	values = {"address":userPublicKey,"activity_type":activityType,"currency":currency}

	try:
		result = await database.fetch_one(query=query,values=values)
		return_dic = {'status':'OK',
				'dateTime':executionDateTime,
				'userPublicKey':userPublicKey,
				'currency': currency,
				'activityType' : activityType,
				'MaxAmount': result['out_maxamount']
				}

	except Exception as e:
		is_error_detected=True
		return_dic = {'status':'ERROR',
					'detail':str(e)
					}
	else:
		is_error_detected=False

	# ------ 10th June 2021 Thrusday -----
	if (ENABLE_ERROR_LOG_DUMP=='1' and is_error_detected==True):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	if (ENABLE_SUCCESS_LOG_DUMP=='1' and is_error_detected==False):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	return return_dic 



# 17th May 2021 -  
# 24th June 2021 - 
# http://127.0.0.1:8000/get/getUserAccountInfo/status?userPublicKey=7d8f3b14b6f511eb85290242ac130003 -> NULL
# http://127.0.0.1:8000/get/getUserAccountInfo/status?userPublicKey=313bc86D3D6e86ba164B2B451cB0D9CfA7943e5c
# - https://mooapi.herokuapp.com/get/getUserAccountInfo/status?userPublicKey=313bc86D3D6e86ba164B2B451cB0D9CfA7943e5c
# - http://127.0.0.1:8000/get/getUserAccountInfo/status?userPublicKey=a0bda5d71291f391a71bf2d695b4ea620ac7b0e6
# - https://mooapi.herokuapp.com/get/getUserAccountInfo/status?userPublicKey=a0bda5d71291f391a71bf2d695b4ea620ac7b0e6
@app.get("/get/getUserAccountInfo/status")
async def get_UserAccountInfo_Status(request: Request,userPublicKey: str,currency: Optional[CurrencyPermittedList] = Default_Currency):

	start_perf_timer = datetime.datetime.utcnow()
	executionDateTime = start_perf_timer.timestamp()

	userPublicKey = userPublicKey.lower()

	query = "select * from func_getuseraccountinfo_status(:address,:currency);"
	values = {"address":userPublicKey,"currency":currency}

	try:
		result = await database.fetch_one(query=query,values=values)

		return_dic = {'status':'OK',
						'dateTime':executionDateTime,
						'userPublicKey':userPublicKey,
						'healthFactor': result['healthFactor'], 
						'liquidationPrice': result['liquidationPrice'], 
						'state': result['state'],
						'currentLTV': result['currentLTV'],
						'maximumLTV': result['maximumLTV'],
						'liquidationThreshold': result['liquidationThreshold'],
						'interestRates': 
						[
						{
						'currency':'Celo',
						'interestRate': result['CeloInterestRate'],
						'totalCollateral': result['CelototalCollateral'],
						'totalDebt': result['CelototalDebt'],
						'totalFee' : result['totalFeeCelo']
						},
						{
						'currency':'cEUR',
						'interestRate': result['cEURInterestRate'],
						'totalCollateral': result['cEURtotalCollateral'],
						'totalDebt': result['cEURtotalDebt'],
						'totalFee' : result['totalFeecEUR']
						},
						{
						'currency':'cUSD',
						'interestRate': result['cUSDInterestRate'],
						'totalCollateral': result['cUSDtotalCollateral'],
						'totalDebt': result['cUSDtotalDebt'],
						'totalFee' : result['totalFeecUSD']
						}
						],
						
						
						'currentPrice' : result['currentPrice'], #---- ???
						'liquidationPenalty': result['liquidationPenalty'],
						'remainingDebt': result['remainingDebt'],
					}
	except Exception as e:
		is_error_detected=True
		return_dic = {'status':'ERROR',
					'detail':str(e)
					}
	else:
		is_error_detected=False

	# ------ 10th June 2021 Thrusday -----
	if (ENABLE_ERROR_LOG_DUMP=='1' and is_error_detected==True):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	if (ENABLE_SUCCESS_LOG_DUMP=='1' and is_error_detected==False):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	return return_dic

# -- redirection 
# - https://mooapi.herokuapp.com/get/getFee?userPublicKey=7d8f3b14b6f511eb85290242ac130003&activityType=borrow&amount=40&currency=cEUR
# - https://mooapi.herokuapp.com/get/getFee?userPublicKey=7d8f3b14b6f511eb85290242ac130003&activityType=borrow&amount=40&currency=cEUR
# - http://127.0.0.1:8000/get/getFee?userPublicKey=7d8f3b14b6f511eb85290242ac130003&activityType=borrow&amount=40&currency=cEUR
@app.get("/get/getFee")
async def get_getFee(request: Request,userPublicKey: str, activityType: Optional[ActicityPermittedList] , amount: float,currency: Optional[CurrencyPermittedList] = Default_Currency):
# This part can be improved - via saving the return msg ---
# url saved , not the return_msg or error state 
	start_perf_timer = datetime.datetime.utcnow()
	executionDateTime = start_perf_timer.timestamp()

	userPublicKey = userPublicKey.lower()

	try:
		call_url = BASE_URL_GETFEE + f"?userPublicKey={userPublicKey}&activityType={activityType}&amount={amount}&currency={currency}"

	except Exception as e:
		is_error_detected=True

	else:
		is_error_detected=False


	# ------ 26th June 2021 Saturday -----
	return_dic = ''
	if (ENABLE_ERROR_LOG_DUMP=='1' and is_error_detected==True):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	if (ENABLE_SUCCESS_LOG_DUMP=='1' and is_error_detected==False):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)


	return RedirectResponse(call_url)




# --- 25th June 2021,Friday 
# - https://mooapi.herokuapp.com/get/getLiquidationPrice?userPublicKey=7d8f3b14b6f511eb85290242ac130003
# https://mooapi.herokuapp.com/get/getLiquidationPrice?userPublicKey=7d8f3b14b6f511eb85290242ac130003
# http://127.0.0.1:8000/get/getLiquidationPrice?userPublicKey=7d8f3b14b6f511eb85290242ac130003
@app.get("/get/getLiquidationPrice")
async def get_getLiquidationPrice(request: Request,userPublicKey: str):
# This part can be improved - via saving the return msg , url etc
	start_perf_timer = datetime.datetime.utcnow()
	executionDateTime = start_perf_timer.timestamp()

	userPublicKey = userPublicKey.lower()

	try:
		call_url = BASE_URL_GETLIQUIDATION_PRICE + f"?userPublicKey={userPublicKey}"

	except Exception as e:
		is_error_detected=True

	else:
		is_error_detected=False

	# ------ 26th June 2021 Saturday -----
	return_dic=''
	if (ENABLE_ERROR_LOG_DUMP=='1' and is_error_detected==True):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)

	if (ENABLE_SUCCESS_LOG_DUMP=='1' and is_error_detected==False):
		await dump_upstream_access_log(start_perf_timer,request.url.path,str(request.url),str(request.query_params),str(return_dic)[:2048],is_error_detected,request.client.host)


	return RedirectResponse(call_url)



# --- 10th June 2021 - Thrusday - 
async def dump_upstream_access_log(start_perf_timer,base_url,in_string,in_parameter,out_string,is_error_detected,ip):

	time_delta =  (datetime.datetime.utcnow() - start_perf_timer).microseconds

	insert_query = "INSERT INTO tbl_upstream_access_log(base_url,in_string,in_parameter,out_string,elapsed_time_performance_metrics, is_error,ip) VALUES (:base_url,:in_string,:in_parameter, :out_string, :elapsed_time_performance_metrics, :is_error,:ip)"
	insert_values = {'base_url': base_url, 'in_string':in_string,'in_parameter': in_parameter,'out_string': out_string,'ip':ip,'elapsed_time_performance_metrics': time_delta, 'is_error': is_error_detected ,'ip': ip}

	try:
		await database.execute(query=insert_query, values=insert_values)

# ----- Save to db to be implemented ---???
	except Exception as e:
		print('ERROR',str(e))
