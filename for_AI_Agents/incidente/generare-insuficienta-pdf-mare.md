# Handoff: rezultate insuficiente pentru un PDF mare

Data raportării: 18 octombrie 2026

Stare: **deschis; nu implementați fără reproducere**

Sursă raportată: `H:\4Next\Lecture_2_Programming_Fundamentals_in_C++.pdf`, 127 pagini, programare C++

Capturi: [dosarul de dovezi](../../miscellaneous/ai-fail-2/README.md)

## Cererea utilizatorului

Utilizatorul a ales o sesiune de **120 de minute** pentru PDF-ul de 127 de pagini. Așteptarea lui este să primească suficiente lecții utile și consistente, construite pe întregul material. Dacă un singur apel AI nu poate procesa volumul fără să piardă conținut, propunerea lui este să fie împărțit în capitole/segmente și generat secvențial. Pentru această sesiune a cerut doar documentarea și commit/push; a spus explicit să nu reparăm generatorul acum.

## Ce dovedesc capturile

- Antetul cursului identifică fișierul, arată **3 lecții**, **127 pagini/secțiuni**, **120 min/sesiune** și limba documentului `EN`.
- Mesajul UI afirmă că sesiunea de 120 de minute este doar o selecție de idei, nu acoperire completă. Așteptarea utilizatorului și produsul se contrazic: durata mare nu produce mai multă acoperire în rezultat.
- Lista lecțiilor are doar „Introduction to C++”, „Variables and Types” și „Functions and Pass-by-Value”. Un exemplu vizibil include afirmația că C++ folosește convenția camelCase și că tipul trebuie definit explicit de fiecare dată; acestea trebuie confruntate cu sursa și regulile limbajului, nu acceptate automat.
- Fragmentele de citare pentru lecția „Variables and Types” conțin secvențe deformate precum `classNum 106`, `94.7 tuesdayTemp` și text amalgamat. Verificați extracția, asocierea citatului cu pagina și felul în care textul e randat.
- Quizul are doar **3 întrebări**. Prima întrebare spune că schimbarea tipului unei variabile produce eroare, deși în C++ atribuirea cu conversie compatibilă poate fi validă. Întrebarea trebuie rescrisă cu condiții precise sau eliminată; distragerile pot întări aceeași ambiguitate.
- Captura flashcardurilor arată **4 carduri** în recapitularea activă. Cardul despre pass-by-value poate fi valid, însă volumul este mic față de 127 de pagini și 120 de minute.
- Rezumatul cursului menționează o tranziție de la Python la C++; verificați dacă aceasta există în documentul sursă.

Acestea sunt observații din UI și din capturi. Nu s-a făcut în acest task o nouă rulare pe PDF și nici o comparație pagină cu pagină cu originalul.

## Diagnosticul de pornire

Comportamentul poate veni din limitele de context, selecția/rezumarea globală a paginilor, instrucțiuni care cer prea puține lecții, limita de timp/tokenuri pe hosting, bugetul modelului, verificatorul care aprobă afirmații susținute doar parțial ori dintr-o combinație a acestora. Investigați codul și logurile curente înainte de a alege cauza. Raportul vechi din [remediere_calitate_ai.md](../../docs/remediere_calitate_ai.md) descrie o reparație anterioară; cazul acesta arată că problema de produs persistă.

## Direcție și criterii de acceptare

Proiectați procesarea PDF-urilor mari în segmente delimitate de capitole, secțiuni sau grupuri consecutive de pagini. Procesați segmentele secvențial ori în loturi mici, cu stare și progres vizibile, reluare după erori, deduplicare și validarea citărilor la document/pagină. Agregați rezultatele într-un cuprins coerent, fără să pretindeți că sursa a fost acoperită dacă lipsesc segmente.

Înainte de lansare, demonstrați pe acest PDF (sau pe o copie cu aceeași structură) că:

1. Toate cele 127 pagini/segmente intră într-un plan de procesare vizibil și pot fi urmărite până la materialele rezultate.
2. Sesiunea de 120 de minute produce o colecție substanțială de lecții în mai multe părți ale documentului; numărul și profunzimea trebuie stabilite prin evaluare pedagogică, nu printr-un număr arbitrar.
3. Nicio lecție, afirmație, întrebare sau răspuns nu contrazice sursa ori faptele de bază. Ambiguitățile sunt precizate sau eliminate.
4. Citatele sunt lizibile, reale și legate de paginile corecte; textul PDF cu coloane, cod și formatare nu se amestecă în mod care schimbă sensul.
5. Quizurile și cardurile sunt suficient de variate și acoperă segmentele diferite, nu doar paginile selectate pentru sumar.
6. Dacă timpul, bugetul sau un serviciu extern oprește procesarea, UI-ul raportează exact ce s-a procesat și ce a rămas.
7. Testele acoperă atât unitatea pe segmente, cât și fluxul end-to-end cu fixture-uri de dimensiuni mari; rezultatul real este verificat manual pe un eșantion stratificat de pagini.

Nu promiteți că durata selectată singură garantează acoperirea completă. Dacă produsul continuă să facă selecție, interfața trebuie să spună clar câte segmente/pagini au fost procesate și să ofere continuarea până la restul documentului.

## Limita acestui handoff

Acest commit adaugă doar documentație și dovezi. Codul generatorului nu a fost modificat, cazul nu a fost reprodus tehnic și nu există încă o cauză confirmată.
