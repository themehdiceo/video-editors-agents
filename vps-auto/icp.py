#!/usr/bin/env python3
"""Garde-fou ICP BLOQUANT (Mehdi 2026-11-24, après le Pixar « réparateur de machines »).

verifier_metier(histoire, legende="") -> (ok, raison). Appelé AVANT planche, vidéo et mise en file Instagram.
L'histoire doit déclarer « metier: … » dans son frontmatter. Absent, hors liste ou interdit = refus (0 crédit).
Liste unique : vps-auto/icp_metiers.json.
  icp.py FICHIER.md [...]   -> OK/REFUS par histoire (code 1 si un refus)
  icp.py --test             -> auto-test
"""
import json, re, sys, unicodedata
from pathlib import Path

LISTE = Path(__file__).with_name("icp_metiers.json")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s).lower().replace("’", "'"))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"\(.*?\)", " ", s)  # « comptable (F, Meknès) » -> « comptable »
    return " ".join(s.split()).strip(" .,;:-")


def _frontmatter(txt: str) -> dict:
    m = re.match(r"---\n(.*?)\n---", txt, re.S)
    fm = {}
    for l in (m.group(1).splitlines() if m else []):
        if ":" in l:
            k, v = l.split(":", 1)
            fm[k.strip()] = v.strip().strip("\"'")
    return fm


def _hook(txt: str) -> str:
    """Ligne de la scène 1 (le hook) : c'est elle que Mehdi voit en premier."""
    for l in txt.splitlines():
        if re.match(r"\|\s*1\s*\|", l) or "HOOK" in l:
            return l
    return ""


def classer(metier: str) -> str:
    """'autorise' | 'rare' | 'interdit' | 'inconnu'"""
    L = json.loads(LISTE.read_text())
    m = _norm(metier)
    m = _norm(L["alias"].get(m, next((v for k, v in L["alias"].items() if _norm(k) == m), m)))
    if m in {_norm(x) for x in L["autorises"]}:
        return "autorise"
    if m in {_norm(x) for x in L["rares"]}:
        return "rare"
    if m in {_norm(x) for x in L["interdits"]}:
        return "interdit"
    return "inconnu"


def _rares_recents(histoire: Path, n: int = 49) -> int:
    """Rares parmi les n histoires précédentes (tous les dossiers pixar-nuit, ordre des noms), refusées exclues."""
    racine = histoire.parent.parent if histoire.parent.parent.name == "pixar-nuit" else histoire.parent
    autres = sorted((p for p in racine.rglob("*.md") if p.name < histoire.name and "refus" not in str(p)), key=lambda p: p.name)
    return sum(classer(_frontmatter(p.read_text()).get("metier", "")) == "rare" for p in autres[-n:])


def verifier_metier(histoire, legende: str = "") -> tuple[bool, str]:
    h = Path(histoire)
    try:
        txt = h.read_text()
    except OSError as e:
        return False, f"histoire illisible ({e})"
    L = json.loads(LISTE.read_text())
    metier = _frontmatter(txt).get("metier", "")
    if not metier:
        return False, "« metier: » absent du frontmatter"
    c = classer(metier)
    if c in ("interdit", "inconnu"):
        return False, f"métier « {metier} » {'interdit' if c == 'interdit' else 'hors liste'} (ICP)"
    zone = _norm(_hook(txt) + " " + legende)
    for mot in L["mots_interdits"]:
        if re.search(r"\b" + re.escape(_norm(mot)), zone):
            return False, f"hook/légende parle de « {mot} » (métier hors ICP)"
    if c == "rare" and _rares_recents(h) >= L["rares_max_sur_50"]:
        return False, f"métier rare « {metier} » : déjà {L['rares_max_sur_50']} sur les 50 dernières histoires"
    return True, f"métier « {metier} » {'rare' if c == 'rare' else 'autorisé'}"


def _test() -> None:
    import tempfile
    d = Path(tempfile.mkdtemp()) / "pixar-nuit" / "histoires-validees"
    d.mkdir(parents=True)
    def h(nom, metier, hook="| 1 | x | v | Kan5dem f lbureau |"):
        p = d / nom
        p.write_text(f"---\ntitre: t\n{'metier: ' + metier if metier else ''}\n---\n\n{hook}\n")
        return p
    assert not verifier_metier(h("a1.md", "réparateur de machines"))[0]
    assert not verifier_metier(h("a2.md", "technicien de maintenance"))[0]
    assert not verifier_metier(h("a3.md", ""))[0]
    assert not verifier_metier(h("a4.md", "astronaute"))[0]
    assert not verifier_metier(h("a5.md", "livreur"))[0]
    assert verifier_metier(h("b1.md", "comptable"))[0]
    assert verifier_metier(h("b2.md", "Infirmière (F, Rabat)"))[0]
    assert verifier_metier(h("b3.md", "chef d'équipe en usine", "| 1 | x | v | Adam m'a tout préparé |"))[0]
    assert not verifier_metier(h("b4.md", "chef d'équipe en usine", "| 1 | x | v | je répare 30 machines par jour |"))[0]
    assert not verifier_metier(h("b5.md", "comptable"), legende="Il répare 30 machines par jour")[0]
    assert verifier_metier(h("c1.md", "policier"))[0]
    assert not verifier_metier(h("c2.md", "militaire"))[0]  # 2e rare sur 50 = refus
    print("icp.py : test OK (réparateur refusé, comptable accepté, rares 1/50)")


if __name__ == "__main__":
    if sys.argv[1:] == ["--test"]:
        _test()
        sys.exit(0)
    ko = 0
    for f in sys.argv[1:]:
        ok, r = verifier_metier(f)
        ko += not ok
        print(f"{'OK   ' if ok else 'REFUS'} {Path(f).name} : {r}")
    sys.exit(1 if ko else 0)
