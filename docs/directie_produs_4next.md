# Direcția produsului 4Next

Acest document păstrează ideile de produs discutate și le transformă în cerințe de referință pentru implementare. Este o direcție de lucru, nu o promisiune că toate funcționalitățile intră în prima versiune.

## Principii pentru AI-ul de studiu

- AI-ul detectează limba materialului-sursă și generează lecții, explicații, flashcarduri, quizuri și recapitulări în aceeași limbă. Nu schimbă limba în mod implicit.
- Se comportă ca un profesor răbdător: explică limpede, adaptează vocabularul la nivelul elevului, descompune ideile dificile în pași, oferă exemple și verifică înțelegerea.
- Tonul poate fi încurajator și natural, dar produsul nu pretinde că AI-ul este o persoană sau un profesor uman.
- Dacă o informație nu poate fi susținută de document, AI-ul spune clar acest lucru. Explicațiile suplimentare trebuie deosebite de ceea ce afirmă sursa.
- O opțiune de traducere într-o altă limbă poate fi adăugată ulterior ca alegere explicită; nu înlocuiește regula implicită a limbii documentului.

## Chat despre document

Experiența va include o secțiune de chat legată de PDF-ul sau materialul deschis, inspirată de felul în care NotebookLM lucrează cu surse. Chatul trebuie să:

- răspundă la întrebări specifice folosind materialul încărcat, nu doar cunoștințe generale ale modelului;
- indice pagina, secțiunea sau fragmentul-sursă când acestea pot fi identificate;
- spună când răspunsul nu se găsește în document și să nu inventeze un răspuns;
- permită întrebări de continuare în contextul aceluiași material;
- distingă afirmațiile din document de clarificările pedagogice adăugate de AI.

**Criteriu de acceptare:** pentru o întrebare al cărei răspuns apare în PDF, chatul oferă un răspuns în limba documentului și o trimitere la sursă; pentru o întrebare al cărei răspuns lipsește, recunoaște limita documentului.

## Pregătire pentru examene și programe școlare

Direcția produsului este pregătirea elevilor și studenților pentru examene, pornind de la materialele lor și, eventual, de la programa relevantă. Înaintea integrării unor surse externe, trebuie cercetate surse oficiale sau API-uri disponibile și verificate actualitatea, proveniența și condițiile de utilizare ale conținutului.

O integrare viitoare ar putea identifica materia, nivelul/clasa și examenul, apoi să asocieze materialul cu temele din programa potrivită și să arate ce este acoperit sau ce mai trebuie studiat. Programa trebuie să indice sursa și versiunea/anul; produsul nu trebuie să prezinte o mapare estimată de AI ca fiind oficială.

Această etapă depinde de alegerea examenelor și nivelurilor școlare vizate și de găsirea unor surse care pot fi folosite legal și fiabil. Până atunci, încărcarea de către elev a materialelor proprii rămâne fluxul de bază.

## Conturi și personalizare — etapă ulterioară

După ce fluxul principal de studiu funcționează bine, contul ar putea începe cu câteva întrebări de personalizare, precum nivelul/clasa, obiectivul sau examenul, data examenului, nivelul perceput și timpul disponibil pentru studiu. Răspunsurile ar putea adapta planul și explicațiile.

Această idee este amânată față de funcțiile de bază. Profilul trebuie să poată fi modificat, iar colectarea datelor să rămână minimă și explicată clar, cu atenție specială dacă produsul este folosit de minori.

## Ordine de lucru propusă

1. Aplică regula limbii documentului și stilul pedagogic în toate generatoarele de materiale.
2. Construiește chatul ancorat în document, cu trimiteri la sursă și comportament explicit pentru informațiile absente.
3. Alege examenele/nivelurile vizate și cercetează surse oficiale, drepturile de utilizare și felul în care se identifică programa.
4. Evaluează integrarea programei și pregătirea ghidată pentru examene pe baza surselor confirmate.
5. Adaugă conturi și personalizare după validarea fluxului de studiu de bază.

Ordinea este o propunere de produs și poate fi ajustată după discuția echipei și cerințele hackathonului.

## Scenariu de verificare a direcției

Un elev încarcă un material. 4Next generează în limba acelui material o explicație pe înțelesul lui, flashcarduri și întrebări de verificare. Elevul întreabă chatul ceva despre PDF și primește un răspuns cu pagina relevantă; dacă PDF-ul nu conține răspunsul, chatul spune asta. Într-o etapă ulterioară, elevul poate lega materialul de o programă oficială pentru examenul și nivelul selectate.

## Decizii care rămân deschise

- Ce examene, materii și niveluri școlare vor fi prioritare?
- Ce formate și limbi de document vor fi susținute și cum va fi identificată limba?
- Ce surse oficiale/API-uri pentru programe și manuale pot fi folosite, cu ce licențe și actualitate?
- Ce nivel de citare poate oferi fiecare format: pagină, secțiune sau fragment?
- Ce date de personalizare sunt necesare și ce protecții sunt potrivite pentru utilizatorii minori?
