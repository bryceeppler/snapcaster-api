from rest_framework.views import APIView
from rest_framework.response import Response
from .scrapers.singleScrapers.GauntletScraper import GauntletScraper
from .scrapers.singleScrapers.HouseOfCardsScraper import HouseOfCardsScraper
from .scrapers.singleScrapers.KanatacgScraper import KanatacgScraper
from .scrapers.singleScrapers.FusionScraper import FusionScraper
from .scrapers.singleScrapers.Four01Scraper import Four01Scraper
import concurrent.futures
from rest_framework import status
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
    results = []
    tempResults = []
    def transform(self, scraper):
        scraper.scrape()
        cardList = scraper.getResults() # a list of card objects

        # get the cheapest card from the list
        cheapestPrice = 100000
        cheapestCard = None
        for card in cardList:
            # check if it has the cheapest condition in stock
            for condition in card['stock']:
                if condition[1] < cheapestPrice:
                    cheapestPrice = condition[1]
                    cheapestCard = card

        self.tempResults.append(cheapestCard)     
        return

    def post(self, request):
        """
        Given a list of card names, and a list of websites,
        get the cheapest price of each card across the provided
        stores.
        """
        # get request body as json
        body = json.loads(request.body.decode('utf-8'))

        # a list of websites to scrape
        websites = body['websites']

        # a list of card names to scrape
        cardNames = body['cardNames']

        for cardName in cardNames:
            # strip any prefixed numbers from the card name
            cardName = re.sub(r'^\d+\s', '', cardName)

            # a list of scrapers to run
            scrapers = []

            # create a scraper for each website and add it to the list
            if 'gauntlet' in websites:
                scrapers.append(GauntletScraper(cardName))
            if 'houseoOfCards' in websites:
                scrapers.append(HouseOfCardsScraper(cardName))
            if 'kanatacg' in websites:
                scrapers.append(KanatacgScraper(cardName))
            if 'fusion' in websites:
                scrapers.append(FusionScraper(cardName))
            if 'four01' in websites:
                scrapers.append(Four01Scraper(cardName))

            # run each scraper in a thread
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                results = executor.map(self.transform, scrapers)

            # if no results, continue
            if len(self.tempResults) == 0:
                continue

            # get the cheapest catd
            cheapestCard = None
            cheapestPrice = 100000

            for card in self.tempResults:
                # check if it has the cheapest condition in stock
                try:
                    for condition in card['stock']:
                        if condition[1] < cheapestPrice:
                            cheapestPrice = condition[1]
                            cheapestCard = card.copy()
                except TypeError:
                    pass

            self.results.append(cheapestCard)
            self.tempResults.clear()



        data = self.results.copy()
        self.results.clear()
        return Response(data)
