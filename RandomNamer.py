import random

left = [ 	"admiring",
		"adoring",
		"affectionate",
		"agitated",
		"amazing",
		"angry",
		"awesome",
		"beautiful",
		"blissful",
		"bold",
		"boring",
		"brave",
		"busy",
		"charming",
		"clever",
		"cool",
		"compassionate",
		"competent",
		"condescending",
		"confident",
		"cranky",
		"crazy",
		"dazzling",
		"determined",
		"distracted",
		"dreamy",
		"eager",
		"ecstatic",
		"elastic",
		"elated",
		"elegant",
		"eloquent",
		"epic",
		"exciting",
		"fervent",
		"festive",
		"flamboyant",
		"focused",
		"friendly",
		"frosty",
		"funny",
		"gallant",
		"gifted",
		"goofy",
		"gracious",
		"great",
		"happy",
		"hardcore",
		"heuristic",
		"hopeful",
		"hungry",
		"infallible",
		"inspiring",
		"interesting",
		"intelligent",
		"jolly",
		"jovial",
		"keen",
		"kind",
		"laughing",
		"loving",
		"lucid",
		"magical",
		"mystifying",
		"modest",
		"musing",
		"naughty",
		"nervous",
		"nice",
		"nifty",
		"nostalgic",
		"objective",
		"optimistic",
		"peaceful",
		"pedantic",
		"pensive",
		"practical",
		"priceless",
		"quirky",
		"quizzical",
		"recursing",
		"relaxed",
		"reverent",
		"romantic",
		"sad",
		"serene",
		"sharp",
		"silly",
		"sleepy",
		"stoic",
		"strange",
		"stupefied",
		"suspicious",
		"sweet",
		"tender",
		"thirsty",
		"trusting",
		"unruffled",
		"upbeat",
		"vibrant",
		"vigilant",
		"vigorous",
		"wizardly",
		"wonderful",
		"xenodochial",
		"youthful",
		"zealous",
		"zen"]

right = ["antioch", "banksy", "benglis", "bernini", "blue", "bosch", "botero", "botticelli", "bourgeois", "brancusi", "bruegel", "canova", "caravaggio", "cezanne", "cézanne", "dali", "david", "davinci", "degas", "delacroix", "donatello", "duchamp", "elgreco", "friedrich", "ghiberti", "giacometti", "giger", "goya", "gris", "hamilton", "hokusai", "homer", "houdon", "johns", "judson", "kahlo", "kandinsky", "kinkade", "klee", "lewis", "lollobrigida", "maar", "manet", "matisse", "michalangelo", "mondrian", "monet", "montgomery", "okeeffe", "picasso", "pollock", "praxiteles", "quinn", "raphael", "rembrandt", "rodin", "rothko", "rouseau", "rubens", "sargent", "smith", "tapies", "thorvaldsen", "titian", "vaneyck", "vangogh", "vermeer", "warhol", "waterhouse", "whistler", "whiteread", "wood"]

class RandomNamer:
	def getName():
		return "{}_{}".format(random.choice(left), random.choice(right))
