from .scrapers.singleScrapers.GauntletScraper import GauntletScraper
from .scrapers.singleScrapers.HouseOfCardsScraper import HouseOfCardsScraper
from .scrapers.singleScrapers.KanatacgScraper import KanatacgScraper
from .scrapers.singleScrapers.FusionScraper import FusionScraper
from .scrapers.singleScrapers.Four01Scraper import Four01Scraper
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
                if "Default" in condition[0]:
                    print('bugged website' + card['website'])
                    print('condition should not be '+condition[0])
                    print('card link is '+card['link'])
                if condition[0] not in self.conditionDict.keys():
                    continue
                if self.conditionDict[condition[0]] <= self.worstCondition:
                    if condition[1] < cheapestPrice:
                        cheapestPrice = condition[1]
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
                conditionCode = condition[0]
                if conditionCode not in self.conditionDict.keys():
                    continue
                if self.conditionDict[condition[0]] <= self.worstCondition:
                    if condition[1] < cheapestPrice:
                        cheapestPrice = condition[1]
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