"""Cartes motion (cards.py, validées anti-gourou 20/11) : une toutes les 10-15 s sur les pubs longues. Vérifie que chaque mot déclencheur existe."""
import json
B = lambda o: [("LE DEAL", "Je prends *10 %*", "10%", 20 + o), ("ATTENTION", "Ghir *3 tal 5* f chhar", "ghir", 52 + o), ("6 SNIN", "Business khddam *6 snin*", "6", 60 + o)]
C = {"i0356": B(0), "v2": B(-2.2), "v3": B(1.7),
 "i0358": [("FORMATION", "*10 000 dh* w dber rassek", "10000", 7), ("BLA FORMATION", "Formation *fabor*", "formation", 16.5), ("LE DEAL", "Je prends *10 %*", "10%", 38), ("CONDITION", "*Budget pub* obligatoire", "budget", 46)],
 "tof1": [("2026", "*1 seule* source de revenu", "masdar", 4), ("HIGH TICKET", "Produits *+100 $*", "100", 28), ("BLA STOCK", "Fournisseur *kaysifet*", "fournisseur", 36), ("LE DEAL", "Je prends *10 %*", "10%", 61), ("ATTENTION", "Ghir *3 tal 5* f chhar", "ghir", 65)],
 "i0360": [("MACHI", "*Trading*, *COD*, crypto", "trading", 10.5), ("L'BUSINESS", "E-com *high ticket*", "high", 46), ("BLA STOCK", "Client *kikhelles b carte*", "carte", 57), ("LE DEAL", "Je prends *un %*", "pourcentage", 79), ("ATTENTION", "*3 à 5* personnes / mois", "3", 86)],
 "tof3": [("SAB9O", "E-commerce *f 2016*", "2016", 14), ("L'FORSA", "E-com *high ticket*", "high", 25), ("BLA STOCK", "Client *kikhelles b carte*", "carte", 34), ("LE DEAL", "Je prends *10 %*", "10%", 44.5)],
 "tof4": [("PLAN DYAL WALIDIN", "9ra, khedma, *sber 30 3am*", "30", 2.5), ("2026", "*T'adapta* wla ydouz t-train", "ghaydouz", 23), ("HIGH TICKET", "Produits *+100 $*", "100", 29.5), ("LE DEAL", "Je prends *10 %*", "10%", 51)],
 "x99": [("FORMATION", "Mor l khlass : *bo7dek*", "bo7dek", 8.5), ("BLA FORMATION", "Business *fabor*", "fabor", 21), ("HIGH TICKET", "Produits *+100 $*", "100", 27), ("LE DEAL", "Je prends *10 %*", "10%", 35)],
 "xq": [("SOU2AL WA7ED", "Ch7al dkhelti mn *l business* ?", "ch7al", 4), ("FORMATION", "Ghir *l ma3louma*", "lma3louma", 31), ("LE DEAL", "Je prends *10 %*", "10%", 51), ("L'MASLA7A", "*Nefs l maslaha*", "lmasla7a", 60.5), ("ATTENTION", "Ghir *3 tal 5* f chhar", "ghir", 66.5)],
 "xf": [("FORMATION", "Ghir *l ma3louma*", "lma3louma", 11), ("SUIVI", "*Appels vidéo* f ga3 les étapes", "appels", 17), ("LE DEAL", "Je prends *10 %*", "10%", 23), ("ATTENTION", "Ghir *3 tal 5* f chhar", "ghir", 32)]}
for n, cs in C.items():
    W = [w for g in json.load(open(f"{n}_g.json")) for w in g["words"]]
    out = []
    for kick, txt, tok, t in cs:
        N = lambda x: x.lower().strip(".,?!").replace("-", "").replace("ou", "o")
        hit = sorted((w for w in W if N(w["w"]).startswith(N(tok)) and abs(w["start"] - t) < 8), key=lambda w: abs(w["start"] - t))
        if not hit: print("MANQUE", n, tok, t); continue
        out.append({"type": "card", "kick": kick, "lines": [[txt.replace("*", ""), hit[0]["w"].lower().strip(".,?!"), hit[0]["start"]]], "hold": 2.0})
    json.dump(out, open(f"{n}_anim.json", "w"), ensure_ascii=False); print(n, len(out))
