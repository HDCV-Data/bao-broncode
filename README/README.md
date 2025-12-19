# Beslisboom ter ondersteuning van de beoordeling kortverblijf Schengenvisumaanvragen 
## Ministerie van Buitenlandse Zaken (BZ)

### Disclaimer
De publicatie van de broncode voor het opstellen van profielen is bedoeld ter transparantie en educatie, niet voor operationeel gebruik. Er wordt geen ondersteuning verleend bij hergebruik buiten de context van deze publicatie. Zie voor meer informatie de EUPL licentie. De broncode is werkzaam wanneer de waardes die ‘redacted’ zijn worden ingevuld. Er is echter geen (sample-) dataset bij deze publicatie gevoegd. Het toevoegen van onze actuele visumaanvraagdataset is niet mogelijk omdat dit gevoelige persoonsgegevens bevat. Daarnaast is het toevoegen van een sample-dataset niet mogelijk, omdat er hiervoor keuzes gemaakt dienen te worden met betrekking tot de verdelingen van de kenmerken. Deze keuzes hebben een directe causale relatie met de output van het algoritme, hetgeen voor verwarring kan zorgen.

### Achtergrond, doel en werking
Het ministerie van Buitenlandse Zaken (BZ) is belast met de taak van het verstrekken van Schengen Kort Verblijf Visa (KVV). Om deze taak zo goed mogelijk uit te voeren, wordt er gebruik gemaakt van een op data-analyse gebaseerde werkwijze: het Informatie Ondersteund Behandelen (IOB). Binnen het IOB worden visumaanvragen enerzijds met bronnen en anderzijds met profielen vergeleken. De combinatie van matches met deze bronnen en mogelijke profielen wordt vertaald naar een gewogen score, die een indicatie geeft van de te verwachten capaciteitsinzet bij de behandeling van een visumaanvraag (zogeheten tracks: fast, regular of intensive). Deze indicatie wordt gedeeld met de consulaire medewerker die verantwoordelijk is voor de behandeling van de visumaanvraag.
Voor het genereren van de profielen wordt gebruik gemaakt van een op regels gebaseerde beslisboom. De broncode van deze beslisboom is onderwerp van deze publicatie. De broncode van het wegingsmodel is geen onderdeel van publicatie. 

Raadpleeg voor meer informatie over de werkwijze bij BZ het algoritmeregister: 
https://algoritmes.overheid.nl/nl/algoritme/mnre1013/94596537/informatie-ondersteund-beslissen-kort-verblijf-schengen-visum-kvv#werking

En de factsheet: 
https://www.nederlandwereldwijd.nl/binaries/content/assets/pdfs-nederlands/factsheet-informatie-ondersteunend-beslissen-032025.pdf.

### Input
De datagedreven profielen in de BAO worden bepaald op basis van de input:
1.	Visumaanvragen van de afgelopen 5 jaar; en
2.	Ketenpartner hits na datum van de goedkeuring van de aanvraag (bijvoorbeeld hoeveel weigeringen bij de KMar er zijn geweest, nadat een aanvrager met een toegewezen visum naar Nederland is gereisd, binnen de groep visumaanvragen). 
Dit betreft geaggregeerde data.

### Output
Op basis van de input genereert de beslisboom een profielcategorie. Deze kunnen de volgende waarden aannemen: 1) kansprofiel, 2) risicoprofiel 3) geen profiel.
Als een visumaanvraag binnenkomt die dezelfde kenmerken bevat als een actief profiel, dan wordt dit betreffende profiel gekoppeld aan de visumaanvraag. Het is ook mogelijk dat een visumaanvraag niet voldoet aan de vooraf ingestelde regels en/of drempelwaardes. Dergelijke visumaanvragen krijgen een ‘inbetween’ profiel, en geven een neutrale score door aan het wegingsmodel. 
Als er geen informatie beschikbaar is over een visumaanvraag in de bronnen van de BAO, dan is de uitkomst van het profiel doorslaggevend in de uiteindelijke vaststelling van de track. Deze output is bedoeld als een ondersteunende inschatting van de te verwachten capaciteitsinzet bij de aanvraag voor de consulaire medewerker.

### Technische uitleg beslisboom
De profielen geven een beeld van hoe soortgelijke visumaanvragen uit het verleden zich aan de voorwaarden van een kort verblijf visum hebben gehouden. Hiervoor wordt er gebruik gemaakt van een op-regels-gebaseerde beslisboom. Deze werkt als volgt:
1.	De historische visumaanvraagdata, bestaande uit visumaanvragen van de afgelopen 5 jaar, worden opgedeeld in groepen. Dit gebeurt op basis van 7 profielkenmerken: eerst worden de aanvragen opgesplitst op basis van het eerste kenmerk, gevolgd door de opeenvolgende kenmerken. Op deze manier ontstaat er een beslisboom waarbij elke visumaanvraag is opgedeeld in een groep, bestaande uit 7 vaste kenmerken.
2.	Vervolgens wordt er voor elke groep gekeken of de groep voldoet aan de minimaal vereiste groepsgrootte. De groepen die hier niet aan voldoen worden uit de beslisboom gesneden.
3.	Voor alle overgebleven groepen wordt er getoetst of de groep voldoet aan de minimale hit- en weigeringspercentages voor een kans- of risicoprofiel. De groepen die hier niet aan voldoen worden een ‘inbetween’ profiel. Dit is een profiel dat een neutrale waarde bevat.
4.	Ten slotte wordt de boom gesnoeid. Dit houdt in dat alle uiterste inbetween profielen -de inbetween profielen die zich aan het uiteinde van de boom bevinden, en niet verder vertakken naar een volgend profiel-, worden verwijderd. Daarnaast worden alle profielen verwijderd die vertakken uit een profiel van hetzelfde type (kans/risico/inbetween). Wanneer een profiel wordt verwijderd, worden de visumaanvragen uit dat profiel opgenomen in het bovenliggende profiel.
