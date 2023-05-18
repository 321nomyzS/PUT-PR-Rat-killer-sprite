# Programowanie Rozproszone
## Skrzaty zabójcy szczurów
Autorzy: Olga Gerlich 148088 | Szymon Baliński 148225

## Problem
Są dwa rodzaje procesów - S skrzatów i G gnomów. Gnomy ubiegają się o jedną z A agrafek i C celowników. Kombinują agrafki z celownikiem tworząc broń. Skrzaty ubiegają się o broń. Po zdobyciu broni zabijają szczury i zwracają agrafki i celowniki do puli.

## Algorytm
### Lokalne struktury i zmienne
- WaitQueue - kolejka procesów oczekujących na ACK, początkowo pusta
- AckCounter - liczba otrzymanych potwierdzeń ACK, początkowo 0
- ac - liczba celowników/agrafek. Jeżeli liczba broni i celowników jest różna, to bierzemy minimum z tych dwóch wartości. Tą zmienną posiadają tylko gnomy
- b - liczba broni. Tą zmienną posiadają tylko skrzaty
### Globalne struktury i zmienne
- G - liczba gnomów
- S - liczba skrzatów
### Stany
- REST - nie ubiega się o dostęp
- WAIT - czeka na dostęp do sekcji krytycznej
- INSECTION - w sekcji krytycznej
### Wiadomości
- ACK - potwierdzenie dostępu do sekcji krytycznej
- sREQ - żądanie skrzata o wejście w stan WAIT, zawierające priorytet żądania w postaci znacznika Lamporta i id skrzata
- sCHG - informacja o zmniejszeniu liczby broni oraz zwiększeniu liczby agrafek z celownikami
- gREQ - żądanie gnoma o wejście w stan WAIT, zawierające priorytet żądania w postaci znacznika Lamporta i id gnoma
- gCHG - informacja o zwiększeniu liczby broni oraz zmniejszeniu liczby agrafek z celownikami
## Szkic algorytmu
W ramach zadania wykorzystujemy algorytm Ricarta-Agrawali.

Proces i ubiegający się o wejście do sekcji krytycznej wysyła do wszystkich pozostałych prośby REQ o dostęp. Jeżeli prośba trafi do procesu innego rodzaju, to jest ignorowana. Pozostałe procesy odsyłają ACK do procesu i, o ile same się nie ubiegają o dostęp lub jeżeli priorytet ich żądania jest mniejszy od priorytetu procesu i. W przeciwnym wypadku zapamiętują REQ w kolejce WaitQueue.

### Skrzat
Proces skrzat wchodzi do sekcji krytycznej po zebraniu przynajmniej *max(S-b, 0)* ACKów od innych skrzatów. Będąc w sekcji krytycznej proces skrzat zmniejsza swoją lokalną wartość broni oraz wysyła sygnał sCHG do wszystkich pozostałych procesów.

### Gnom
Proces gnom wchodzi do sekcji krytycznej po zebraniu przynajmniej *max(G-ac, 0)* ACKów od innych gnomów. Będąc w sekcji krytycznej proces gnom zmniejsza swoją lokalną wartość agrafek z celownikami oraz wysyła sygnał gCHG do wszystkich pozostałych procesów. Po wyjściu z sekcji krytycznej odsyła ACK do wszystkich procesów znajdujących się w WaitQueue.

Po wyjściu z sekcji krytycznej odsyła ACK do wszystkich procesów znajdujących się w WaitQueue.

## Szczegółowy opis algorytmu dla poszczególnych stanów gnoma
### REST: stan początkowy
Proces i przebywa w stanie REST do czasu, aż podejmie decyzję o ubieganie się o sekcję krytyczną. Ze stanu REST następuje przejście do stanu WAIT po uprzednim wysłaniu wiadomości gREQ do wszystkich innych procesów oraz ustawieniu AckCounter na zero. Wszystkie wiadomości gREQ są opisane tym samym priorytetem, równym zegarowi Lamporta w chwili wysłania pierwszej wiadomości REQ. W przypadku gdy *ac − G*, gnom i od razu zmienia stan na INSECTION i wchodzi do sekcji krytycznej.
#### Reakcje na wiadomości
- sREQ: ignoruje wiadomość
- gREQ: odsyła ACK
- ACK: ignoruje (sytuacja niemożliwa)
- gCHG: zmniejsza wartość *ac*
- sCHG: zwiększa wartość *ac*

### WAIT: ubieganie się o sekcję krytyczną.
Ze stanu WAIT następuje przejście do stanu INSECTION pod warunkiem, że *(AckCounter − G − ac)*.
#### Reakcje na wiadomości
- sREQ: ignoruje wiadomość 
- gREQ:
  - proces i odsyła ACK jeżeli jego żądanie ma mniejszy priorytet niż priorytet otrzymanej wiadomości gREQ.
  - proces i dopisuje id procesu, od którego dostał wiadomość do kolejki WaitQueue, jeżeli żądanie procesu i ma większy priorytet niż priorytet otrzymanej wiadomości gREQ.
- ACK: zwiększa licznik AckCounter
- gCHG: zmniejsza wartość *ac*
- sCHG: zwiększa wartość *ac*

Gdy proces i otrzymał wiadomość ACK od przynajmniej *G − ac* pozostałych procesów, przechodzi do stanu INSECTION.

### INSECTION: przebywanie w sekcji krytycznej
Proces przebywa w sekcji krytycznej do czasu podjęcia decyzji o jej opuszczeniu. Będąc w sekcji krytycznej zmniejsza wartość ac oraz wysyła wiadomość gCHG do wszystkich pozostałych procesów. Po podjęciu decyzji o opuszczeniu sekcji, proces wysyła ACK do procesów, których id znajduje się w WaitQueue, a następnie przechodzi do stanu REST.
#### Reakcje na wiadomości
- sREQ: ignoruje wiadomość
- gREQ: Id procesu dopisuje do kolejki WaitQueue
- ACK: ignoruje (sytuacja niemożliwa)
- gCHG: zmniejsza wartość *ac*
- sCHG: zwiększa wartość *ac*

## Szczegółowy opis algorytmu dla poszczególnych stanów skrzata
### REST: stan początkowy
Proces i przebywa w stanie REST do czasu, aż podejmie decyzję o ubieganie się o sekcję krytyczną. Ze stanu REST następuje przejście do stanu WAIT po uprzednim wysłaniu wiadomości sREQ do wszystkich innych procesów oraz ustawieniu AckCounter na zero. Wszystkie wiadomości sREQ są opisane tym samym priorytetem, równym zegarowi Lamporta w chwili wysłania pierwszej wiadomości REQ.W przypadku gdy *b − S*, skrzat i od razu zmienia stan na INSECTION i wchodzi do sekcji krytycznej.
#### Reakcje na wiadomości
- gREQ: ignoruje wiadomość
- sREQ: odsyła ACK
- ACK: ignoruje (sytuacja niemożliwa)
- sCHG: zmniejsza wartość *b*
- gCHG: zwiększa wartość *b*

### WAIT: ubieganie się o sekcję krytyczną
Ze stanu WAIT następuje przejście do stanu INSECTION pod warunkiem, że *(AckCounter >= S − b)*.
#### Reakcje na wiadomości
- gREQ: ignoruje wiadomość
- sREQ:
  - proces i odsyła ACK jeżeli jego żądanie ma mniejszy priorytet niż priorytet otrzymanej wiadomości gREQ.
  - proces i dopisuje id procesu, od którego dostał wiadomość do kolejki WaitQueue, jeżeli żądanie procesu i ma większy priorytet niż priorytet otrzymanej wiadomości sREQ.
- ACK: zwiększa licznik AckCounter.
- sCHG: zmniejsza wartość *b*
- gCHG: zwiększa wartość *b*

Gdy proces i otrzymał wiadomość ACK od przynajmniej S − b pozostałych procesów, przechodzi do stanu INSECTION.

### INSECTION: przebywanie w sekcji krytycznej
Proces przebywa w sekcji krytycznej do czasu podjęcia decyzji o jej opuszczeniu. Będąc w sekcji krytycznej zmniejsza wartość *b* oraz wysyła wiadomość sCHG do wszystkich pozostałych procesów. Po podjęciu decyzji o opuszczeniu sekcji, proces wysyła ACK do procesów, których id znajduje się w WaitQueue, a następnie przechodzi do stanu REST.
#### Reakcje na wiadomości
- gREQ: ignoruje wiadomość
- sREQ: Id procesu dopisuje do kolejki WaitQueue
- ACK: ignoruje (sytuacja niemożliwa)
- sCHG: zmniejsza wartość *b*
- gCHG: zwiększa wartość *b*

## Program
### Uruchomienie programu
Program uruchamiamy z poziomu terminala wpisując:
```
mpiexec -n [liczba_procesów] python main.py [liczba gnomów] [liczba skrzatów]
```

Przykład:
```
mpiexec -n 5 python -B main.py 3 2
```

Należy pamiętać, że liczba procesów musi się równać sumie liczby gnomów i skrzatów.

### Biblioteki
Przed uruchmieniem programu należy zainstalować biblioteki:
- mpi4py - biblioteka użyta do działania programu w trybie rozproszonym
- colorama - biblioteka użyta do wyświetlania komunikatów w różnych kolorach
```
pip install mpi4py
pip install colorama
```