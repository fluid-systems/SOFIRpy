# Checkliste zur Software-Entwicklung bei studentischen Arbeiten (Markdown Vorlage)

## Nutzungshinweise
Diese Checkliste liefert Empfehlungen zur Software-Entwicklung bei studentischen Arbeiten (Bachelor-Thesis, Master-Thesis, ADP) und wurde von der dlr entwickelt. Eine deteilierte Beschreibung der Empfehlungen/Anforderungen ist hier zu finden: [Software-Engineering-Empfehlungen des DLR](https://zenodo.org/record/1344608#.YHVVi0VR0uU). Primär richten sich diese an Software-Entwickler zur Selbsteinschätzung entwickelter Software und als Ideengeber für die weitere Entwicklung. Die Checkliste liefert keine neuen, revolutionären Ansätze zur Software-Entwicklung. Sie hilft aber notwendige, wesentliche Schritte der Software-Entwicklung nicht zu vergessen. Zudem können die Empfehlungen als Argumentationshilfe dienen.

 Die Empfehlungen sind mit Fokus auf Wissenserhalt und gute Software-Engineering-Praxis erstellt. Sie unterstützen dabei, die Nachvollziehbarkeit und Nachhaltigkeit entwickelter Software zu erhalten. Die Empfehlungen motivieren den Einsatz von Tools, die Erstellung von Dokumentation, die Etablierung von Prozessen oder die Einhaltung von Prinzipien. Bei der Bewertung einer Empfehlung empfiehlt es sich daher zu überlegen, inwieweit der genannte Aspekt umgesetzt ist und ob Verbesserungsbedarf besteht. Dies kann man beispielsweise wie folgt umsetzen:

* Gibt es derzeit keinen Verbesserungsbedarf und die Empfehlung ist prinzipiell passend adressiert? Status: **ok**
* Gibt es Verbesserungspotential, welches in nächster Zeit umgesetzt werden kann bzw. sollte? Status: **todo**, Verbesserungsbedarf unter Bemerkungen festhalten
* Ist die Empfehlung derzeit noch nicht relevant, könnte aber in einer spÃ¤teren Entwicklungsphase hilfreich sein? Status: **future**
* Ist die Empfehlung im Entwicklungskontext nicht sinnvoll umsetzbar? Status: **n.a.** (not applicable, nicht zutreffend), Grund unter Bemerkungen erläutern

> Den Status zwischen `**[]**` vermerken. Die Bemerkungen unterhalb der Empfehlung als Liste (z.B. `* Repository einrichten`) erfassen.

## Zusammenfassung der Ergebnisse
Die Software erreicht Anwendungsklasse [1, 2 oder 3].

Der Schwerpunkt zukünftiger Verbesserungen liegt auf:

## Inhaltsverzeichnis
[[Qualifizierung](#qualifizierung)] [[Anforderungsmanagement](#anforderungsmanagement)] [[Software-Architektur](#software-architektur)] [[Änderungsmanagement](#aenderungsmanagement)] [[Design und Implementierung](#design-implementierung)] [[Software-Test](#software-test)] [[Release-Management](#release-management)] [[Automatisierung und AbhÃ¤ngigkeitsmanagement](#automatisierung-abhaengigkeiten)] 


## Qualifizierung <a name="qualifizierung"></a>
**[]** Der Software-Verantwortliche kennt die verschiedenen Anwendungsklassen und weiß, welche für seine Software anzustreben ist. *(EQA.1)*

**[]** Der Software-Verantwortliche weiß, wie er gezielt Unterstützung zu Beginn und im Verlauf der Entwicklung anfordern und sich mit anderen Kollegen (Studierende, WiMis) zum Thema Software-Entwicklung austauschen kann. *(EQA.2)*

**[]** Die an der Entwicklung Beteiligten ermitteln den Qualifikationsbedarf in Bezug auf ihre Rolle und die angestrebte Anwendungsklasse. Sie kommunizieren diesen Bedarf an den Vorgesetzten (betreuender WiMi). *(EQA.3)*

**[]** Den an der Entwicklung Beteiligten stehen die für ihre Aufgaben benötigten Werkzeuge zur Verfügung und sie sind geschult in deren Benutzung. *(EQA.4)*


## Anforderungsmanagement <a name="anforderungsmanagement"></a>
**[]** Die Aufgabenstellung ist mit allen Beteiligten abgestimmt und dokumentiert. Sie beschreibt in knapper, verständlicher Form die Ziele, den Zweck der Software, die wesentlichen Anforderungen und die angestrebte Anwendungsklasse. *(EAM.1)*


**[]** Die Randbedingungen (zu verwendete Programmiersprache, Frameworks, etc) sind erfasst. *(EAM.3)*

## Software-Architektur <a name="software-architektur"></a>
**[]** Wesentliche Architekturkonzepte und damit zusammenhängende Entscheidungen sind zumindest in knapper Form dokumentiert. *(ESA.2)*

## Änderungsmanagement <a name="aenderungsmanagement"></a>
**[]** Die wichtigsten Informationen, um zur Entwicklung beitragen zu können, sind an einer zentralen Stelle abgelegt. Es werden die grundlegenden Schritte beschrieben, um mit der Entwicklung beginnen zu können. Häufig befinden sich diese Informationen im Repository bspw. in der README Datei. (Wichtig falls, nach der stutenischen Arbeit von neuen Entwicklern an der Software weitergearbeitet werden soll) *(EÄM.2)*

**[]** Bekannte Fehler, wichtige ausstehende Aufgaben und Ideen sind zumindest stichpunktartig in einer Liste festgehalten und zentral abgelegt. Diese Informationen können ebenfalls im README festegehalten werden. *(EÄM.5)*

**[]** Ein Repository ist in einem Versionskontrollsystem (z.B. Gitlab) eingerichtet. Das Repository ist angemessen strukturiert und enthält möglichst alle Artefakte, die zum Erstellen einer nutzbaren Version der Software erforderlich sind. *(EÄM.7)*

**[]** Jede Änderung des Repository dient möglichst einem spezifischen Zweck, enthält eine verständliche Beschreibung und hinterlässt die Software möglichst in einem konsistenten, funktionierenden Zustand. *(EÄM.8)*

## Design und Implementierung <a name="design-implementierung"></a>
**[]** Es werden die üblichen Konstrukte und Lösungsansätze der gewählten Programmiersprache eingesetzt sowie ein Regelsatz hinsichtlich des Programmierstils konsequent angewendet. Der Regelsatz bezieht sich zumindest auf die Formatierung und Kommentierung. Ein Beispiel für ein solchen Regelsatz für verschiedene Programmiersprachen kann hier entnommen werden: [Google Style Guides](https://google.github.io/styleguide/) *(EDI.1)*

**[]** Die Software ist möglichst modular strukturiert. Die Module sind lose gekoppelt, d.h., ein einzelnes Modul hängt möglichst gering von anderen Modulen ab. *(EDI.2)*

**[]** Im Quelltext und in den Kommentaren sind möglichst wenig duplizierte Informationen enthalten. ("Don`t repeat yourself.") *(EDI.9)*

**[]** Es werden einfache, verständliche Lösungen bevorzugt eingesetzt.  ("Keep it simple and stupid."). *(EDI.10)*

## Software-Test <a name="software-test"></a>
**[]** Die grundlegenden Funktionen und Eigenschaften der Software werden in einer möglichst betriebsnahen Umgebung getestet. Es ist sinnvoll einen Test nach folgenden Teststufen zu klassifizieren: Modultest, Integrationstest, Systemtest, Abnahmetest. Eine Definition dieser Klassifikationen findet sich unter Kapitel 4.6. Dabei ist es ausreichend die Tests manuell durchzuführen. *(EST.4)*

**[]** Das Repository enthält möglichst alle für den Test der Software erforderlichen Artefakte. *(EST.10)*

## Release-Management <a name="release-management"></a>
**[]** Das Release-Paket enthält oder verweist auf die Nutzer-Dokumentation. Sie besteht zumindest aus Installations-, Nutzungs- und Kontaktinformationen sowie den Release Notes. Im Fall der Weitergabe des Release-Pakets an Dritte außerhalb des FST, sind die Lizenzbedingungen beizulegen. *(ERM.2)*

Die folgenden Punkte sind müssen bei studentische Arbeiten in der Regel nicht erfüllt werden.

**[]** Jedes Release besitzt eine eindeutige Release-Nummer. Anhand der Release-Nummer lässt sich der zugrunde liegende Softwarestand im Repository ermitteln. *(ERM.1)*

**[]** Während der Release-Durchführung werden alle vorgesehenen Testaktivitäten ausgeführt. *(ERM.6)*

**[]** Vor der Weitergabe des Release-Pakets an Dritte außerhalb des FST ist sicherzustellen, dass eine Lizenz festgelegt ist, die Lizenzbestimmungen verwendeter Fremdsoftware eingehalten werden und alle erforderlichen Lizenzinformationen dem Release-Paket beigelegt sind. *(ERM.9)*

**[]** Vor der Weitergabe des Release-Pakets an Dritte außerhalb des FST ist sicherzustellen, dass die Regelungen zur Exportkontrolle eingehalten werden. *(ERM.10)*

## Automatisierung und Abhängigkeitsmanagement <a name="automatisierung-abhaengigkeiten"></a>
**[]** Der einfache Build-Prozess läuft grundlegend automatisiert ab und notwendige manuelle Schritte sind beschrieben. Zudem sind ausreichend Informationen zur Betriebs- und Entwicklungsumgebung vorhanden. *(EAA.1)*

**[]** Die Abhängigkeiten zum Erstellen der Software sind zumindest mit dem Namen, der Versionsnummer, dem Zweck, den Lizenzbestimmungen und der Bezugsquelle beschrieben. *(EAA.2)*

**[]** Das Repository enthält möglichst alle Bestandteile, um den Build-Prozess durchführen zu können. *(EAA.10)*