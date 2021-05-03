## Protokoll 01.04.2021 - 12.04.2021

- Gespräch mit Marius - Verbesserungsvorschläge:
    * Speichern von Daten in HDF5 Datein nicht nötig; Datenmanagement nicht nötig &rarr; einführen eines "Testing Modes"
    * bessere Strukturierung des Codes &rarr; Überlegung mehr OOP zu arbeiten und Übersicht mit UML Klassendiagramm
    * Rückgaben mancher Funktionen zur besseren Fehlersuche 
    * MAS wird mit meheren Modellen getestet &rarr; event. andere Ordner Struktur überlegen, die es erlaubt zwischen den Modellen zu unterscheiden
    * leicht einstellen, wie man den Workflow benutzen will (Testen, Daten generieren, etc); welche Daten sollen geplottet werden
    * (Dymola Modell beschleunigen) 
- Erstellung von Issues <br> [Issue Board](https://git.rwth-aachen.de/fst-tuda/projects/digitalization/fair_sim/ADP_FAIR_Sim/-/boards)
- Lesen von DLR Guidelines
- Code durchgehen
- Gedanken über verbesserte Struktur &rarr; UML Diagramm

## Protokoll 13.04.2021 - 03.05.2021
- Lizenz Probleme
- [dlr guidelines für studentische Arbeiten](https://git.rwth-aachen.de/fst-tuda/projects/digitalization/fair_sim/fair_sim_release/-/blob/master/dlr%20guidelines/requirements_class_1.md)
- Überarbeitete Struktur des Datenimport und FMU Export 
    - Schnittstelle zu OpenModelica --> FMU Export möglich, aber Datenimport noch nicht
    - Zuordnung von PIDs wurde entfernt --> wird später in einem anderen Modul implementiert --> Gewährleistung der Modularität
    - Arbeiten an zusätzlichen Feature --> checken ob importierte Parameter im Modell vorhanden sind (bisher kam es zu keiner Fehlermeldung)
- Struktur des Simulations Modul am Überarbeiten, Ziel:
    - mehrere FMU simulieren 
    - beliebige MAS simulieren
    - FMU mit belibiegen Input aus Python Skripten simulieren

Beim überarbeiten der Module stest im Hinterkopf, Modul sollte als alleinstehdes Modul nutzbar sein.

