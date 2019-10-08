import pickle

import tabulate

from scraper import VeranstaltungsScraper

filehandler = open('modules_2.obj', 'rb')
modules = pickle.load(filehandler)

filehandler = open('lsf.obj', 'rb')
lsf = pickle.load(filehandler)

def happens_on_day(id, check_day):
    name, sws, dates = lsf[id]
    for (day, rythm, from_time, to_time, from_date, to_date, room) in dates:
        if day == check_day:
            return True
    return False

def get_things_for_day(day):
    l = []
    for key in lsf:
        if happens_on_day(key, day):
            l.append(key)
    return l

def module_for_key(key):
    for m in modules:
        if key in modules[m][2]:
            return m

def print_dates(dates):
    print(tabulate.tabulate(dates))

def print_day(day):
    l = get_things_for_day(day)
    for v in l:
        name, sws, dates = lsf[v]
        module = module_for_key(v)
        print(f'Veranstaltung {name} ({v})')
        if module:
            print(f'gehört zu {modules[module][0]}')
        else:
            print(f'keine Zugehörigkeit gefunden')
        print_dates(dates)
        if module:
            url = f'https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?number={module}&version={modules[module][1]}&sprache=1'
            print(f'Zum Modul: {url}')
        vid = '+'.join(v.split(' '))
        print(f'Zum LSF: http://www.lsf.tu-berlin.de/qisserver/servlet/de.his.servlet.RequestDispatcherServlet?state=wsearchv&search=1&subdir=veranstaltung&choice.veranstaltung.semester=y&veranstaltung.semester=20192&veranstaltung.veranstnr={vid}&P_start=0&P_anzahl=999&P.sort=veranstaltung.veranstnr&_form=display')
        print('\n\n\n')
print_day('Freitag')