#libraries used
import requests
import json
import sqlite3
import datetime
from bs4 import BeautifulSoup
from tabulate import tabulate

#finnhub.io api key
token = '################'

#connecting to database
conn = sqlite3.connect('databasename')
c = conn.cursor()

#commands that are available to use
commands = ['buy', 'check', 'browse', 'sell', 'quit']
uses = ['buy stocks', 'check your stocks',
        'browse stock options', 'sell stocks', 'quits program']


def buyStock(name):
    print()

    #get current money, stock, and add up the total
    money = changeMoney('read')
    money = round(money, 2)
    stock = getStockMoney()
    total = round(money + stock, 2)

    print(f'You have ${money} available.')
    print(f'You have ${stock} in stocks.')

    print()
    print(f'${total} in total money.')

    print()
    print("Fetching data...")
    print()

    name = name.lower()

    #getting the stock symbol if you enter a company
    url = 'https://www.marketwatch.com/tools/quotes/lookup.asp?siteID=mktw&Lookup={0}&Country=all&Type=All'.format(
        name)
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    data = soup.find_all('td', class_='bottomborder')

    #current price and company of the stock
    current_price = currentPrice(name)
    company = name.upper()

    sym = 0
    com = 1

    if current_price == 0:
        if name == 'google':
            symbol = 'GOOG'
            company = 'Google'

        else:
            symbol = data[sym].text
            company = data[com].text
            sym += 3
            com += 3

        current_price = currentPrice(symbol)

    #if there isn't a price with the symbol, moves you to the main page
    if current_price == 0:
        print('There is no stock by this name.')
        mainPage()

    else:
        
        #gets the price, and asks if it is the comapny you were looking for
        price = '$' + str(current_price)
        correctStock = input(company + ' : ' + price +
                  '. Is this the stock you were looking for (y/n): ').lower()

        #if the company and price is incorrect, it gathers the data for the next company
        if correctStock == 'n' or correctStock == 'no':
            while (correctStock == 'no' or correctStock == 'n') and com < len(data):
                symbol = data[sym].text
                company = data[com].text

                sym += 3
                com += 3

                current_price = currentPrice(symbol)
                price = '$' + str(current_price)
                correctStock = input(company + ' : ' + price +
                          '. Is this the stock you were looking for: ').lower()

            if correctStock == 'back' or correctStock == 'b':
                mainPage()

        #if the company is correct, it asks if you want to buy it
        if correctStock == 'yes' or correctStock == 'y':
            buyOption = input('Do you want to buy it (y/n): ')
            
            #if you do, it shows you the price of one share, and asks how many you want to buy
            if buyOption == 'yes' or buyOption == 'y':

                number = input(
                    'How many stocks do you wanna buy. 1 ' + symbol + ' = ' + price + ': ')

                #checks if its a valid input
                checkNumber(number, current_price, symbol, money)

                number = int(number)
                moneyUsed = current_price * number

                money -= moneyUsed
                money = round(money, 2)

                stock += moneyUsed
                stock = round(stock, 2)

                #fetching info from database, checking if the stock was bought previously
                c.execute(
                    """select number from stocks where name = '{}'""".format(symbol))
                value = c.fetchone()
                
                #adds to database if its a new stock
                if not value:
                    addToDatabase(symbol, current_price, number)

                #or adds to a stock you've previously bought
                else:
                    value = value[0]
                    value += number
                    c.execute(
                        """update stocks set number = {} where name = '{}'""".format(value, symbol))
                    conn.commit()

                #changes the amount of money you have in stocks, and cash
                changeMoney('write', money)

                print(f"You have ${money} left.")
                print(f'You have ${stock} in stocks.')

            #takes you to main page if you don't, or if its an invald input
            elif buyOption == 'n' or buyOption == 'no':
                mainPage()

            else:
                print('Invalid input.')
                mainPage()

        else:
            print('Invalid input')
            mainPage()

    mainPage()


def checkNumber(num, cost, symbol, money):
    #checks if the number of stocks you wanted to buy is a valid number
    while num.isdigit() == False or cost * int(num) > money:
        print('Invalid. Must be a number, or enter 0 to not buy any.')
        num = input('How many stocks do you wanna buy. 1 ' +
                    symbol + ' = ' + cost + ': ')

    if num == '0':
        mainPage()


def addToDatabase(name, cost, numbers):
    #adds the new stock to your database
    c.execute("""insert into stocks(name, cost, number) values ('{}', {}, {})""".format(
        name, cost, numbers))
    conn.commit()


def changeMoney(change, moneyRemaining=None):

    #reads the amount of money you have
    if change == 'read':
        with open('stocks/money.txt', 'r') as f:
            money = float(f.readline())
            f.close()
        return money

    #changes the amount of money, if you sold or bought
    elif change == 'write':
        with open('stocks/money.txt', 'w') as f:
            f.write(str(moneyRemaining))
            f.close()


def getStockMoney():
    #gets the number of stocks buy reading your database
    c.execute("""select name, number from stocks""")
    values = c.fetchall()
    stockValue = 0

    #gets current price for each stock in your database
    for i in range(len(values)):
        name = values[i][0]
        number = values[i][1]
        current_price = currentPrice(name)
        stockValue += number * current_price

    stockValue = round(stockValue, 2)
    return stockValue


def checkValue():
    #gets all the values from your database
    c.execute("""select * from stocks""")
    values = c.fetchall()
    results = []
    print()

    #gets current price for each stock in your database, and compares it to prices when you bought it
    for i in range(len(values)):
        symbol = values[i][0]
        index = values[i][2]
        price = values[i][1]
        current_price = currentPrice(symbol)
        netGain = (index * current_price) - (index * price)

        results.append((symbol, index, price, current_price, netGain))

    #returns a table of your data
    table = tabulate(results, headers=[
                     "Stock", "#'s", "Bought", "Current", "Gain/Loss"], tablefmt='orgtbl')
    return table


def currentPrice(symbol):
    #getting the current price of company by using Finnhub API
    r = requests.get(
        f'https://finnhub.io/api/v1/quote?symbol={symbol}&token={token}').json()
    current_price = r['c']
    return current_price


def mainPage():
    #main page, redirects to all of the commands
    user = input(
        "What would you like to do (write 'help' or 'h' to see all commands): ").lower()

    if user == 'h' or user == 'help':
        print()
        print(allCommands(user))

    elif user in commands:
        allCommands(user)

    else:
        if user == 'q':
            print("Goodbye!")
            quit()
        else:
            print("Invalid command, use 'help' or 'h' to see list.")
            mainPage()


def allCommands(cmd):
    #what does the redirection in the main page
    cmd = cmd.lower()

    #takes you to where you are buying stocks
    if cmd == 'buy':
        #asks which stock you want to buy
        name = input('What stock would you like to buy: ')
        if name == 'back' or name == 'quit':
            mainPage()
        else:
            buyStock(name)
    
    #where you can check the status of the stocks you own
    elif cmd == 'check':
        #calls checkValue, and prints the table that it returns
        table = checkValue()
        print(table)
        print()
        mainPage()
   
    #shows the list of commmands, and what they do
    elif cmd == 'help' or cmd == 'h':
        for i in range(len(commands)):
            print(f"'{commands[i]}' - {uses[i]}")
        print()
        mainPage()
    
    #selling stocks
    elif cmd == 'sell':
        sellStock()
    
    #exiting the program
    elif cmd == 'quit':
        print('Goodbye!')
        quit()
    
    #browse the different stocks, and getting different data
    elif cmd == 'browse':
        #asks which stock you want to look at
        stock = input("What stock do you want to look at: ")
        if stock == 'back' or stock == 'quit':
            mainPage()
        else:
            browse(stock)


def sellStock():
    #where to sell stocks

    #goBack is if you wanted to go back to the main page
    goBack = False
    
    #asks which stocks, and shows a table of your stocks that you own
    print('Which stock do you wanna sell?')

    table = checkValue()
    print(table)

    print()
    
    #asks you for a stock symbol, and checks if you have that in your database
    getStock = input("Select stock symbol: ").upper()

    c.execute("""select number from stocks where name = '{}'""".format(getStock))
    value = c.fetchone()

    #redirects to mainPage
    if getStock.lower() == 'back' or getStock.lower() == 'quit':
        mainPage()

    else:
        #if it isn't owned by you, it will ask until you give a valid answer
        while not value:
            print('Invalid input. Stock not bought.')
            getStock = input("Select stock symbol: ").upper()
            if getStock.lower() == 'back' or getStock.lower() == 'quit':
                mainPage()
            c.execute("""select number from stocks where name = '{}'""".format(getStock))
            value = c.fetchone()

        #gets the current price and asks you how many you want to buy
        shares = value[0]
        numOfStocks = input("How many stocks do you wanna sell: ")

        #checks if its a valid input
        while numOfStocks.isdigit() == False or int(numOfStocks) > shares:
            print("Invalid input.")

            numOfStocks = input("How many stocks do you wanna sell: ")

            if numOfStocks.lower() == 'back' or numOfStocks.lower() == 'quit':
                goBack = True
                break
        
        #if input was either 'back' or 'quit', redirects to main page
        if goBack:
            mainPage()

        else:

            #changes the number of stocks in your database
            numOfStocks = int(numOfStocks)
            shares -= numOfStocks

            #gets current money, and adds the amount that stocks sold for to it
            money = changeMoney('read')
            soldStocks = currentPrice(getStock) * numOfStocks
            money += soldStocks
            money = round(money, 2)
            changeMoney('write', money)

            #if you have no more of that stock remaining, it deletes it from your database
            if shares == 0:
                c.execute("""delete from stocks where name = '{}'""".format(getStock))
                conn.commit()

            #or it changes the shares of that stock you have left
            else:
                c.execute(
                    """update stocks set number = {} where name = '{}'""".format(shares, getStock))
                conn.commit()

            #prints table of what's remaining, the goes to the main page
            print()
            print("Stocks sold")
            print()
            table = checkValue()
            print(table)
            print()

    mainPage()


def browse(name):
    #browsing different stocks 

    #getting company and stock symbol of what you've enetered
    print()
    url = 'https://www.marketwatch.com/tools/quotes/lookup.asp?siteID=mktw&Lookup={0}&Country=all&Type=All'.format(
        name)
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    data = soup.find_all('td', class_='bottomborder')

    sym = 0
    com = 1

    r = requests.get(
        f'https://finnhub.io/api/v1/quote?symbol={name}&token={token}').json()

    if r['c'] == 0:
        if name == 'google':
            symbol = 'GOOG'
            company = 'Google'

        else:
            symbol = data[sym].text
            company = data[com].text
            sym += 3
            com += 3

    #if there is no stock by the given name
    if currentPrice(symbol) == 0:
        print('No stock by this name.')
        mainPage()

    else:
        #asks if this is the correct stock
        correctStock = input(
            company + ' : Is this the stock you were looking for (y/n): ').lower()

        #if it isn't, gets the next company in the table
        while correctStock == 'no' or correctStock == 'n':
            symbol = data[sym].text
            company = data[com].text

            sym += 3
            com += 3

            correctStock = input(
                company + ' : Is this the stock you were looking for: ').lower()

        #redirects to main page
        if correctStock == 'back' or correctStock == 'b':
            mainPage()

    if correctStock == 'yes' or correctStock == 'y':

        #gets the information that pertains to the stock
        r = requests.get(
            f'https://finnhub.io/api/v1/quote?symbol={symbol}&token={token}').json()

        #changing unix time to date and time
        milli = r['t']
        time = datetime.datetime.fromtimestamp(
            milli).strftime('%Y-%m-%d %H:%M:%S.%f')
        r['t'] = time

        #changing the json keys to more descriptive names
        names = {'c': 'Current', 'o': 'Open', 'h': 'Highest',
              'l': 'Lowest', 'pc': 'Previous close', 't': 'Date'}
        info = dict((names[key], value) for (key, value) in r.items())

        #prints the info of the stock
        print(info)
        print()

        #asks if you want to check more stocks, and redirects to main page if you don't
        while True:
            moreStocks = input('Do you want to look at more stocks (y/n): ').lower()
            
            if moreStocks == 'y' or moreStocks == 'yes':
                typeOfStock = input("What stock do you want to look at: ")
                browse(typeOfStock)
            
            elif moreStocks == 'no' or moreStocks == 'n':
                break
            
            else:
                print('Invalid input.')

        mainPage()

    else:
        print("Invalid input.")
        mainPage()


mainPage()
conn.close()
