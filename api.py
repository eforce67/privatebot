import math, requests, numpy as np, datetime
import private_main

from earnapp import earnapp
from pyHoneygain import HoneyGain, NotLoggedInError as honeygain_login
from pyIPRoyalPawns import IPRoyalPawns, NotLoggedInError as iproyal_login

"""API.py created by @Neonshark#2321.
This script is made to handle requests and anything related to web."""

def checkProxy(proxy):
    if proxy is None or len(proxy) <= 0 or proxy == "None":
        return None
    else:
        return proxy # format ip:port:username:password

def convert_size(size_bytes): # does math on finding byte size, i got this from stackoverflow L
   if size_bytes <= 0:
       return "0/B"
   
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return f"{s}/{size_name[i]}"

class runEarnapp:
    def __init__(self, oath_token : str, proxy):
        self.user = earnapp.User()
        
        if checkProxy(proxy=proxy) is not None:
            self.user.setProxy(
                proxy={
                    "http": f"socks5://{proxy[2]}:{proxy[3]}@{proxy[0]}:{proxy[1]}", 
                    "https" : f"socks5://{proxy[2]}:{proxy[3]}@{proxy[0]}:{proxy[1]}"
                    }) # format ip:port:username:password
        try:
            self.user.login(token=oath_token, method="google")
        except earnapp.IncorrectTokenException:
            print("[Earnapp] Incorrect token")
            raise SystemExit
    
    def checkEarning(self):
        online_device = len(self.user.onlineStatus()) # gets max online device | not good for 1k devices
        # {"multiplier": 1, "multiplier_icon": "", "multiplier_hint": "", "redeem_details": null, "balance": 0.06, "earnings_total": 141.12, "ref_bonuses": 0, "ref_bonuses_total": 1.67, "promo_bonuses": 0, "promo_bonuses_total": 0, "ref_bvpn": 0, "ref_bvpn_total": 0, "ref_hola_browser": 0, "ref_hola_browser_total": 0, "referral_part": "10%"}
        balance = self.user.money() # gets balance status
        email = self.user.userData()["email"] # gets earnapp email
        
        return {"online": online_device, "money": balance, "contact": email}

class runIProyal:
    def __init__(self, jwt_token : str, proxy):
        self.user = IPRoyalPawns()
        
        if checkProxy(proxy=proxy) is not None:
            self.user.set_socks5_proxy(proxy) # format ip:port:username:password
        self.user.set_jwt_token(jwt=jwt_token) # set the token
    
    def checkEarning(self):
        try:
            balance = self.user.balance()["json"] # gets balance info
            pages = self.user.devices()["json"]["meta"]["last_page"] # gets the last page of device list
            email = self.user.me()["json"]["email"] # gets the email of account
            
            active_devices = 0
            count_country = []
            
            for page in range(1, pages):
                devices = self.user.devices(page=page)["json"]["data"]
                
                for line in range(len(devices)):
                    count_country.append([devices[line]["last_peer_country"]])
                    active_devices += devices[line]["active_peers_count"] # sometimes peers are stacked together, so we have to count this
            
            total_device_location = []
            values, count = np.unique(count_country, return_counts=True)
            
            for i in range(len(values)):
                total_device_location.append((f"{values[i]}: {count[i]}\n"))
            
        except iproyal_login:
            return False
        return {"balance": balance, 
                "email": email, 
                "online_devices": active_devices, 
                "total_location": total_device_location, 
                "referral_status": self.user.affiliate_stats()["json"]}

class runHoney:
    def __init__(self, jwt_token : str, proxy):
        self.user = HoneyGain()
        self.token = jwt_token
        
        self.proxy = checkProxy(proxy=proxy)
        if self.proxy is not None:
            self.user.set_proxy(proxy) # format ip:port:username:password
        self.user.set_jwt_token(jwt_token=jwt_token) # set the token
        
    def checkEarning(self):
        try:
            user_devices = self.user.devices()
            #email = self.user.me()#["json"]["email"] # this doesn"t work for some reason, unless you fix the api
            
            short_session = requests.Session()
            
            try:
                proxy = self.proxy.split(":")
                short_session.proxies = {
                    "http": f"socks5://{proxy[2]}:{proxy[3]}@{proxy[0]}:{proxy[1]}", 
                    "https" : f"socks5://{proxy[2]}:{proxy[3]}@{proxy[0]}:{proxy[1]}"
                }
            except AttributeError:
                email = short_session.get(url="https://dashboard.honeygain.com/api/v1/users/me", headers={"authorization": "Bearer " + self.token}).json()["data"]["email"]
        except honeygain_login:
            print("[honeygain] Incorrect Token")
            raise SystemExit
        
        count_cd_device = 0 # count the numbers of devices that have content delivery enabled
        count_device_type = [] # device operating system
        
        for i in range(len(user_devices)):
            if (user_devices[i]["streaming_enabled"]) is True:
                count_cd_device += 1

            count_device_type.append([user_devices[i]["manufacturer"]])
        
        total_device = []
        values, count = np.unique(count_device_type, return_counts=True)
        for i in range(len(values)):
            total_device.append((f"{values[i]}: {count[i]}\n"))
        
        return {"balance": self.user.stats_today_jt(), # counting only JMPT mode because who uses HG mode anyways?
                "traffic": convert_size(int(self.user.stats_today()["gathering"]["bytes"])), 
                "devices": total_device, 
                "cd_devices": count_cd_device, 
                "contact": email}
    
    def claimPot(self):
        result = self.user.open_honeypot()
        
        if result["success"] == True: 
            claimed_amount = result["credits"]["credits"]
        else: 
            claimed_amount = None
        return claimed_amount

class runJMPT:
    def __init__(self, token : str, proxy):
        self.token = "Bearer " + token
        self.proxy = checkProxy(proxy=proxy)

    def checkEarning(self):
        session = requests.Session()
        session.headers = {"authorization": self.token}
        
        if self.proxy is None:
            pass
        else:
            proxy = self.proxy.split(":")
            session.proxies = {"http": f"socks5://{proxy[2]}:{proxy[3]}@{proxy[0]}:{proxy[1]}", 
                               "https" : f"socks5://{proxy[2]}:{proxy[3]}@{proxy[0]}:{proxy[1]}"
                               }
        current_price = session.get(url="https://api.jumptask.io/currency/").json()["data"]["usd"] # gets the current price of jumptask to usd
        jmpt_balance = session.get(url="https://api.jumptask.io/accounting/balances").json()["data"]["total"] # gets your total jumptask balanace
        
        gas_fees = session.get(url="https://api.jumptask.io/token/market/gas-fees").json()["data"]["gas_fee"] # gets the market price current gas price
        
        # gets payout history | payment["status"], payment["requested_amount"], payment["created_at"]
        latest_payment = session.get(url="https://api.jumptask.io/accounting/payouts").json()["data"][0]["created_at"]
        
        # {"wallet": "wallet_address", "book_date": "2023-01-22T00:00:00+00:00", "amount": "0.005955267598467500", "created_at": "2023-01-22T00:06:05+00:00", "updated_at": "2023-01-22T21:11:58+00:00", "source": "hg", "type": "earnings"}
        wallet = session.get(url="https://api.jumptask.io/accounting/stats").json()["data"][0]["wallet"]
        
        # jumptask price to usd convertor | price = coin times usd price
        usd_price = private_main.convert_price(usd_price=float(jmpt_balance) * float(current_price))
        usd_gas_fees = private_main.convert_price(usd_price=float(gas_fees) * float(current_price))
            
        return {"wallet": wallet, 
                "today_balance": current_price, 
                "today_jmpt": jmpt_balance, 
                "usd_price": usd_price, 
                "gas_price": gas_fees, 
                "usb_tax": usd_gas_fees, 
                "latest_payment": latest_payment}
    
    def claimToken(self, balance):
        if balance >= private_main.THRESHOLD == True: # price is more than amount then claim proceed to payout
            payout = requests.post(url="https://api.jumptask.io/accounting/payouts/requests", headers={"authorization": self.token}).json()["data"]["status"]
            return payout
        else:
            return "not_enough_balance"

"""class runTraffmonetizer:
    def __init__(self, token: str, proxy):
        self.token = "Bearer " + token
        self.proxy = checkProxy(proxy=proxy)
    
    def checkEarning(self):
        session = requests.Session()
        
        if self.proxy is None:
            pass
        else:
            proxy = self.proxy.split(":")
            session.proxies = {"http": f"socks5://{proxy[2]}:{proxy[3]}@{proxy[0]}:{proxy[1]}", 
                               "https" : f"socks5://{proxy[2]}:{proxy[3]}@{proxy[0]}:{proxy[1]}"
                               }
        # to be done below here"""

class runProxyrack:
    def __init__(self, api_key: str, proxy):
        self.api_key = api_key
        self.proxy = checkProxy(proxy)
    
    def checkEarning(self):
        session = requests.Session()
        
        if self.proxy is None:
            pass
        else:
            proxy = self.proxy.split(":")
            session.proxies = {"http": f"socks5://{proxy[2]}:{proxy[3]}@{proxy[0]}:{proxy[1]}", 
                               "https" : f"socks5://{proxy[2]}:{proxy[3]}@{proxy[0]}:{proxy[1]}"
                               }
        headers = {
            'Api-Key': self.api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        #Get balance. Get available for payout balance of your account.
        balance = session.post('https://peer.proxyrack.com/api/balance', headers=headers).json()
        
        """
        Get bandwidth. Get bandwidth data for all devices or for specific device attached to your account.
        bandwidth
        
        Query parameters:
            device_id Optional
                ID of device for bandwidth review. If not provided - data for all devices will be returned.

            date_start Optional
                Start date for bandwidth data range in Y-m-d format. Required if date_end provided.
                If dates not specified - data for last 7 days will be returned.

            date_end Optional
                End date for bandwidth data range in Y-m-d format. Should not be grater then start date. Required if date_start provided.
                If dates not specified - data for last 7 days will be returned.
        """
        bandwidth = session.post("https://peer.proxyrack.com/api/bandwidth", headers=headers).json()
        
        return {"balance": float(balance["data"]["balance"].replace("$", "")), # returns your current balance
                "traffic": bandwidth["data"]["bandwidth"][str(datetime.datetime.utcnow().date())], # PER GB
                }
        

if __name__ == "__main__":
    test_run = runProxyrack(api_key="TEST", proxy=None)
    print(test_run.checkEarning())
