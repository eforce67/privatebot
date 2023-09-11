import os, logging, asyncio, pandas as pd, random, datetime, json
import api
import yaml # pyyaml
import discord # pycord
from discord_webhook import DiscordWebhook # discord webhook

"""
Main script created by @Neonshark#2321. 
This starts the discord webhook, and also loads the config + etc.
"""

# list of supported applications
supported_apps = {"honeygain": [], 
                  "earnapp": [], # todo
                  "pawns": [],
                  "traffmonetizer": [], # todo
                  "proxyrack": [], # todo
                  "jumptask": []
                  }

with open(f"{os.path.dirname(os.path.realpath(__file__))}/database/config.yaml", "r") as config:
    config_data = yaml.safe_load(config)

# load images
HG_IMAGE = config_data["honeygain_logo"]
IPR_IMAGE = config_data["iproyal_logo"]
EA_IMAGE = config_data["earnapp_logo"]
JMPT_IMAGE = config_data["jumptask_logo"]
PR_IMAGE = config_data["proxyrack_logo"]
JMPT_IMAGE1 = config_data["jumptask_thumbnail"]
JMPT_IMAGE2 = config_data["jumptask_bottom"]
REFERRAL_IMAGE = config_data["referral_image"]

APPLICATION = config_data["application"]
THRESHOLD = config_data["jmpt_threshold"] # jumptask min payout before bailing out

JMPT_AUTO_REDEEM = config_data["jmpt_redeem"] # true or false to auto redeem jmpt tokens
HG_AUTO_REDEEM = config_data["hp_redeem"] # true or false to auto redeem honeypot

webhook_url = config_data["discord_webhook"] # your discord webhook

# Initialize logging
if config_data.get("logging"):
    log_file_path = f"./database/logs/log-{datetime.datetime.now().strftime('%d-%m-%Y H%H-M%M-S%S')}.txt"
    logging.basicConfig(filename=log_file_path, filemode="w", level=logging.DEBUG, format="%(asctime)s %(levelname)s:%(name)s: %(message)s")
    logging.info("The script has started without any issues...")

# Function to clear the last hour data
def clear_last_data(last_hour):
    if last_hour:
        last_hour.pop(0)

def readCSV(application : str):
    return pd.read_csv(f"{os.path.dirname(os.path.realpath(__file__))}/database/secure/{application}/accounts.csv", 
                           skipinitialspace=True, 
                           usecols=["token", "proxy_ip"],  
                           low_memory=True)

def convert_price(usd_price):
    TRACK = 0 # set the track = 0
    NUMBER = 5 # WARNING: keep this at 5
    total_usd_price = []
    for number in str(usd_price):
        if TRACK == NUMBER:
            break
        elif TRACK != NUMBER:
            if number in ["0", "."]:
                total_usd_price.append(number) # appending the dot or zero only
            else:
                total_usd_price.append(number) # appending any number
                TRACK += 1 # giving points only when its a integer
    return float("".join(total_usd_price))

def manageLasthour(session : list, match_value, total):
    last_hour = None
    if len(session) == 0:
        pass
    else:
        try:
            for line in range(len(session)):
                if session[line][0] == match_value:
                    last_hour = session[line][1]
                    del session[line]
        except:
            pass
    """
    Else statement is unnecessary as there are only four possible outcomes. 
    If additional outcomes arise, the code will require revision.
    """
    if last_hour == None: # outcome. 1
        earning_measure = "Your balance is"
    elif total == last_hour: # outcome. 2
        earning_measure = "Your balance remained the same"
    elif total > last_hour: # outcome. 3
        earning_measure = f"Your balance increased by +{(total - last_hour)}" # returning positive 
    elif total < last_hour: # outcome. 4
        earning_measure = f"Your balance decreased by {(last_hour - total)}" # will return a negative number
    return earning_measure

async def prepareData(**kwargs): # expected values: embed, webhook, last_hour, wallet, total
    embed_dict = kwargs["embed"].to_dict()
    json.dumps(embed_dict)
    kwargs["webhook"].add_embed(embed=embed_dict)
    
    clear_last_data(kwargs["last_hour"])
    kwargs["last_hour"].append([kwargs["value1"], kwargs["value2"]])
    await asyncio.sleep(random.randint(1, 30)) # random cooldown required

class privateBot:
    def __init__(self, ids):
        self.ids = ids
    
    async def createLoop(self):
        while True:
            webhook = DiscordWebhook(url=webhook_url) # creates the discord webhook
            for id in self.ids:
                if id == "honeygain": # honeygain
                    csv_data = readCSV(application=id)
                    for i in range(len(csv_data)):
                        token = csv_data.values[i][0]
                        proxy = csv_data.values[i][1]
                            
                        honeygain = api.runHoney(jwt_token=token, proxy=proxy)
                        now = datetime.datetime.utcnow()
                            
                        if int(now.strftime("%H")) == 1 and HG_AUTO_REDEEM is True: # the utc time has reset. luckypot has been spotted, time to claim
                            claim_result = honeygain.claimPot()

                            if claim_result == None:
                                status = "The script tried to claim the honeygain pot but failed to claim the honeypot, perhaps the account is **banned** or did **not earned more** than `15/mb` before the `UTC time` resets. This problem can also occur if you already ran the instance and the script claimed the pot."                           
                                statuses = "failure"
                            else:
                                status = "The script successfully claimed the honeypot without any issues!"
                                statuses = "success"
                            embed = discord.Embed(title=f"UTC TIME RESETS", 
                                                description=status, 
                                                color=discord.Colour.gold())
                            embed.set_author(name="Honeygain", icon_url=HG_IMAGE)
                            embed.set_thumbnail(url=HG_IMAGE)
                            embed.add_field(name="your winnings are", value=claim_result, inline=True)
                            embed.add_field(name="status", value=statuses, inline=True)
                            embed.set_footer(text="created by @Neonshark#2321")

                            embed_dict = embed.to_dict()
                            json.dumps(embed_dict)
                            webhook.add_embed(embed=embed_dict)

                        result = honeygain.checkEarning()
                        earnings = result["balance"]
                        bandwidth = result["traffic"]
                        total_device = "".join(result["devices"])
                        content_delivery_devices = result["cd_devices"]
                        email = result["contact"]
                            
                        total = earnings["total"]["credits"]
                        earning_measure = manageLasthour(session=supported_apps[id], match_value=email, total=total)
                                    
                        embed = discord.Embed(title=f"{earning_measure} [{convert_price(usd_price=total)}/CD | JMPT MODE]", 
                                            description=f"Your honeygain earnings have been **updated** for the user: ||`{email}`||, see the following below! __[honeygain dashboard](https://dashboard.honeygain.com/)__", 
                                            color=discord.Colour.gold())
                        embed.set_author(name="Honeygain", icon_url=HG_IMAGE)
                        embed.set_thumbnail(url=HG_IMAGE)
                        embed.add_field(name="**traffic shared**", value=bandwidth, inline=True)
                        embed.add_field(name="**honeyjar winnings**", value=f"{earnings['winning']['credits']}/CD", inline=True)
                        embed.add_field(name="**referral earnings**", value=f"{earnings['referral']['credits']}/CD", inline=True)
                        embed.add_field(name="**other earnings**", value=f"{earnings['other']['credits']}/CD", inline=True)
                        embed.add_field(name="**active content delivery devices: **", value=content_delivery_devices, inline=True)
                        embed.add_field(name="**devices: **", value=total_device)
                        embed.set_footer(text="created by @Neonshark#2321")
                                    
                        await prepareData(embed=embed, webhook=webhook, last_hour=supported_apps["honeygain"], value1=email, value2=total)
                
                if id == "pawns": # iproyal pawns
                    csv_data = readCSV(application=id)
                    for line in range(len(csv_data)):
                        token = csv_data.values[line][0]
                        proxy = csv_data.values[line][1]
                            
                        pawns = api.runIProyal(jwt_token=token, proxy=proxy)
                        result = pawns.checkEarning()
                        referral = result["referral_status"]
                        
                        total = result["balance"]["balance"]
                        earning_measure = manageLasthour(session=supported_apps[id], match_value=token, total=total)
                        
                        embed = discord.Embed(title=f"{earning_measure} [{convert_price(usd_price=total)}/USD]", 
                                            description=f"Your iproyal pawns earnings have been **updated** for the user: ||`{result['email']}`||, see the following below! __[pawns dashboard](https://dashboard.pawns.app/)__", 
                                            color=discord.Colour.blurple())
                        embed.set_author(name="Pawns", icon_url=IPR_IMAGE)
                        embed.set_thumbnail(url=IPR_IMAGE)
                        embed.add_field(name="**traffic shared**", value=f"{result['balance']['traffic_sold']}/GB", inline=True)
                        embed.add_field(name="**total refferal earnings**", value=f"{referral['total_commissions_amount']}/USD", inline=True)
                        embed.add_field(name="**today referral earnings**", value=f"{referral['today_commissions_amount']}/USD", inline=True)
                        embed.add_field(name="**user pending payment**", value=f"{result['balance']['pending_balance_amount']}/USD", inline=True)
                        embed.add_field(name="**referral pending payment**", value=f"{referral['pending_commissions_amount']}/USD", inline=True)
                        embed.add_field(name="**active devices**", value=f"{result['online_devices']}")
                        embed.add_field(name="**devices location**", value="".join(result['total_location']))
                        embed.set_footer(text=f"{referral['registered_users_count']} have registered using your link!", icon_url=REFERRAL_IMAGE)
                        
                        await prepareData(embed=embed, webhook=webhook, last_hour=supported_apps["pawns"], value1=token, value2=total)
                if id == "earnapp": # earnapp brightdata
                    csv_data = readCSV(application=id)
                    for line in range(len(csv_data)):
                        token = csv_data.values[line][0]
                        proxy = csv_data.values[line][1]
                        
                        results = api.runEarnapp(oath_token=token,proxy=proxy)
                        result = results.checkEarning()
                        
                        balance = result["money"]
                        total = balance["balance"]
                        email = result["contact"]
                        
                        earning_measure = manageLasthour(session=supported_apps[id], match_value=email, total=total)
                        
                        embed = discord.Embed(title=f"{earning_measure} [{total}/USD]", 
                                            description=f"Your earnapp earnings have been **updated** for the email: ||`{email}`||, see the following below! __[earnapp dashboard](https://earnapp.com/dashboard)__", 
                                            color=discord.Colour.brand_green())
                        embed.set_author(name="Earnapp", icon_url=EA_IMAGE)
                        embed.set_thumbnail(url=EA_IMAGE)
                        embed.add_field(name="**current balance**", value=f"${total}", inline=True)
                        embed.add_field(name="**today referral earnings**", value=f"${balance['ref_bonuses']}", inline=True)
                        embed.add_field(name="**lifetime referral earnings**", value=f"${balance['ref_bonuses_total']}", inline=True)
                        embed.add_field(name="**lifetime earnings**", value=f"${balance['earnings_total']}", inline=True)
                        embed.add_field(name="**multiplier**", value=f"(**{balance['multiplier']}**)x", inline=True)
                        embed.add_field(name="**pending redemption**", value=f"||{balance['redeem_details']}||", inline=True)
                        
                        embed.set_footer(text=f"there are {result['online']} devices online!")
                        await prepareData(embed=embed, webhook=webhook, last_hour=supported_apps[id], value1=email, value2=total)
                    
                if id == "jumptask": # jump into the task
                    csv_data = readCSV(application=id)
                    for line in range(len(csv_data)):
                        token = csv_data.values[line][0]
                        proxy = csv_data.values[line][1]
                        
                        results = api.runJMPT(token=token,proxy=proxy)
                        result = results.checkEarning()
                        
                        wallet = result["wallet"] # gets your wallet
                        current_price = convert_price(result["today_balance"]) # current price of jumptask
                        total = convert_price(result["today_jmpt"]) # your current balance in jumptask tokens
                        usd_price = result["usd_price"] # your current balance in usd dollars
                        jmpt_gas_fees = convert_price(result["gas_price"]) # jmpt gas fees in tokens
                        usd_gas_fees = result["usb_tax"] # jmpt gas fees in usd dollars
                        latest_payment = result["latest_payment"] # the date of your latest payment
                        
                        earning_measure = manageLasthour(session=supported_apps[id], match_value=wallet, total=total)
                        
                        embed = discord.Embed(title=f"{earning_measure} [{convert_price(usd_price=total)}/JMPT]", 
                                                description=f"Your jumptask earnings have been **updated** for the wallet: ||`{wallet}`||, see the following below! __[jumptask dashboard](https://app.jumptask.io/)__", 
                                                color=discord.Colour.nitro_pink())
                        embed.set_author(name="Jumptask", icon_url=JMPT_IMAGE)
                        embed.set_thumbnail(url=JMPT_IMAGE2)
                        embed.add_field(name="**JMPT Current Price**", value=f"{current_price}/**JMPT**", inline=True)
                        embed.add_field(name="**Your JMPT Balance**", value=f"{total}/**JMPT**\nor\n${usd_price}", inline=True)
                        embed.add_field(name="**JMPT Gas Fees**", value=f"{jmpt_gas_fees}/**JMPT**\nor\n**$**{usd_gas_fees}", inline=True)
                        embed.add_field(name="**Latest Payout**", value=latest_payment, inline=True)
                        
                        if JMPT_AUTO_REDEEM is True: # if auto redeem is turned on
                            claiming_result = results.claimToken(balance=usd_price)
                            if claiming_result == "not_enough_balance": 
                                embed.add_field(name="Payout status", value=f"not enough (**min**: `${THRESHOLD}`)", inline=True)
                            else: 
                                embed.add_field(name="Payout status", value=claiming_result, inline=True) 
                            embed.set_footer(text=f"created by @Neonshark#2321", icon_url=JMPT_IMAGE1)
                        
                        await prepareData(embed=embed, webhook=webhook, last_hour=supported_apps[id], value1=wallet, value2=total)
                
                if id == "proxyrack": # proxyrack
                    csv_data = readCSV(application=id)
                    for line in range(len(csv_data)):
                        key = csv_data.values[line][0]
                        proxy = csv_data.values[line][1]
                        
                        results = api.runProxyrack(api_key=key, proxy=proxy)
                        result = results.checkEarning()
                        total = convert_price(result['balance'])
                        
                        earning_measure = manageLasthour(session=supported_apps[id], match_value=key, total=total)
                        
                        embed = discord.Embed(title=f"{earning_measure} [{total}/USD]", 
                                                description=f"Your proxyrack earnings have been **updated** for the token: ||`{key}`||, see the following below! __[proxyrack dashboard](https://peer.proxyrack.com/)__", 
                                                color=discord.Colour.dark_red())
                        embed.set_author(name="ProxyRack", icon_url=JMPT_IMAGE)
                        embed.set_thumbnail(url=PR_IMAGE)
                        embed.add_field(name="**current balance**", value=f"{total}/USD", inline=True)
                        embed.add_field(name="**bandwidth shared**", value=f"{convert_price(result['traffic'])}/GB", inline=True)
                        
                        await prepareData(embed=embed, webhook=webhook, last_hour=supported_apps[id], value1=wallet, value2=total)
            
            webhook.execute() # execute the webhook
            now = datetime.datetime.utcnow() # get the current time
            next_hour = now.replace(microsecond=0, second=0, minute=0) + datetime.timedelta(hours=1)
            delay = (next_hour - now).total_seconds()
            await asyncio.sleep(delay)
            print(supported_apps)
            
            logging.info(f"The time is now: {next_hour}, the script will execute the given tasks.")
        
if __name__ == "__main__":
    def menuScreen():
        print("""========================
            welcome to private, i couldn't think of a name to call it so here you go.
            - brought to you by @Neonshark#2321
            1. [start script!]
            2. [help?]
            ========================""")
        prompt = int(input("type in your choice: "))
        
        if prompt == 1:
            if config_data["logging"] is True:
                logging.basicConfig(filename=f"./database/logs/log-{datetime.datetime.now().strftime('%d-%m-%Y H%H-M%M-S%S')}.txt", filemode="w", level=logging.DEBUG, format="%(asctime)s %(levelname)s:%(name)s: %(message)s")
                logging.info("The script has started without any issues...")
            
            async def runBot():
                bot = privateBot(ids=APPLICATION)
                await bot.createLoop()
            asyncio.run(runBot())
        elif prompt == 2:
            print("""
                  [Proxy Support] -> The code was made to support only socks5 proxies
                  
                  [Application Support] -> This script currently supports the following applications:
                  honeygain, earnapp, proxyrack, jumptask
                  
                  [Honeygain Mode] -> This application only captures honeygain JMPT mode and not the honeygain mode
                  
                  [Using Multiple Accounts] -> This script can infact check multiple accounts earnings on the same application. 
                  All you have to do is correctly add your tokens.
                  
                  [Tokens expiring] -> Earnapp and Traffmonetizer tokens will expire in a few days. This script does not have an option to regenerate new tokens.
                  
                  [About Me] -> I am neonshark, I code and this script is bad and needs more work.
                  """)
            button = input("type anything to go back || press \"X\" to exit script: ")
            if button.lower() == "x":
                exit()
            else:
                menuScreen()
    try:
        menuScreen()
    except KeyboardInterrupt:
        menuScreen()
