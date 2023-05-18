from mpi4py import MPI
import colorama
from colorama import Fore
import time

def get_messages(comm, rank, lamport):
    messages = []
    while True:
        status = MPI.Status()
        #sprawdź czy jest wiadomosc do odebrania od obojętnie kogo. Jak jest, to zapisz o niej informacje w 'status'
        if comm.iprobe(source=MPI.ANY_SOURCE, status=status): 
            message = comm.recv(source=status.Get_source())
            print(f"[SKRZAT:{rank}|{lamport}] Otrzymalem wiadomosc {message} od {status.Get_source()}")
            messages.append((status.Get_source(), message))
        else:
            break
    return messages

def skrzat_code(comm, S, b):
    # Ustawianie zmiennych i struktur lokalnych
    wait_queue = []
    ack_counter = 0
    current_state = "REST"

    # Ustawienia MPI
    rank = comm.Get_rank()
    size = comm.Get_size()

    lamport_clock = 0

    # Ustawianie koloru tekstow
    colorama.init()
    available_colors = [Fore.RED, Fore.GREEN, Fore.BLUE, Fore.YELLOW, Fore.MAGENTA, Fore.CYAN]
    print(available_colors[rank % len(available_colors)], end='')

    while True:
        if current_state == "REST":
            print(f"[SKRZAT:{rank}|{lamport_clock}] Jestem w stanie REST")
            messages = get_messages(comm, rank, lamport_clock)

            for message in messages:
                message_author = message[0]
                message_type = message[1].split()[0]

                if message_type == "gREQ":
                    continue

                elif message_type == "sREQ":
                    print(f"[SKRZAT:{rank}|{lamport_clock}] Odsylam wiadomosc ACK do {message_author}")
                    comm.send("ACK", dest=message_author)

                elif message_type == "ACK":
                    continue

                elif message_type == "sCHG":
                    b -= 1
                    print(f"[SKRZAT:{rank}|{lamport_clock}] Zmniejszam b, teraz jest {b}")

                elif message_type == "gCHG":
                    b += 1
                    print(f"[SKRZAT:{rank}|{lamport_clock}] Zwiekszam b, teraz jest {b}")

            # Przejście do stanu INSECTION
            if b >= S:
                current_state = "INSECTION"
            else:
                # Przejście do stanu WAIT
                ack_counter = 0
                lamport_clock += 1
                print(f"[SKRZAT:{rank}|{lamport_clock}] Wysylam wiadomosc sREQ do wszystkich procesow")
                for i in range(size):
                    if i != rank:
                        comm.send(f"sREQ {lamport_clock}", dest=i)
                # comm.bcast(f"sREQ {lamport_clock}", root=rank)
                current_state = "WAIT"

        if current_state == "WAIT":
            print(f"[SKRZAT:{rank}|{lamport_clock}] Jestem w stanie WAIT")
            
            while ack_counter < S - b:
                messages = get_messages(comm, rank, lamport_clock)

                for message in messages:
                    message_author = message[0]
                    message_type = message[1].split()[0]

                    if message_type == "gREQ":
                        continue

                    elif message_type == "sREQ":
                        message_clock = int(message[1].split()[1])
                        if lamport_clock <= message_clock:
                            print(f"[SKRZAT:{rank}|{lamport_clock}] Odsylam wiadomosc ACK do {message_author}")
                            lamport_clock = message_clock + 1
                            comm.send("ACK", dest=message_author)
                        else:
                            lamport_clock += 1
                            wait_queue.append(message_author)

                    elif message_type == "ACK":
                        ack_counter += 1

                    elif message_type == "sCHG":
                        b -= 1
                        print(f"[SKRZAT:{rank}|{lamport_clock}] Zmniejszam b, teraz jest {b}")

                    elif message_type == "gCHG":
                        b += 1
                        print(f"[SKRZAT:{rank}|{lamport_clock}] Zwiekszam b, teraz jest {b}")

                # Przejście do stanu INSECTION
                # if ack_counter >= S - b:
            current_state = "INSECTION"

        if current_state == "INSECTION":
            print(f"[SKRZAT:{rank}|{lamport_clock}] Jestem w stanie INSECTION")
            b -= 1
            print(f"[SKRZAT:{rank}|{lamport_clock}] Zmniejszam b, teraz jest {b} i wysylam wiadomosc sCHG do wszystkich procesow")
            for i in range(size):
                if i != rank:
                    comm.send(f"sCHG", dest=i)
            # comm.bcast("sCHG", root=rank)

            messages = get_messages(comm, rank, lamport_clock) 

            for message in messages:
                message_author = message[0]
                message_type = message[1].split()[0]

                if message_type == "gREQ":
                    continue

                elif message_type == "sREQ":
                    wait_queue.append(message_author)

                elif message_type == "ACK":
                    continue

                elif message_type == "sCHG":
                    b -= 1
                    print(f"[SKRZAT:{rank}|{lamport_clock}] Zmniejszam b, teraz jest {b}")

                elif message_type == "gCHG":
                    b += 1
                    print(f"[SKRZAT:{rank}|{lamport_clock}] Zwiekszam b, teraz jest {b}")

            # Przejście do stanu REST
            for target_rank in wait_queue:
                print(f"[SKRZAT:{rank}|{lamport_clock}] Wysylam wiadomosc ACK do {target_rank} znajdujacego sie w poczekalni")
                comm.send("ACK", dest=target_rank)
            wait_queue = []
            current_state = "REST"
            time.sleep(1)