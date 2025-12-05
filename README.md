# Beslisboom ter ondersteuning van de beoordeling kortverblijf Schengenvisumaanvragen 
## Ministerie van Buitenlandse Zaken (BZ)

### Achtergrond, doel en werking
Het ministerie van Buitenlandse Zaken is belast met de taak van het verstrekken van Schengen Kort Verblijf Visa (KVV). Om deze taak zo goed mogelijk uit te voeren wordt er gebruik gemaakt van een op data-analyse gebaseerde werkwijze, het Informatie Ondersteund Beslissen (IOB). Een belangrijk onderdeel hiervan is de Buitenlandse zaken Analyse Omgeving (BAO), waarbij er gebruik wordt gemaakt van een beslisboom. De broncode van deze beslisboom wordt  hier openbaar weergegeven. 
De BAO is een applicatie waarmee visumaanvragen enerzijds met bronnen  (BAO matching) en anderzijds met profielen (BAO profielen) vergeleken kunnen worden. Eenvoudig gezegd wordt er een bericht teruggegeven in de visumaanvraag applicatie met informatie over een eventuele match op bronnen en/of profielen met daarbij de te verwachten behandelintensiteit (track) van de aanvraag. De BAO wordt op de volgende manieren ingezet:
1. Controle of er informatie binnen het visumaanvraag applicatielandschap beschikbaar is over de aanvrager, referent, werkgever en/of reisdocument;
2. Controle of er informatie binnen bronnen van de migratie ketenpartners beschikbaar is over de aanvrager en/of referent; en
3. Het vergelijken van de visumaanvraag met de op dat moment in de BAO aanwezige profielen en op termijn lokale informatie.
Er is sprake van een 'match' indien de aanvrager, referent en/of werkgever in de database van het systeem voorkomt. Een match bestaat hierbij uit een hit/no-hit signaal, waar bij twijfel over de match het proces voor handmatige behandeling wordt ingezet. Daarnaast kan een aanvrager een 'match' hebben als de aanvraag voldoet aan de kenmerken van een profiel. De combinatie van deze matches tezamen worden vertaald naar een gewogen score door een beslisboom (het algoritme), en geeft een indicatie van de te verwachten intensiteit van de te behandelen aanvraag, welke wordt teruggekoppeld aan de beslismedewerker. Komt de aanvrager, referent en/of werkgever niet voor in de database en voldoet de aanvraag niet aan de kenmerken van een profiel, dan is er sprake van een ‘no match’, welke tevens wordt teruggekoppeld aan de beslismedewerker.

De track die door de BAO aan de beslismedewerker wordt teruggegeven is samengestelde informatie uit verschillende componenten, zoals bijvoorbeeld op welke bron er een hit is en welk profiel er van toepassing is. De datagedreven profielen vormen een belangrijk onderdeel in de totstandkoming van de uiteindelijk tracks. Ze geven de beslismedewerker inzicht in hoe er in het verleden werd omgegaan met soortgelijke visumaanvragen, en welke mogelijke overtredingen van de visumcode hebben plaatsgevonden na uitgifte van het visum en hoe uiteindelijk de besluitvorming op deze visumaanvragen is verlopen. Deze datagedreven profielen worden maandelijks gegenereerd door een op-regels-gebaseerde beslisboom. De code van deze beslisboom is het onderwerp van deze publicatie.
De combinatie van componenten, of informatie, geeft in onderlinge samenhang een indicatie van te verwachten intensiteit van de behandeling van de aanvraag. Al deze informatie weegt mee in de uiteindelijke score en daarmee in de track dat de BAO adviseert bij de aanvraag. Aan de hand van de geadviseerde track kan de beslismedewerker besluiten extra controles tijdens de behandeling van de aanvraag uit te voeren, of juist niet.

### Gebruikers
De output van de beslisboom wordt getoond aan BZ-medewerkers die zijn opgeleid om visumaanvragen te beoordelen. Dit zijn de visumbeslismedewerkers.  

### Input
De beslisboom ontvangt als input een dataset bestaande uit de historische visumaanvragen van de afgelopen vijf jaar. 
De datagedreven profielen in de BAO worden bepaald op basis van de volgende bronnen:
1. Visumaanvragen van de afgelopen 5 jaar; en
2. Ketenpartner hits na datum van aanvraag (bijvoorbeeld hoeveel weigeringen bij de KMar zijn er geweest binnen de groep visumaanvragen?).
Input voor de datagedreven profielen komt volledig geautomatiseerd vanuit onze data science omgeving en maandelijks geüpload naar de BAO portal. Dit betreft geaggregeerde data, die niet tot individuele personen te herleiden is, en enkel wordt toegepast voor het aanmaken van de profielen. Hierbij worden een aantal kenmerken van de visumaanvrager op volgorde meegenomen. Het beheer van deze data is belegd bij het verantwoordelijke BZ-data team. Dit proces wordt op termijn op wekelijkse basis uitgevoerd. 

### Output
Op basis van de input genereert de beslisboom een profielcategorie. Deze kunnen de volgende waarden aannemen:
-Kansprofiel
-Risicoprofiel
-Geen profiel 

Als een visumaanvraag binnenkomt die dezelfde kenmerken bevat als een actief profiel, dan wordt dit betreffende profiel gekoppeld aan de visumaanvraag. Het is ook mogelijk dat een visumaanvraag niet voldoet aan de vooraf ingestelde regels en/of drempelwaardes. Dergelijke visumaanvragen krijgen een ‘inbetween’ profiel, en geven een neutrale score door aan het wegingsmodel.
Bovenstaande profielcategorieën vormen 10% input voor het wegingsmodel dat het uiteindelijke behandeladvies aan de beslismedewerkers geeft:
- Fast track
- Regular track
- Intensive track

Als er geen informatie beschikbaar is over een visumaanvrager in de interne lijsten van BZ en de ketenpartnerbronnen, dan is de uitkomst van het profiel doorslaggevend in het uiteindelijke behandeladvies. Deze output is bedoeld als een ondersteunende inschatting van de intensiteit van de aanvraag voor de beslismedewerker. 

### Technische uitleg beslisboom
De profielen geven een beeld van hoe soortgelijke visumaanvragen uit het verleden zich aan de voorwaarden van een kort verblijf visum hebben gehouden. Hiervoor wordt er gebruik gemaakt van een op-regels-gebaseerde beslisboom. Deze werkt als volgt:
1) De historische visumaanvraagdata, bestaande uit visumaanvragen van de afgelopen 5 jaar wordt opgedeeld in groepen. Dit gebeurt op basis van de 7 profielkenmerken: eerst worden de aanvragen opgesplitst op basis van het land van betaalplaats, vervolgens wordt elk van deze gecreëerde groepen opgesplitst op basis van het hoofddoel van de reis, gevolgd door een opsplitsing in leeftijdscategorieën, etc. Op deze manier ontstaat er een beslisboom waarbij elke visumaanvraag is opgedeeld in een groep, bestaande uit 7 kenmerken. 
2) Vervolgens wordt er voor elke groep gekeken of de groep voldoet aan de minimaal vereiste groepsgrootte. De groepen die hier niet aan voldoen worden uit de beslisboom gesneden. 
3) Voor alle overgebleven groepen wordt er getoetst of de groep voldoet aan de minimale hit- en weigeringspercentages voor een kans- of risicoprofiel. De groepen die hier niet aan voldoen worden een ‘inbetween’ profiel. Dit is een profiel die een neutrale waarde bevat.
4) Ten slotte wordt de boom gesnoeid. Dit houdt in dat alle uiterste inbetween profielen -de inbetween profielen die zich aan het uiteinde van de boom bevinden, en niet verder vertakken naar een volgend profiel-, worden verwijderd. Daarnaast worden alle profielen verwijderd die vertakken uit een profiel van hetzelfde type (kans/risico/inbetween). Wanneer een profiel wordt verwijderd worden de aanvragen in dat profiel opgenomen in het bovenliggende profiel.

Voor verdere informatie zie het algoritmeregister:
https://algoritmes.overheid.nl/nl/algoritme/mnre1013/94596537/informatie-ondersteund-beslissen-kort-verblijf-schengen-visum-kvv#werking

En de factsheet: 
https://www.nederlandwereldwijd.nl/binaries/content/assets/pdfs-nederlands/factsheet-informatie-ondersteunend-beslissen-032025.pdf


### Disclaimer
De code is bedoeld ter transparantie en educatie, niet voor operationeel gebruik. Er wordt geen ondersteuning verleend bij hergebruik buiten de context van deze publicatie. Zie voor meer info de EUPL licentie .
De code is werkzaam wanneer de waardes die ‘redacted’ zijn worden ingevuld. Er is echter geen (sample-) dataset bij de code gevoegd. Het toevoegen van onze actuele visumaanvraagdataset is niet mogelijk omdat dit gevoelige persoonsgegevens bevat. Daarnaast is het toevoegen van een sample-dataset niet mogelijk omdat er hiervoor keuzes gemaakt dienen te worden met betrekking tot de verdelingen van de kenmerken. Deze keuzes hebben een directe causale relatie met de output van het algoritme, wat voor verwarring kunnen zorgen.
