#!/usr/bin/env python3
"""Chiffres de la semaine pour l'agent du lundi : ORGANIQUE d'abord (Mehdi 20/11), puis les pubs.
Pas de clé : l'agent lit Supabase (projet PPC) avec le connecteur claude.ai du login root, en LECTURE SEULE
(hook lecture_seule.py). Ce module donne seulement les requêtes et la règle de lecture.
"""
PROJET = "zbpvlcqfzanjflabpggf"
SEUIL_COUPE = 12  # $ dépensés sans candidature (règle Dakota 12-14 $)
OUTILS = ["mcp__claude_ai_Supabase__execute_sql"]

ORGANIQUE = """select p.media_id, p.title, p.published_at, p.permalink,
  count(c.ig_id) filter (where c.lead_id is not null) as leads,
  coalesce(sum(c.n_comments), 0) as commentaires, count(c.ig_id) as contacts
from public.ppc_ig_posts p left join public.ppc_ig_contacts c on c.first_media_id = p.media_id
where p.media_id is not null
group by 1, 2, 3, 4 order by leads desc, commentaires desc limit 40"""

SITE = """select utm_source, utm_campaign, utm_content, count(*) as leads
from public.ppc_leads where created_at > now() - interval '30 days'
group by 1, 2, 3 order by leads desc limit 30"""

PUBS = f"""select entity_type, meta_entity_id, round(sum(spend)::numeric, 2) as depense,
  sum(applications_submitted) as candidatures, sum(qualified_leads) as qualifies
from public.meta_daily_insights where date >= current_date - 7
group by 1, 2 order by depense desc limit 30"""


def resume() -> str:
    return (
        "CHIFFRES (organique d'abord) : lis Supabase avec mcp__claude_ai_Supabase__execute_sql, "
        f"project_id « {PROJET} », LECTURE SEULE (une requête SELECT par appel, le reste est bloqué).\n"
        f"1. Leads organiques par reel Instagram :\n{ORGANIQUE}\n"
        f"2. Leads du site par source (30 jours) :\n{SITE}\n"
        f"3. Pubs Meta 7 jours :\n{PUBS}\n"
        "Lecture : un Pixar part d'abord en ORGANIQUE ; ceux qui ramènent le plus de leads organiques sont proposés à Mehdi "
        f"pour un test en publicité (rien n'est publié automatiquement). Pub à couper : ≥ {SEUIL_COUPE} $ sans candidature.\n"
        "Relie chaque reel (title) à son histoire dans kit-pixar-v1/2-style/registre-histoires.md et mets à jour ses chiffres. "
        "Si Supabase ne répond pas : écris « chiffres indisponibles » et continue."
    )


if __name__ == "__main__":
    print(resume())
