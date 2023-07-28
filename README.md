# DirettaScraper ⚽📋

## Technologies 📡
<p align="center">
    <img width="250" height="250" src="https://i.postimg.cc/hv65ZXr4/py.png">
    <img width="250" height="250" src="https://i.postimg.cc/prh0j2tw/Selenium-Logo.png">
</p>

## API 🐝
DirettaScraper uses Twitter API to take all the tweet about a target football game and Telegram API to post real time game results.

## How DirettaScraper works
### Scraping and polling
DirettaScraper born by the necessity to have real-time telegram bot that post information about Seria A football games. 
The scraper works on diretta.it, a site that give real time football game results. Every game has a dedicated page with this structure: https://www.diretta.it/game/gameID.
So scraping made by Selenium starts every day at 00:00 CEST with the goal to save in a "sample.json" file all the Seria A games that are played in that day.
There is an example of the game representation in the sample.json file:
<p align="center"><img src="https://i.postimg.cc/cCddX5F4/Immagine1.jpg"></p>
When the scrape end, a message with those information will be sent by the telegram bot:
<p align="center"><img src="https://i.postimg.cc/d1x99zsG/Immagine2.jpg"></p>

After that, the bot will check every 10 seconds if there is a new event for all the games scraped in the previous phase.When a new event appears, bot will write under the corresponding game 
in the "polling.json" file the new event (represented by the actions array) :
<p align="center"><img src="https://i.postimg.cc/BbsPGpnX/Immagine3.jpg"></p>

Analyzing this image we can notice that:
- Id represents the id of the game;
- Actions represents all the event of the game, like a Yellow Card, Goal, End of the first half, etc. ;
- Risultato represents the current result;
- State respresents a combination of current half + minutes of the game.

After the polling.json file is updated, a message will notify in the telegram bot:

<p align="center"><img src="https://i.postimg.cc/8PFc0sG2/Immagine6.jpg"></p>

### Sentiment Analysis
After the end of a game, bot will start a scrape of all the tweets posted in Twitter from the start of the game till the end. Scrape is made by the tweepy lib and the sentiment analysis is done by VADER.
The results will be shown as below:
<p align="center"><img src="https://i.postimg.cc/V6dPkrK1/Immagine5.jpg"></p>

## Usage

- To run the project: py main.py
- To change the target championship (default one is Serie A), search the interested link on diretta.it and assign it to "PATH" variable inside the code
- Remember to change the chrome driver path with your own (for the variable s of the Service)!
 


# Author 💻 👦
DirettaScraper has been developed by Claudio Caudullo, Computer Science student at Department of Mathematics and Computer Science, University of Catania, Italy. 

Email: claudiocaudullo01@gmail.com
