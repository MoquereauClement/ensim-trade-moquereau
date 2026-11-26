# Stratégie de retournement sur le marché ENSIM

Clément Moquereau · TP 2 de Business Intelligence

L’objectif est de faire progresser la valeur totale du portefeuille tout en limitant les reculs depuis ses meilleurs niveaux. La stratégie compare les trois derniers prix de chaque produit pour confirmer un retournement dans une zone d’achat ou après un sommet dans la zone de vente. Sur 371 tours rejoués, elle gagne 11,47 %. Le vendeur aléatoire subit une baisse maximale beaucoup plus faible, ce qui illustre le compromis entre rendement et exposition au marché.

## Règles de décision

Une baisse suivie d’une hausse confirme un creux local. L’achat demande que le prix du rebond soit encore sous le seuil d’achat. Une hausse suivie d’une baisse confirme un sommet local. La vente est déclenchée si le sommet du tour précédent atteint le seuil de vente. Le prix du nouveau tour confirme la baisse. Dans les autres cas, le signal vaut zéro.

- **A** oscille autour d’un niveau relativement stable. La zone d’achat occupe les 15 % inférieurs de l’intervalle entre le minimum et le maximum observés. La zone de vente occupe les 15 % supérieurs.
- **B** oscille malgré une tendance haussière. Les quatre baisses identifiées valent en moyenne 17,4 % et les trois hausses 34,9 %. La cible d’achat est le dernier sommet confirmé multiplié par 0,826. La cible de vente est le dernier creux confirmé multiplié par 1,349.
- **C** oscille malgré une tendance baissière. Les quatorze baisses identifiées valent en moyenne 40,0 % et les quinze hausses 56,5 %. Les coefficients d’achat et de vente sont respectivement 0,600 et 1,565.

Pour B et C, le seuil d’achat est la cible majorée de 3 % et le seuil de vente la cible minorée de 3 %. Le script confirme le sommet ou le creux de référence après une variation inverse de 5 % pour B ou de 10 % pour C. Ces filtres réduisent les changements de référence dus aux petites oscillations. Ils peuvent aussi retarder la prise en compte d’un nouveau cycle.

Le plafond est de dix unités par produit. Les ventes sont limitées au stock. Les achats se partagent le budget dans l’ordre A, B, C et laissent une réserve de 50 au prix observé. Le prix d’exécution du tour suivant peut changer le montant effectivement dépensé.

## Simulation historique

Le portefeuille initial contient 1 000 d’argent et 1 000 unités de chaque produit. Il vaut 17 374 au premier tour. Pour chacun des 370 tours suivants, le script décide avec les données déjà connues et exécute l’ordre au prix publié du tour suivant. Les prix observés restent fixes. Les trois références suivent les distributions publiques du marché, avec 1 000 tirages indépendants de la trajectoire par référence. Le tableau donne les médianes de leurs résultats.

| Stratégie | Valeur finale | Rendement | Baisse maximale |
| --- | ---: | ---: | ---: |
| Stratégie A, B et C | 19 366,65 | +11,47 % | 16,90 % |
| Garder le portefeuille | 18 521,60 | +6,61 % | 17,81 % |
| Trader aléatoire | 17 783,42 | +2,36 % | 18,52 % |
| Acheteur aléatoire | 18 604,31 | +7,08 % | 18,77 % |
| Vendeur aléatoire | 18 081,47 | +4,07 % | 0,54 % |

La stratégie gagne 845,05 de plus que le portefeuille conservé et devance 73,9 % des trajectoires du trader aléatoire. Sur les mêmes tours, l’ancienne règle, qui comparait le prix après la baisse au seuil de vente, donnait 11,59 %. Le vendeur aléatoire sort progressivement du marché et conserve son argent. Sa faible baisse maximale s’accompagne ici d’un rendement inférieur. Les amplitudes de B et C ont été estimées sur les mêmes 371 tours. Ce résultat mesure l’efficacité sur l’historique observé. Seuls les tours suivants permettent de vérifier si elle se maintient.

## Suivi des décisions

Le tableau de bord suit le portefeuille et les trois références à partir du classement officiel. Le rendement observé part de la première valeur publique de Clément et la baisse maximale mesure l’écart le plus élevé entre un sommet et un relevé ultérieur. Les cartes A, B et C donnent le prix, les seuils et le sens de l’ordre. Le journal conserve le tour observé, l’ordre publié et son motif. L’ordre correspond à une demande transmise au marché, dont l’exécution dépend du tour suivant.

Au tour 371, le script calcule trois ordres d’attente. A se trouve sous son seuil d’achat, mais ses derniers prix descendent encore. B rebondit au-dessus de son seuil d’achat. C remonte sans former de creux sur ses trois derniers prix. Ce relevé illustre le rôle de la confirmation et des seuils dans la décision.

Le rejeu du tour 379 de C illustre le changement de règle. Le sommet du tour 378 se situe à 1,3699, au-dessus du seuil de 1,36943. Le prix de 1,3495 au tour 379 confirme la baisse. La nouvelle règle aurait envoyé un ordre de vente après le tour 379, pour exécution au tour 380.

Les données proviennent de [l’historique des prix](https://raw.githubusercontent.com/exofri/ensim-trade-center/main/docs/data/market.json), du [classement officiel](https://raw.githubusercontent.com/exofri/ensim-trade-center/main/docs/data/leaderboard.json) et des [règles d’exécution du marché](https://github.com/exofri/ensim-trade-center/blob/main/scripts/market_tick.py).
