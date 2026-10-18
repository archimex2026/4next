# Context pentru agenții AI

Citește acest fișier la începutul unei sesiuni de lucru în repo. Apoi citește incidentul activ și checklistul proiectului înainte să schimbi codul.

## Starea proiectului

4Next este un prototip de studiu din documente. Stackul curent este Next.js și FastAPI, iar demo-ul public rulează pe Render Free cu date temporare. Ramurile de lucru folosite de echipă sunt `flavius` și `main`. README-ul rădăcinii descrie funcțiile curente; [docs/urmatorii_pasi.md](../docs/urmatorii_pasi.md) ține backlogul și prioritățile.

## Lucrări relevante deja făcute

- Extracția PDF folosește `pdfplumber`, curăță glyph-uri suprapuse și watermarkuri mari și păstrează reperele paginilor.
- Generarea poate folosi Gemini, păstrează explicațiile generate după validarea citărilor și verificării factuale și etichetează fallbackul extractiv.
- Contextul AI pentru documente lungi este eșantionat pe pagini și limitat ca dimensiune; aceasta nu echivalează cu procesarea pedagogică integrală a cărții.
- Există regresii pentru extracție, limbă, citări, chat și verificarea afirmațiilor. Consultă [docs/remediere_calitate_ai.md](../docs/remediere_calitate_ai.md) pentru istoricul reparației și limitele sale.

## Probleme active

Actualizare după audit: procesarea consecutivă, planul salvat, continuarea și verificarea semantică separată sunt implementate și publicate pe Render în commitul `9e499c5`. Citește [raportul din 18 octombrie](../docs/audit_generare_segmentata.md) pentru dovezi, limite și starea publicării. Versiunea Live este `9e499c5`; `b2579fc` este versiunea precedentă și nu considera toate materialele drept explicații AI: modul poate fi mixt.

Incidentul urgent este în [incidente/generare-insuficienta-pdf-mare.md](incidente/generare-insuficienta-pdf-mare.md), susținut de capturile din [miscellaneous/ai-fail-2](../miscellaneous/ai-fail-2/README.md). Nu considera un rezultat bun doar pentru că trece verificarea citărilor sau pentru că Gemini răspunde în engleză fluentă. Verifică acoperirea tuturor segmentelor, corectitudinea semantică și calitatea efectivă a lecțiilor, cardurilor și quizurilor.

## Reguli de lucru

- Începe cu reproducerea și inspecția codului curent; documentele pot descrie o stare anterioară.
- Nu citi `H:\4Next\Lecture_2_Programming_Fundamentals_in_C++.pdf` integral prin instrumente cu cost mare sau ieșire masivă. Pentru reproducere, extrage metadatele și fragmente reprezentative, apoi verifică pagini/capitole stratificat.
- Respectă limba documentului la toate materialele generate.
- Nu promite „acoperire completă” după sumarizare sau eșantionare. Raportează clar ce capitole/pagini au fost procesate și ce lipsește.
- Procesează documentele mari în segmente cu limite explicite, păstrează starea/progresul, permite reluarea la eșec și unește lecțiile fără duplicate. Durata selectată trebuie să influențeze profunzimea sau numărul lecțiilor în mod verificabil.
- Testează semantic afirmațiile, răspunsurile corecte și distractorii, nu doar structura JSON, limba și existența unei citări.
- Nu modifica cheia Gemini sau alte secrete și nu le afișa în loguri, capturi, Git ori documentație.
- Nu implementa funcții din backlog fără să actualizezi starea și criteriile relevante în documentație.

## Ordinea de citire

1. Acest fișier.
2. [Incidentul de generare pentru PDF mare](incidente/generare-insuficienta-pdf-mare.md).
3. [Checklistul de lucru](../docs/urmatorii_pasi.md).
4. [Raportul remedierii AI anterioare](../docs/remediere_calitate_ai.md).
5. README-ul rădăcinii pentru rulare și configurație.
