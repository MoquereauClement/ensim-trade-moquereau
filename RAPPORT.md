# Stratégie de retournement sur le marché ENSIM

Clément Moquereau · TP 2 de Business Intelligence

L’objectif est de faire progresser la valeur totale du portefeuille tout en limitant les reculs depuis ses meilleurs niveaux. La stratégie compare les trois derniers prix de chaque produit pour confirmer un retournement dans une zone d’achat ou après un sommet dans la zone de vente. Sur 371 tours rejoués, elle gagne 75,61 % avec une marge commune de 7 % et des ordres de 100 unités au maximum. Le vendeur aléatoire subit une baisse maximale beaucoup plus faible, ce qui illustre le compromis entre rendement et exposition au marché.

## Règles de décision

Une baisse suivie d’une hausse confirme un creux local. L’achat demande que le prix du rebond soit encore sous le seuil d’achat. Une hausse suivie d’une baisse confirme un sommet local. La vente est déclenchée si le sommet du tour précédent atteint le seuil de vente. Le prix du nouveau tour confirme la baisse. Dans les autres cas, le signal vaut zéro.

- **A** oscille autour d’un niveau relativement stable. La cible d’achat est son plus bas observé et la cible de vente son plus haut observé.
- **B** oscille malgré une tendance haussière. Les quatre baisses identifiées valent en moyenne 17,4 % et les trois hausses 34,9 %. La cible d’achat est le dernier sommet confirmé multiplié par 0,826. La cible de vente est le dernier creux confirmé multiplié par 1,349.
- **C** oscille malgré une tendance baissière. Les quatorze baisses identifiées valent en moyenne 40,0 % et les quinze hausses 56,5 %. Les coefficients d’achat et de vente sont respectivement 0,600 et 1,565.

Pour les trois produits, le seuil d’achat est la cible majorée de 7 % et le seuil de vente la cible minorée de 7 %. Pour les cycles de B et C, le script confirme le sommet ou le creux de référence après une variation inverse de 5 % pour B ou de 10 % pour C. Ces filtres réduisent les changements de référence dus aux petites oscillations. Ils peuvent aussi retarder la prise en compte d’un nouveau cycle.

Le plafond est de 100 unités par produit et par tour. Les ventes sont limitées au stock. Les achats se partagent le budget dans l’ordre A, B, C et laissent une réserve de 50 au prix observé. Le prix d’exécution du tour suivant peut changer le montant effectivement dépensé.

## Simulation historique

Le portefeuille initial contient 1 000 d’argent et 1 000 unités de chaque produit. Il vaut 17 374 au premier tour. Pour chacun des 370 tours suivants, le script décide avec les données déjà connues et exécute l’ordre au prix publié du tour suivant. Les prix observés restent fixes. Les trois références suivent les distributions publiques du marché, avec 1 000 tirages indépendants de la trajectoire par référence. Le tableau donne les médianes de leurs résultats.

| Stratégie | Valeur finale | Rendement | Baisse maximale |
| --- | ---: | ---: | ---: |
| Stratégie actuelle, marge de 7 %, 100 unités max. | 30 509,64 | +75,61 % | 13,62 % |
| Anciens seuils, 100 unités max. | 26 853,44 | +54,56 % | 12,64 % |
| Anciens seuils, 10 unités max. | 19 366,65 | +11,47 % | 16,90 % |
| Garder le portefeuille | 18 521,60 | +6,61 % | 17,81 % |
| Trader aléatoire | 17 783,42 | +2,36 % | 18,52 % |
| Acheteur aléatoire | 18 604,31 | +7,08 % | 18,77 % |
| Vendeur aléatoire | 18 081,47 | +4,07 % | 0,54 % |

Sur cet historique, la marge commune de 7 % déclenche davantage d’ordres que les anciens seuils et augmente le rendement simulé. La baisse maximale augmente également. La simulation recalcule l’ordre à chaque tour. En pratique, le marché peut relire un ordre si le bot tarde à le remplacer, ce qui amplifie aussi l’exposition. Le vendeur aléatoire sort progressivement du marché et conserve son argent. Sa faible baisse maximale s’accompagne ici d’un rendement inférieur. Les amplitudes de B et C, la taille d’ordre et les marges ont été évaluées sur les mêmes 371 tours. Seuls les tours suivants permettent de vérifier si les résultats se maintiennent.

## Suivi des décisions

Le tableau de bord suit le portefeuille et les trois références à partir du classement officiel. Le rendement observé part de la première valeur publique de Clément et la baisse maximale mesure l’écart le plus élevé entre un sommet et un relevé ultérieur. Les cartes A, B et C donnent le prix, les seuils et le sens de l’ordre. Le journal conserve le tour observé, l’ordre publié et son motif. L’ordre correspond à une demande transmise au marché, dont l’exécution dépend du tour suivant.

Au tour 371, le script calcule trois ordres d’attente. A se trouve sous son seuil d’achat, mais ses derniers prix descendent encore. B rebondit au-dessus de son seuil d’achat. C remonte sans former de creux sur ses trois derniers prix. Ce relevé illustre le rôle de la confirmation et des seuils dans la décision.

Le rejeu du tour 379 de C illustre l’effet de la confirmation. Le sommet du tour 378 se situe à 1,3699, au-dessus du seuil de vente. Le prix de 1,3495 au tour 379 confirme la baisse. La règle actuelle aurait envoyé un ordre de vente après le tour 379, pour exécution au tour 380.

Les données proviennent de [l’historique des prix](https://raw.githubusercontent.com/exofri/ensim-trade-center/main/docs/data/market.json), du [classement officiel](https://raw.githubusercontent.com/exofri/ensim-trade-center/main/docs/data/leaderboard.json) et des [règles d’exécution du marché](https://github.com/exofri/ensim-trade-center/blob/main/scripts/market_tick.py).
