import pickle

from scraper import VeranstaltungsScraper

x = VeranstaltungsScraper()

mods = x.all_modules()
lsf = x.all_lsf()

f1 = open('modules.obj', 'wb')
pickle.dump(mods, f1)

f2 = open('lsf.obj', 'wb')
pickle.dump(lsf, f2)

print("done")
