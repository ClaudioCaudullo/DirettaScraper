from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
from bs4 import BeautifulSoup as soup
from datetime import datetime
import time
import threading
import pandas as pd
import numpy as np
import json
import schedule
import requests
import hashlib
import snscrape.modules.twitter as sntwitter
from textblob import TextBlob
import sys
import tweepy
import matplotlib.pyplot as plt
import os
import nltk
import pycountry
import re
import string
from wordcloud import WordCloud, STOPWORDS
from PIL import Image
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from langdetect import detect
from nltk.stem import SnowballStemmer
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from dotenv import load_dotenv

load_dotenv()

nltk.download('vader_lexicon') #download del vocabolario di nltk
nltk.download('stopwords')     #download delle stopwords
# Authentication
consumerKey = os.environ["consumerKey"]
consumerSecret = os.environ["consumerSecret"]
accessToken = os.environ["accessToken"]
accessTokenSecret = os.environ["accessTokenSecret"]
auth = tweepy.OAuthHandler(consumerKey, consumerSecret)
auth.set_access_token(accessToken, accessTokenSecret)
api = tweepy.API(auth)
risorsa_occupata = False
insidePolling = False

#Calcolo percentuale dei post di una tipologia(negativi/neutrali/positivi) su tutti i post 
def percentage(part,whole):
    return 100 * float(part)/float(whole)

def pollingPartite():
    global risorsa_occupata
    global insidePolling
    if risorsa_occupata:  #controllo effettuato per evitare di avere più processi in parallelo che lavorano sulla stessa funzione così' da evitare problemi di
                          #concorrenza nella scrittura sui file
       # print("sono nel polling ma la risorsa è occupata") 
        return
    if insidePolling : 
        #print("sono nel polling ma il polling è occupato")
        return
    else :
        insidePolling = True

    f = open('sample.json') #apertura del file sample dove andare andare a prendere gli url delle partite 
    informazioni = json.load(f)   
    
    #settaggi vari di Selenium
    i=0
    s=Service("C:\Program Files (x86)\chromedriver-win64\chromedriver.exe") 
    options = Options()
    options.add_argument('headless')
    options.add_argument('window-size=2048x1536')
    options.add_argument("--start-maximized")
    options.add_argument("--incognito")
    options.add_argument("--log-level=3")
    driver = webdriver.Chrome(service=s,options=options)
    output=[]

    f = open('polling.json') #apertura del file su cui questa funzione deve lavorare
    data = json.load(f)   
    change=False #variabile booleana per indicare se è avvenuto un cambiamento così da aggiornare il file polling.json
    
    for match in informazioni:  #in match verranno conservate tutte le informazioni presenti nel file sample.json
        trovato=False
        t=0
        for match2 in data: #ciclo implementato per la sicurezza di avere ogni partita sia nel file polling.json che nel file sample.json
            if match2['id']==match['idEvent']: 
                trovato=True
                break
            t+=1
        driver.get(match['urlMatch']) #reindirizzamento sulla pagina specifica dell'evento(esempio: https://www.diretta.it/partita/l4XUgXVf)
        page_html = driver.page_source
        #scraping della pagina
        page_soup = soup(page_html,features="html.parser")
        risultato=page_soup.find('div',{'class':'detailScore__wrapper'}).getText()  #risultato(esempio:"0-0","1-0")
        stato=page_soup.find('div',{'class':'detailScore__status'}).getText()   #stato(esempio: "-", "10:00", "Fine primo tempo", "Finita")
        dettagli=page_soup.findAll('div',{'class':'smv__participantRow'}) #tutti le azioni salienti(esempio: cartellino giallo,goal,goal annullato,rigore sbagliato)
        events=[]
        tweets_list2 = []
        for dettaglio in dettagli: #prendo il singolo dettaglio per inserirlo nella lista degli eventi della partita
            minuto=dettaglio.find('div',{'class':'smv__timeBox'}).getText() #prendo il minuto dell'azione
            if dettaglio.find('svg',{'class':'yellowCard-ico'}) : #se è un cartellino giallo
                if(dettaglio.find('a',{'class':'smv__playerName'})): #se è presente il nome del giocatore
                    nome=dettaglio.find('a',{'class':'smv__playerName'}).getText() #prendo il nome
                    #creo l'evento e lo aggiungo al dizionario
                    dictionary ={
                        "idAzione" : hashlib.md5(("yellowCard-"+(nome+"-"+minuto)).encode('utf-8')).hexdigest(),
                        "Name" : nome,
                       # "Incident" : motivazione,
                        "minuto" : minuto,
                        "Tipo" : "giallo"
                    }
                    events.append(dictionary) #lo aggiungo agli eventi
            if dettaglio.find('svg',{'class':'footballGoal-ico'}) : #se è un goal
                if dettaglio.find('a',{'class':'smv__playerName'}): #se è presente il nome del giocatore
                    nome=dettaglio.find('a',{'class':'smv__playerName'}).getText() #prendo il nome
                    #creo l'evento e lo aggiungo al dizionario
                    dictionary ={
                        "idAzione" : hashlib.md5(("goal-"+(nome+"-"+minuto)).encode('utf-8')).hexdigest(),
                        "Name" : nome,
                        "minuto":minuto,
                        "Tipo" : "goal"
                    }
                    events.append(dictionary) #lo aggiungo agli eventi
     
            if dettaglio.find('svg',{'class':'footballOwnGoal-ico '}) : #se è un autogoal    
                if dettaglio.find('a',{'class':'smv__playerName'}): #se è presente il nome del giocatore 
                    nome=dettaglio.find('a',{'class':'smv__playerName'}).getText() #prendo il nome
                    #creo l'evento e lo aggiungo al dizionario
                    dictionary ={
                        "idAzione" : hashlib.md5(("autogoal-"+(nome+"-"+minuto)).encode('utf-8')).hexdigest(),
                        "Name" : nome,
                        "minuto":minuto,
                        "Tipo" : "autogoal"
                    }
                    events.append(dictionary) #lo aggiungo agli eventi
     
            if dettaglio.find('svg',{'class':'redYellowCard-ico '}) or dettaglio.find('svg',{'class':'card-ico '}): #se è un cartellino rosso
                if dettaglio.find('a',{'class':'smv__playerName'}) : #se è presente il nome del giocatore 
                    nome=dettaglio.find('a',{'class':'smv__playerName'}).getText() #prendo il nome
                    #creo l'evento e lo aggiungo al dizionario
                    dictionary ={
                        "idAzione" : hashlib.md5(("redCard-"+(nome+"-"+minuto)).encode('utf-8')).hexdigest(),
                        "Name" : nome,
                        "minuto":minuto,
                        "Tipo" : "rosso"
                    }
                    events.append(dictionary) #lo aggiungo agli eventi   
     
            if dettaglio.find('svg',{'class':'penaltyMissed-ico'}): #se è un rigore sbagliato
                if dettaglio.find('a',{'class':'smv__playerName'}): #se è presente il nome del giocatore 
                    nome=dettaglio.find('a',{'class':'smv__playerName'}).getText() #prendo il nome 
                    #creo l'evento e lo aggiungo al dizionario
                    dictionary ={
                        "idAzione" : hashlib.md5(("rigore_sbagliato-"+(nome+"-"+minuto)).encode('utf-8')).hexdigest(),
                        "Name" : nome,
                        "minuto":minuto,
                        "Tipo" : "rigore_sbagliato"
                    }
                events.append(dictionary) #lo aggiungo agli eventi 

            if dettaglio.find('svg',{'class':'var-ico'}): #se è stato usato il var per annullare un goal    
                if dettaglio.find('a',{'class':'smv__playerName'}): #se è presente il nome del giocatore
                    nome=dettaglio.find('a',{'class':'smv__playerName'}).getText() #prendo il nome   
                    #creo l'evento e lo aggiungo al dizionario
                    dictionary ={
                        "idAzione" : hashlib.md5(("goal_annullato-"+(nome+"-"+minuto)).encode('utf-8')).hexdigest(),
                        "Name" : nome,
                        "minuto":minuto,
                        "Tipo" : "goal_annullato"
                    }  
                    events.append(dictionary) #lo aggiungo agli eventi       
        
        if trovato==True: #è stato trovato un nuovo evento rispetto al polling fatto in precedenza
            #print("evento trovato")
            dictionary ={
                        "id" : match['idEvent'],
                        "actions": events,
                        "risultato" : risultato,
                        "state" : stato
                    }
            
            if risultato != data[t]['risultato']: #se il risultato è diverso da quello presente nel file polling.json
                #mando il messaggio su telegram
                messaggio="🆚 Match 🆚\n"+match['home']+" "+risultato+" "+match['away']+"\n" 
                URL='https://api.telegram.org/bot5114308196:AAGBlrtRzOzDczXU5npZg2pAMaTWg1pY_GE/sendMessage'
                r = requests.get(url = URL, params = {'chat_id':-1001520829278,'text':messaggio})  
                change=True #mi segno che è avvenuto un cambiamento
     
            if stato != data[t]['state']: #se lo stato è diverso da quello presente nel file polling.json (lo stato cambia quando passa ogni secondo,
                #perchè se il minuto conservato era 10:00 ed adesso siamo a 10:10 ho un altro stato, ma non notifico ogni cambio di minuto ma solo i finali dei tempi)
                change=True #mi segno che è avvenuto un cambiamento
                if(stato!="Finale"): #se non è finita la partita
                    if(stato=="Intervallo"): #se c'è l'intervallo
                        #mando il messaggio su telegram
                        messaggio="⏸ Fine primo tempo ⏸\n"+match['home']+" "+risultato+" "+match['away']+"\n"
                        URL='https://api.telegram.org/bot5114308196:AAGBlrtRzOzDczXU5npZg2pAMaTWg1pY_GE/sendMessage'
                        r = requests.get(url = URL, params = {'chat_id':-1001520829278,'text':messaggio})  
                else: #la partita è finita
                    #mando il messaggio su telegram
                    messaggio="⏹ Match Finito ⏹\n"+match['home']+" "+risultato+" "+match['away']+"\n"
                    URL='https://api.telegram.org/bot5114308196:AAGBlrtRzOzDczXU5npZg2pAMaTWg1pY_GE/sendMessage'
                    r = requests.get(url = URL, params = {'chat_id':-1001520829278,'text':messaggio})
                    #inizio la sentiment analysis
                    #considero i post contenenti i nomi di entrambe le squadre
                    keyword =  match['home']+" "+match['away']
                    positive = int(0)
                    negative = int(0)
                    neutral = int(0)
                    polarity = int(0)
                    tweet_list = []
                    neutral_list = []
                    negative_list = []
                    positive_list = []
                    j=1
                    try:
                        for j,tweet in enumerate(sntwitter.TwitterSearchScraper(keyword+' since:'+match['date']).get_items()): #prendo i post con la keyword dall'inizio della partita fino ad ora
                            if tweet.id in tweet_list: continue #se ho già analizzato il post in precedenza
                            analysis = TextBlob(tweet.content)
                            score = SentimentIntensityAnalyzer().polarity_scores(tweet.content)
                            neg = score["neg"]
                            neu = score["neu"]
                            pos = score["pos"]
                            comp = score["compound"]
                            polarity += analysis.sentiment.polarity
                            #print(tweet.content+"\n")
                            if neg > pos:
                                negative_list.append(tweet.content)
                                negative = int(negative + 1)
                            elif pos > neg:
                                positive_list.append(tweet.content)
                                positive = int(positive + 1)

                            elif pos == neg:
                                neutral_list.append(tweet.content)
                                neutral = int(neutral + 1)
                            if j>500:
                                break
                            tweet_list.append([tweet.date, tweet.id, tweet.content, tweet.user.username])
                    except Exception as e:
                        print("Scraping 1 finito")
                    
                    #adesso considero i post solo con il nome della squadra di casa con la stessa modalità di prima
                    j=1
                    keyword=match['home']
                    try:
                        for j,tweet in enumerate(sntwitter.TwitterSearchScraper(keyword+' since:'+match['date']).get_items()):
                            if tweet.id in tweet_list: continue
                            analysis = TextBlob(tweet.content)
                            score = SentimentIntensityAnalyzer().polarity_scores(tweet.content)
                            neg = score["neg"]
                            neu = score["neu"]
                            pos = score["pos"]
                            comp = score["compound"]
                            polarity += analysis.sentiment.polarity
                            #print(tweet.content+"\n")
                            if neg > pos:
                                negative_list.append(tweet.content)
                                negative = int(negative + 1)
                            elif pos > neg:
                                positive_list.append(tweet.content)
                                positive = int(positive + 1)

                            elif pos == neg:
                                neutral_list.append(tweet.content)
                                neutral = int(neutral + 1)
                            if j>500:
                                break
                            tweet_list.append([tweet.date, tweet.id, tweet.content, tweet.user.username])
                    except Exception as e:
                        print("Scraping 2 finito")

                    #adesso considero i post solo con il nome della squadra ospite con la stessa modalità di prima    
                    j=1
                    keyword=match['away']
                    try:
                        for j,tweet in enumerate(sntwitter.TwitterSearchScraper(keyword+' since:'+match['date']).get_items()):
                            if tweet.id in tweet_list: continue
                            analysis = TextBlob(tweet.content)
                            score = SentimentIntensityAnalyzer().polarity_scores(tweet.content)
                            neg = score["neg"]
                            neu = score["neu"]
                            pos = score["pos"]
                            comp = score["compound"]
                            polarity += analysis.sentiment.polarity
                            #print(tweet.content+"\n")
                            if neg > pos:
                                negative_list.append(tweet.content)
                                negative = int(negative + 1)
                            elif pos > neg:
                                positive_list.append(tweet.content)
                                positive = int(positive + 1)

                            elif pos == neg:
                                neutral_list.append(tweet.content)
                                neutral = int(neutral + 1)
                            if j>500:
                                break
                            tweet_list.append([tweet.date, tweet.id, tweet.content, tweet.user.username])
                    except Exception as e:
                        print("Scraping 3 finito")
                    #print(tweet_list)

                    #calcolo le percentuali dei post 
                    positive = percentage(positive, j)
                    negative = percentage(negative, j)
                    neutral = percentage(neutral, j)
                    polarity = percentage(polarity, j)
                    positive = format(positive, ".1f")
                    negative = format(negative, ".1f")
                    neutral = format(neutral, ".1f")   
                    #Number of Tweets (Total, Positive, Negative, Neutral)
                    tweet_list = pd.DataFrame(tweet_list)
                    neutral_list = pd.DataFrame(neutral_list)
                    negative_list = pd.DataFrame(negative_list)
                    positive_list = pd.DataFrame(positive_list)
                    print("total number: ",len(tweet_list))
                    print("positive number: ",len(positive_list))
                    print("negative number: ", len(negative_list))
                    print("neutral number: ",len(neutral_list))
                    #mando il messaggio su telegram
                    messaggio="💭Reazioni dei tifosi su twitter per la partita "+match['home']+" - "+match['away']+" 💭\n"+"🔎Numero totale di post:"+str(len(tweet_list))+"\n😄Post positivi: "+str(len(positive_list))+"\n😡Post negativi:"+str(len(negative_list))+"\n😶Post neutrali:"+str(len(neutral_list))+"\n"
                    URL='https://api.telegram.org/bot5114308196:AAGBlrtRzOzDczXU5npZg2pAMaTWg1pY_GE/sendMessage'
                    r = requests.get(url = URL, params = {'chat_id':-1001520829278,'text':messaggio})

                    #adesso elimino la partita dai file
                    del informazioni[i]
                    json_object = json.dumps(informazioni, indent = 4)
                    with open("sample.json", "w") as outfile:
                        outfile.write(json_object)
                    print("\nEliminazione evento\n")
     
            if(stato!="Finale"): 
                #print("Stato non finale,partita continua,aggiungo al file")
                output.append(dictionary)
            
            for actionUpdate in events: # controllo implementato per avere la sicurezza che il nuovo evento non sia stato già catturato da un polling precedente 
                actionFound=False
                for actionCache in data[t]['actions']:
                    if actionUpdate['idAzione'] == actionCache['idAzione']:
                        actionFound = True
                
                if not actionFound: #se l'evento è effettivamente nuovo
                    change = True #segno che c'è stato un update
                    #imposto il messaggio di aggiornamento in base alla tipologia d'evento
                    if actionUpdate['Tipo'] == 'goal': 
                        messaggio="⚽ GOOOOOOOL ⚽\n"+actionUpdate['minuto']+" "+match['home']+" "+risultato+" "+match['away']+"\n" + actionUpdate['Name'] +"\n"
                        
                    if actionUpdate['Tipo'] == 'giallo': 
                        messaggio="🟨 Cartellino giallo 🟨\n"+actionUpdate['minuto']+" "+match['home']+" "+data[t]['risultato']+" "+match['away']+"\n" + actionUpdate['Name'] +"\n"   
     
                    if actionUpdate['Tipo'] == 'rosso':
                        messaggio="🟥 Cartellino rosso 🟥\n"+actionUpdate['minuto']+" "+match['home']+" "+data[t]['risultato']+" "+match['away']+"\n" + actionUpdate['Name'] +"\n"  
     
                    if actionUpdate['Tipo'] == 'autogoal':
                        messaggio="🤬 Autogol 🤬\n"+actionUpdate['minuto']+" "+match['home']+" "+risultato+" "+match['away']+"\n" + actionUpdate['Name'] +"\n"                                                                
                        
                    if actionUpdate['Tipo'] == 'rigore_sbagliato':
                        messaggio="⚠ Rigore sbagliato ⚠\n"+actionUpdate['minuto']+" "+match['home']+" "+data[t]['risultato']+" "+match['away']+"\n" + actionUpdate['Name'] +"\n"    

                    if actionUpdate['Tipo'] == 'goal_annullato':
                        messaggio="⚠ Gol annullato ⚠\n"+actionUpdate['minuto']+" "+match['home']+" "+risultato+" "+match['away']+"\n" + actionUpdate['Name'] +"\n"     
                    #mando il messaggio di aggiornamento
                    URL='https://api.telegram.org/bot5114308196:AAGBlrtRzOzDczXU5npZg2pAMaTWg1pY_GE/sendMessage'
                    r = requests.get(url = URL, params = {'chat_id':-1001520829278,'text':messaggio})
     
        else: #se l'evento fosse stato presente solo in uno dei due file, lo aggiungo al file mancante per parallelizzare le informazioni
           # print("evento non trovato,aggiungo al file")
            dictionary ={
                        "id" : match['idEvent'],
                        "actions": events,
                        "risultato" : risultato,
                        "state" : stato
                    }
            output.append(dictionary)
            change=True  
     
        i+=1

      
    if change == True: #se ci sono stati nuovi eventi, aggiorno il file
       # print("Sto scrivendo nel polling \n")
        json_object = json.dumps(output, indent = 4)
        with open("polling.json", "w") as outfile:
            outfile.write(json_object)

    insidePolling = False
        

    return



  


def searchMatch():
    global risorsa_occupata 
    
    global insidePolling 
    if insidePolling:#controllo effettuato per evitare di avere più processi in parallelo che lavorano sulla stessa funzione così' da evitare problemi di
                     #concorrenza nella scrittura sui file
        print("sono nel polling non posso cercare risorse")
        return
    
    if risorsa_occupata:
        print("sono nelle risorse non posso cercare risorse")
        return

    risorsa_occupata = True
    #print("insideINIT")
    #settaggi vari di Selenium 
    s=Service("C:\Program Files (x86)\chromedriver-win64\chromedriver.exe")
    options = Options()
    options.add_argument('headless')
    options.add_argument('window-size=2048x1536')
    options.add_argument("--start-maximized")
    options.add_argument("--incognito")
    options.add_argument("--log-level=3")
    driver = webdriver.Chrome(service=s,options=options)
    PATH="https://www.diretta.it/serie-a/" #pagina da cui prendere gli eventi
    print("Diretta scraper  v.1 \nScraping in corso...\n")
    driver.get(PATH)
    page_html = driver.page_source
    page_soup = soup(page_html,features="html.parser")
    containers=page_soup.findAll('div',{'class':'event__match'}) #conservo ogni event__match per le stesse motivazioni spiegate nella relazione
    driver.close() #chiudo la pagina

    # datetime object containing current date and time
    now = datetime.now() 
    # dd/mm/YY H:M:S
    dt_string = now.strftime("%Y-%m-%d %H-%M")
    dataOggi=dt_string[0:dt_string.rfind(' ')]
    orarioOggi=dt_string[dt_string.rfind(' '):len(dt_string)]
    pathPartite="https://www.diretta.it/partita/" #imposto il path delle partite standard a cui deve essere poi concatenato l'id della singola partita (effettuato in riga 448)
    output=[]
    urlPartite=[]
    idPartite=[]   
    messaggio=""
    for event in containers:
        #controllo se l'evento è già iniziato controllando lo stato di diverse informazioni ( come ad esempio il minuto che lampeggia )
        isLive = event.find('svg',{'class':'liveBet-ico'}) or event.find('span',{'class':'blink'}) or (event.find('div',{'class':'event__stage--block'}) and event.find('div',{'class':'event__stage--block'}).getText == "Intervallo")
        idEvento=event.get("id")[event.get("id").rfind('g_1_')+4:len(event.get("id"))] #prendo l'id dell'evento
        home=event.find('div',{'class':'event__participant--home'}).getText() #prendo il nome della squadra di casa
        away=event.find('div',{'class':'event__participant--away'}).getText() #prendo il nome della squadra ospite
        urlPartita=pathPartite+idEvento #creo l'url della partita concatenando il path standard con l'id partita
        p=event.find('div',{'class':'event__time'}) #prendo l'ora o il tempo della partita
        if  (not p) and (not isLive): continue
        if (isLive) :
            p = "iniziata"
        else:
            p=p.getText()

        ##TODO ENABLE FOR PRODUCTION
        if ((p.find('. ') != -1) or (p.find(":") == -1)) and (not isLive) :continue

        ##TODO ENABLE FOR TESTING
        #if (not isLive) :continue


        orarioPartita=p
        #aggiungo tutte le informazioni prese precedentemente ad un dizionario
        dictionary ={
            "idEvent" : idEvento,
            "urlMatch" : urlPartita,
            "home" : home,
            "away" : away,
            "date" : dataOggi,
            "time" : orarioPartita
        }
        output.append(dictionary) #metto le informazioni contenute nel dizionario in un vettore di dizionari
        
        #creo il messaggio informativo
        messaggio+="🔗 Url 🔗\n"+urlPartita+"\n"
        messaggio+="🆚 Match 🆚\n"+home+" - "+away+"\n"
        messaggio+="📆 Date 📆\n "+dataOggi+" "+orarioPartita+"\n\n\n"

    if len(output)==0: #se non ho trovato partite
        messaggio="⚽ Oggi non ci saranno partite ⚽"      
    else: 
        messaggio="⚽ Partite di oggi ⚽\n\n" + messaggio  

    # Serializing json 
    json_object = json.dumps(output, indent = 4) 

    # Writing to sample.json
    #scrivo le partite con i rispettivi meta dati nel file sample.json
    with open("sample.json", "w") as outfile:
        outfile.write(json_object)

    URL='https://api.telegram.org/bot5114308196:AAGBlrtRzOzDczXU5npZg2pAMaTWg1pY_GE/sendMessage'

    if len(messaggio)>4090: #se il messaggio è troppo lungo per essere inviato in una volta sola
        n = 4090
        messages = [messaggio[i:i+n] for i in range(0, len(messaggio), n)]
        for mex in messages:
            #mando il messaggio
            r = requests.get(url = URL, params = {'chat_id':-1001520829278,'text':mex})  

    else:
        #mando il messaggio
        r = requests.get(url = URL, params = {'chat_id':-1001520829278,'text':messaggio})  


    risorsa_occupata = False
    return


schedule.every().day.at("00:00").do(searchMatch)
schedule.every(10).seconds.do(pollingPartite)
while True:
    schedule.run_pending()
    
    
    

