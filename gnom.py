from mpi4py import MPI
import colorama
from colorama import Fore
import time

def get_messages(comm, rank, size):
    messages = []
    while True:
        status = MPI.Status()
        if comm.iprobe(source=MPI.ANY_SOURCE, status=status):
            message = comm.recv(source=status.Get_source())
            print(f"[GNOM:{rank}] Otrzymalem wiadomosc {message} od {status.Get_source()}")
            messages.append((status.Get_source(), message))
        else:
            break
    return messages

def gnome_code(comm, G, ac):
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
            print(f"[GNOM:{rank}|{lamport_clock}] Jestem w stanie REST")
            messages = get_messages(comm, rank, size) 
            
            for message in messages:
                message_author = message[0]
                message_type = message[1].split()[0]

                if message_type == "sREQ":
                    continue

                elif message_type == "gREQ":
                    print(f"[GNOM:{rank}|{lamport_clock}] Odsylam wiadomosc ACK do {message_author}")
                    comm.send("ACK", dest=message_author)

                elif message_type == "ACK":
                    continue

                elif message_type == "gCHG":
                    ac -= 1
                    print(f"[GNOM:{rank}|{lamport_clock}] Zmniejszam ac, teraz jest {ac}")

                elif message_type == "sCHG":
                    ac += 1
                    print(f"[GNOM:{rank}|{lamport_clock}] Zwiekszam ac, teraz jest {ac}")

            # Przejście do stanu INSECTION
            if ac >= G:
                current_state = "INSECTION"
            else:
                # Przejście do stanu WAIT
                ack_counter = 0
                lamport_clock += 1 
                print(f"[GNOM:{rank}|{lamport_clock}] Wysylam wiadomosc gREQ do wszystkich procesow")
                for i in range(size):
                    if i != rank:
                        comm.send(f"gREQ {lamport_clock}", dest=i)
                # comm.bcast(f"gREQ {lamport_clock}", root=rank)  # Wysylka do każdego procesu
                current_state = "WAIT"

        if current_state == "WAIT":
            print(f"[GNOM:{rank}|{lamport_clock}] Jestem w stanie WAIT")
            
            while ack_counter < G - ac:
                messages = get_messages(comm, rank, size)
                for message in messages:
                    message_author = message[0]
                    message_type = message[1].split()[0]

                    if message_type == "sREQ":
                        continue

                    elif message_type == "gREQ":
                        message_clock = int(message[1].split()[1])
                        if lamport_clock <= message_clock:
                            lamport_clock = message_clock + 1
                            print(f"[GNOM:{rank}|{lamport_clock}] Odsylam wiadomosc ACK do {message_author}")
                            comm.send("ACK", dest=message_author)
                        else:
                            lamport_clock += 1
                            wait_queue.append(message_author)

                    elif message_type == "ACK":
                        ack_counter += 1

                    elif message_type == "gCHG":
                        ac -= 1
                        print(f"[GNOM:{rank}|{lamport_clock}] Zmniejszam ac, teraz jest {ac}")

                    elif message_type == "sCHG":
                        ac += 1
                        print(f"[GNOM:{rank}|{lamport_clock}] Zwiekszam ac, teraz jest {ac}")

            # Przejście do stanu INSECTION
            current_state = "INSECTION"

        if current_state == "INSECTION":
            print(f"[GNOM:{rank}|{lamport_clock}] Jestem w stanie INSECTION")
            ac -= 1
            print(f"[GNOM:{rank}|{lamport_clock}] Zmniejszam ac, teraz jest {ac}. Wysylam wiadomosc gCHG do wszystkich procesow")
            # print(f"[GNOM:{rank}|{lamport_clock}] Wysylam wiadomosc gCHG do wszystkich procesow")
            for i in range(size):
                if i != rank:
                    comm.send(f"gCHG", dest=i)
            # comm.bcast("gCHG", root=rank)

            messages = get_messages(comm, rank, size)  

            for message in messages:
                message_author = message[0]
                message_type = message[1].split()[0]

                if message_type == "sREQ":
                    continue

                elif message_type == "gREQ":
                    wait_queue.append(message_author)

                elif message_type == "ACK":
                    continue

                elif message_type == "gCHG":
                    ac -= 1
                    print(f"[GNOM:{rank}|{lamport_clock}] Zmniejszam ac, teraz jest {ac}")

                elif message_type == "sCHG":
                    ac += 1
                    print(f"[GNOM:{rank}|{lamport_clock}] Zwiekszam ac, teraz jest {ac}")

            # Przejście do stanu REST
            for target_rank in wait_queue:
                print(f"[GNOM:{rank}|{lamport_clock}] Wysylam wiadomosc ACK do {target_rank} znajdujacego sie w poczekalni")
                comm.send("ACK", dest=target_rank)
            wait_queue = []
            current_state = "REST"
            time.sleep(1)