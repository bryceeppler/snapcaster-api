from .scrapers.singleScrapers.GauntletScraper import GauntletScraper
from .scrapers.singleScrapers.HouseOfCardsScraper import HouseOfCardsScraper
from .scrapers.singleScrapers.KanatacgScraper import KanatacgScraper
from .scrapers.singleScrapers.FusionScraper import FusionScraper
from .scrapers.singleScrapers.Four01Scraper import Four01Scraper

from .scrapers.singleScrapersV2.GauntletScraper import GauntletScraper as GauntletScraperV2
from .scrapers.singleScrapersV2.HouseOfCardsScraper import HouseOfCardsScraper as HouseOfCardsScraperV2
from .scrapers.singleScrapersV2.KanatacgScraper import KanatacgScraper as KanatacgScraperV2
from .scrapers.singleScrapersV2.FusionScraper import FusionScraper as FusionScraperV2
from .scrapers.singleScrapersV2.Four01Scraper import Four01Scraper as Four01ScraperV2

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
import concurrent.futures
import json
import re




# Create your views here.
class ping(APIView):
    def get(self, request):
        return Response(status=status.HTTP_200_OK)

class getPrice(APIView):
    results = []

    def transform(self, scraper):
        scraper.scrape()
        self.results.append(scraper.getResults())
        return

    def get(self, request):
        """
        Given the name of a card as a query paramater,
        get the price of a card across all stores.
        """
        # get "name" parameter from request
        name = request.GET.get('name')

        houseOfCardsScraper = HouseOfCardsScraper(name)
        gauntletScraper = GauntletScraper(name)
        kanatacgScraper = KanatacgScraper(name)
        fusionScraper = FusionScraper(name)
        four01Scraper = Four01Scraper(name)

        scrapers = [
            houseOfCardsScraper,
            gauntletScraper,
            kanatacgScraper,
            fusionScraper,
            four01Scraper
        ]

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = executor.map(self.transform, scrapers)

        data = self.results.copy()
        self.results.clear()
        return Response(data)

class getBulkPrice(APIView):
    worstCondition = 3
    conditionDict = {
        'NM': 0,
        'LP': 1,
        'MP': 2,
        'HP': 3,
    }
    def scraperThread(self, scraper):
        """
        Returns the cheapest price of a card from a single store.
        """
        scraper.scrape()
        cardList = scraper.getResults() # a list of card objects
        # get the cheapest card from the list
        cheapestPrice = 100000
        cheapestCard = None
        for card in cardList:
            # check if it has the cheapest condition in stock
            for condition in card['stock']:
                if "Default" in condition['condition']:
                    print('bugged website' + card['website'])
                    print('condition should not be '+condition['condition'])
                    print('card link is '+card['link'])
                if condition['condition'] not in self.conditionDict.keys():
                    continue
                if self.conditionDict[condition['condition']] <= self.worstCondition:
                    if condition['price'] < cheapestPrice:
                        cheapestPrice = condition['price']
                        cheapestCard = card

        return  cheapestCard

    def cardThread(self, cardName):
        """
        Returns the cheapest price of a card across all stores.
        """
        # create scrapers
        scrapers = []
        if 'gauntlet' in self.websites:
            scrapers.append(GauntletScraper(cardName))
        if 'houseoOfCards' in self.websites:
            scrapers.append(HouseOfCardsScraper(cardName))
        if 'kanatacg' in self.websites:
            scrapers.append(KanatacgScraper(cardName))
        if 'fusion' in self.websites:
            scrapers.append(FusionScraper(cardName))
        if 'four01' in self.websites:
            scrapers.append(Four01Scraper(cardName))

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = executor.map(self.scraperThread, scrapers)
            # results now has the cheapest price from each store

        # filter through results to find the cheapest card
        cheapestPrice = 100000
        cheapestCard = None
    
        for card in results:
            try:
                name = card['name']
                stock = card['stock']
                if "Art Card" in name:
                    continue
                elif "Art Series" in name:
                    continue
            except:
                continue

            for condition in stock:
                conditionCode = condition['condition']
                if conditionCode not in self.conditionDict.keys():
                    continue
                if self.conditionDict[condition['condition']] <= self.worstCondition:
                    if condition['price'] < cheapestPrice:
                        cheapestPrice = condition['price']
                        cheapestCard = card

        return cheapestCard

    
    def post(self, request):
        body = json.loads(request.body.decode('utf-8'))
        self.websites = body['websites']
        cardNameList = [re.sub(r'^\d+\s', '', cardName) for cardName in body['cardNames']]
        
        # worst acceptable condition as an int
        try:
            self.worstCondition = self.conditionDict[body['condition']]
        except:
            self.worstCondition = 4


        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = executor.map(self.cardThread, cardNameList, timeout=20)

        cheapestCards = list(results)
        return Response(cheapestCards, status=status.HTTP_200_OK)
        

class getPriceV2(APIView):
    results = []

    def transform(self, scraper):
        scraper.scrape()
        self.results.append(scraper.getResults())
        return

    def get(self, request):
        # with open('./api/dummyresponse.json') as f:
        #     data = json.load(f)
        # return Response(data)
        """
        Given the name of a card as a query paramater,
        get the price of a card across all stores.
        """
        # get "name" parameter from request
        name = request.GET.get('name')

        houseOfCardsScraper = HouseOfCardsScraperV2(name)
        gauntletScraper = GauntletScraperV2(name)
        kanatacgScraper = KanatacgScraperV2(name)
        fusionScraper = FusionScraperV2(name)
        four01Scraper = Four01ScraperV2(name)

        scrapers = [
            houseOfCardsScraper,
            gauntletScraper,
            kanatacgScraper,
            fusionScraper,
            four01Scraper
        ]

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = executor.map(self.transform, scrapers)

        data = self.results.copy()
        self.results.clear()
        
        # post processing to join arrays
        data = [item for sublist in data for item in sublist]

        # formattedData will have an object for every card condition, eliminating the stock list
        formattedData = []
        for card in data:
            for condition in card['stock']:
                formattedData.append({
                    'name': card['name'],
                    'price': condition['price'],
                    'condition': condition['condition'],
                    'link': card['link'],
                    'website': card['website'],
                    'set': card['set'],
                    'image': card['image']
                })

        # add an id to every json object in data
        for i in range(len(formattedData)):
            formattedData[i]['id'] = i

        return Response(formattedData)