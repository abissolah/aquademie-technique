- faire une sauvegarde de la base de données postgres 
- monter un autre site qui pointera sur cette base de données postgres sauvegardée avec un sous domaine de la forme https://www.25-26.app-suivitech.fr/

-créer une base de données vierge app-suivitech.fr/ sur laquelle on doit ajouter une nouvelle table anciens_adherents avec les meme champs que adhéents pour pouvoir à l"inscription préremplir le formulaire. 
-à l'inscription, l'utilisateur devra choisir s'il est un nouveau membre ou un ancien membre.
-si c'est un ancien membre, il devra entrer son nom ce qui préremplira le formulaire d'inscription, il devra vérifier ses informations, et ajouter son caci s'il a un nouveau caci, et la date d'expiration du caci obligatoire, et valider son inscription, tous les nouveaux caci doivent être validés par un administrateur. notifier l'administrateur par email, et renvoyer l'utilisateur sur helloasso. 
-voir si c'est possible de faire un webhook pour mettre un flag pour indiquer que l'utilisateur a bien validé son paiement sur helloasso.

-




