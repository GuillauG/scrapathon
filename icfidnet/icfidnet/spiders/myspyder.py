from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.selector import HtmlXPathSelector
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor

from scrapy.item import Item, Field

class IcfidnetItem(Item):
    fullname = Field()
    mandats = Field()
    declarations = Field()
    pass

class MandatItem(Item):
	groupe = Field()
	code = Field()
	decision = Field()
	statut = Field()
	pass

class DeclarationItem(Item):
	date = Field()
	content = Field()
	pass

class DeclarationContentItem(Item):
	typ = Field()
	entreprise = Field()
	activite = Field()
	participation = Field()
	periode = Field()
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

	def make_declaration(self, hnode, dnode):
		header = hnode.select("tr/td/b/text()").extract()[0]
		decl_rows = dnode.select("tr[position() >= 2]")

		def from_row(decl_row):
			decl = decl_row.select("td")
			l = len(decl)
			
			if l <= 1:
				# Declaration est "Neant (declaration d'absence de liens)"
				return DeclarationItem(date=header, content=None)
			else:
				# Declaration non vide

				# recupere le type et l'entreprise declaree
				typ = decl_row.select("td[1]/a/b/text()").extract()[0]
				ent = decl_row.select("td[2]/b/text()").extract()[0]
				
				# autres champs : activite/produits, participation/remun et periode
				r = decl_row.select("td[position() > 2]/text()").extract()

				# si la particpation n'est pas mentionnee
				if len(r) == 2:
					act, part, peri = r[0], "unkown", r[1]
				# si la particpation est mentionnee
				else:
					act, part, peri = r[0], r[1], r[2]
				
				dContent = DeclarationContentItem(typ=typ, entreprise=ent, activite=act, participation=part, periode=peri)
				return DeclarationItem(date=header, content=dContent)


		return [ from_row(decl_row) for i, decl_row in enumerate(decl_rows) ]

	def extract_declaration(self, hxs):
		decls = hxs.select("/html/body/table[@width='80%']") # remove mandats

		# pages ou liens declares est "AUCUN DECLARATION N A ETE ENREGISTREE DANS FIDES"
		if len(decls) == 3:
			return

		grps = [ (decls[i], decls[i+1]) for i, d in enumerate(decls) if (i % 2 == 0) & (i > 1)]

		return [ self.make_declaration(hnode, dnode) for hnode, dnode in grps ]


	def parse_member(self, response):
		hxs = HtmlXPathSelector(response)

		fullname = hxs.select("/html/body/h3/text()").extract()[0]
		mandats = self.extract_mandats(hxs)
		declarations = self.extract_declaration(hxs)

		return IcfidnetItem(fullname=fullname, mandats=mandats, declarations=declarations)