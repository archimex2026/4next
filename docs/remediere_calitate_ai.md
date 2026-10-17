# Remedierea calității materialelor de studiu

18 octombrie 2026. Raportul pornește de la `citeste_asta.txt`, cele opt capturi `ai-fail` și testul permis pe PDF-ul C++ de 22 de pagini. Documentul suplimentar de 127 de pagini nu a fost citit.

## Cauze confirmate

1. PyPDF2 transforma caracterele suprapuse folosite pentru bold în identificatori repetați. Watermarkul diagonal „DRAFT” ajungea în propoziții.
2. Chiar dacă Gemini producea explicații, aplicația le elimina și reconstruia cursul numai din citate. Măsura prevenea afișarea unor afirmații neverificate, dar anula funcția de profesor.
3. Bugetul de cinci minute selecta primul grup de fragmente. Peste 100.000 de caractere, generatorul evita complet AI-ul.
4. Întrebările generale despre conținut nu erau recunoscute. „Difference” reducea scorul de căutare, iar spațiile din identificatori precum `conste xpr` provocau refuzuri false.
5. Aliasul Gemini putea expira sau eșua. O cheie nouă nu rezolvă singură selecția modelului, extracția și eliminarea explicațiilor.

## Schimbări implementate

- Extragere cu pdfplumber, deduplicare de glyph-uri și excluderea watermarkurilor mari diagonale. Operatorii C++ precum `++` și `<<` rămân intacți.
- Explicațiile, cardurile și quizurile AI se păstrează după validarea structurii și limbii. Un apel separat verifică suportul în fragmentele citate; afirmațiile cu numere absente din dovezi sunt respinse și local.
- Un card sau quiz opțional cu citare invalidă este omis; nu anulează lecțiile deja validate. Lecțiile fără citări valide rămân respinse.
- Validarea limbii păstrează verificarea fiecărui câmp, cu o singură detecție limitată per câmp, pentru CPU-ul demo.
- Citările folosesc ID-uri ale fragmentelor oferite de server. Serverul returnează textul exact și pagina reală, în loc să ceară modelului să reintroducă manual citate lungi.
- Documentele mari folosesc un context limitat, distribuit între toate paginile. Cinci minute înseamnă overview/selectare, fără promisiunea acoperirii întregului document.
- Chatul recunoaște întrebări generale, comparații și identificatori afectați de spațiere. Pentru un overview, caută dovezi distribuite între pagini.
- Interfața avertizează despre durata aleasă, permite verificarea textului extras înainte de generare, afișează codul delimitat în blocuri și semnalează clar fallbackul extractiv.
- Modelul implicit testat este `gemini-3.1-flash-lite`. Noua cheie este configurată local în `.env` ignorat de Git; fișierul de import Render rămâne în directorul secret, în afara repository-ului.

## Dovezi de verificare

Testele automate acoperă caractere suprapuse, operatori C++, citări exacte, ID-uri inventate, identificatori spațiați, păstrarea explicației AI, respingerea explicațiilor nesusținute și eșantionarea documentelor lungi.

Testul real pe PDF-ul C++ a produs un curs `ai_grounded`, cu lecții despre sintaxă, tipuri, controlul execuției, clase, modularitate și erori. Citările ajung în partea finală a documentului. Cu noua cheie, generarea a reușit din nou în aproximativ 11 secunde. Testul real de cinci minute a produs un overview cu dovezi din mai multe zone ale PDF-ului. Chatul a explicat conținutul și diferența `const` / `constexpr`, iar întrebarea despre un campionat absent din sursă a fost refuzată.

Artefactele locale de test sunt în `H:\4Next\artifact-qa\ai-fix`, în afara Git. Numărul de teste și starea publicării sunt consemnate în README și în checklistul de pași rămași.

## Limite și pași rămași

- Verificarea automată reduce erorile; nu garantează corectitudinea pedagogică sau factuală a fiecărei explicații. Un set de evaluare cu profesori/elevi rămâne necesar.
- Dacă modelul, cheia sau verificarea nu sunt disponibile, aplicația oferă extrase etichetate, nu pretinde că a produs o lecție AI.
- Materialele generate anterior păstrează conținutul vechi în baza de date. Pentru a beneficia de corecția extracției și a generării, documentul trebuie reîncărcat. Nu se șterg automat notițe sau progres.
- Bonusul cu până la trei surse într-un spațiu rămâne separat: trebuie citate după document și pagină, validate limitele cumulate și tratate documentele în limbi diferite.
- Publicarea acestei corecții și verificarea ei pe Render se confirmă separat de testele locale. Datele planului Free rămân temporare.
