from scrapy.spider import BaseSpider
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.selector import HtmlXPathSelector
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor

from scrapy.item import Item, Field

class IcfidnetItem(Item):
    # define the fields for your item here like:
    fullname = Field()
    mandats = Field()
    pass

class MandatItem(Item):
	groupe = Field()
	code = Field()
	decision = Field()
	statut = Field()
	pass

class MyspyderSpider(CrawlSpider):
	name = "myspyder"
	allowed_domains = ["icfidnet.ansm.sante.fr"]
	start_urls = ('https://icfidnet.ansm.sante.fr/Public/memb_idx.php',)

	rules = [ Rule(SgmlLinkExtractor(allow='membre.php', restrict_xpaths=("/html//a[@class='ifides']")),
					follow=False,
					callback='parse_member') ]

	def mandat(self, mrow):
		grp_node = mrow.select("td[1]")

		if len(grp_node.select("a").extract()) == 0:
			r = mrow.select("td/text()").extract()
			return MandatItem(groupe=r[0], code=r[1], decision=r[2], statut=r[3])
		else:
			a = mrow.select("td/a/text()").extract()[0]
			r = mrow.select("td/text()").extract()
			return MandatItem(groupe=a, code=r[0], decision=r[1], statut=r[2])

	def extract_mandats(self, hxs):
		mandat_rows = hxs.select("/html/body/table[5]/tr")
		mandats = [ self.mandat(mrow) for idx, mrow in enumerate(mandat_rows) ]

		return mandats[1:]


	def parse_member(self, response):
		hxs = HtmlXPathSelector(response)

		fullname = hxs.select("/html/body/h3/text()").extract()[0]
		mandats = self.extract_mandats(hxs)

		i = IcfidnetItem(fullname=fullname, mandats=mandats)

		return i