# SER Guides — état réel du système

Dernière vérification : 21/09/2026.

## Objectif

Vendre des guides digitaux SER Guides, encaisser via Stripe, livrer automatiquement le guide par e-mail, puis industrialiser le même système sur 15 niches.

## Guide 01 — Micro-entreprise 2026

- Statut éditorial : FINAL.
- Fichier live du guide : `niches/administratif-fiscal/ebook/index.html`.
- Prix cible : 12,99 €.
- Stripe Payment Link live : `https://buy.stripe.com/14AdR9ayhbFS2n5aQHeUU06`.
- Nouveau Price Stripe : `price_1UGXyjHWJZWsPOa4GQx4aTfl`.
- Ancien prix 19,90 € : existe encore dans Stripe.
- Ancien Payment Link 19,90 € : encore actif au 21/09/2026 ; à désactiver dès que le connecteur Stripe dispose des droits d'écriture correspondants.

## Livraison automatique

### Stripe

Webhook live actif :
- événement principal : `checkout.session.completed`
- endpoint : Neon Function `serdelivery`

### Neon

Projet : `ser-guides-delivery`

Fonction : `serdelivery`

Déploiement actif : v7.

La v7 :
- vérifie la signature Stripe ;
- ignore les paiements non payés ;
- reconnaît le Payment Link du Guide 01 ;
- récupère l'e-mail du client ;
- utilise un idempotency key pour éviter les doubles envois ;
- joint le guide depuis le fichier GitHub ;
- utilise le champ Resend `attachments.url` ;
- est déjà structurée pour ajouter d'autres guides par Payment Link.

Variables présentes :
- `RESEND_API_KEY`
- `STRIPE_WEBHOOK_SECRET`

### Resend

Template publié :
- `SER Guide 01 — Livraison après achat`
- alias : `ser-guide-01-delivery`

Le mauvais expéditeur TantiGusti a été retiré du template.

Domaine SER créé dans Resend :
- `mail.serguides.fr`
- statut actuel : NON VÉRIFIÉ / DNS à configurer chez OVH.

Expéditeur prévu :
- `SER Guides <guides@mail.serguides.fr>`

IMPORTANT :
- la clé Resend actuellement injectée dans Neon a été créée avant le domaine SER ;
- après vérification de `mail.serguides.fr`, créer une nouvelle clé Resend SER dédiée puis remplacer `RESEND_API_KEY` dans Neon.

## DNS à ajouter chez OVH

Domaine Resend : `mail.serguides.fr`

DKIM TXT :
- sous-domaine : `resend._domainkey.mail`
- valeur : `p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDn8X37gkVqctoC05e9FpLKS43P1tzLajGGMsmP75qbr/+6nimqR+8YoKSlFUcduRpavxe3Y3sIbxl3cd7DGLtn9dYZRdzcIPX7vBPaeY7ZppOkP/A5LrcucaXWY8GfW7uEpVWikxKJTr0EJH90roZp1bBgRIv7lAwTv4bbwkESawIDAQAB`

SPF MX :
- sous-domaine : `send.mail`
- cible : `feedback-smtp.eu-west-1.amazonses.com`
- priorité : `10`

SPF TXT :
- sous-domaine : `send.mail`
- valeur : `v=spf1 include:amazonses.com ~all`

CNAME :
- sous-domaine : `rsend.mail`
- cible : `send.forge.rmta.net`

## Instagram

Repo : `Soufianeerd/SER-Module`

Le moteur existe et valide les 15 niches.

Workflow : `.github/workflows/publish.yml`

Fonctionnement prévu :
- upload des slides sur Cloudinary ;
- publication du carousel via Instagram Graph API ;
- sauvegarde de l'historique dans GitHub.

État :
- Cloudinary : configuré.
- Code Instagram : présent.
- publication Instagram live : PAS ENCORE VALIDÉE de bout en bout.
- secrets Instagram attendus par GitHub Actions :
  - `IG_USER_ID_MRLIPTN`
  - `IG_TOKEN_MRLIPTN`

Ne pas bloquer la mise en vente du Guide 01 sur Instagram Automation : la priorité est paiement + livraison automatique + page/CTA de vente.

## 15 niches

1. Administratif & fiscal — FINAL
2. Réparation smartphone & électroménager — draft
3. Bricolage & rénovation — draft
4. Mécanique automobile — draft
5. Fitness & transformation — draft
6. Jardinage & potager — draft
7. Immobilier & location — draft
8. Informatique domestique — draft
9. Parental & scolaire — draft
10. Animaux — draft
11. Cuisine & contraintes — draft
12. Langues — draft
13. Revente & petit business — draft
14. Musique & instrument — draft
15. Photo & vidéo smartphone — draft

## Ordre obligatoire avant lancement commercial

1. Confirmer que `serguides.fr` est bien actif chez OVH.
2. Ajouter les 4 enregistrements DNS ci-dessus dans la zone DNS OVH.
3. Vérifier `mail.serguides.fr` dans Resend.
4. Créer une nouvelle API key Resend SER dédiée.
5. Injecter automatiquement cette clé dans Neon.
6. Envoyer un e-mail test avec le Guide 01.
7. Vérifier la réception et la pièce jointe.
8. Faire un paiement Stripe contrôlé et vérifier le parcours complet.
9. Désactiver l'ancien Payment Link 19,90 €.
10. Mettre le nouveau prix 12,99 € comme prix par défaut Stripe.
11. Publier le premier contenu Instagram avec CTA vers le lien 12,99 €.
12. Passer à la niche 02.

## Règle de sortie

Le Guide 01 n'est considéré comme LIVE que lorsque :

`paiement Stripe → webhook Neon → e-mail Resend → guide reçu`

a été vérifié réellement.
